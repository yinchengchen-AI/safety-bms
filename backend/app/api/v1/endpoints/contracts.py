import contextlib
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import ContractStatus, PermissionCode
from app.core.exceptions import BusinessError, DuplicateError, NotFoundError, PermissionDeniedError
from app.crud.contract import crud_contract
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.contract import Contract, ContractChange, ContractSignature, ContractTemplate
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.service import ServiceOrder
from app.models.user import User
from app.schemas.common import PageResponse, ResponseMsg
from app.schemas.contract import (
    ContractCreate,
    ContractListOut,
    ContractOut,
    ContractSignRequest,
    ContractStatusUpdate,
    ContractUpdate,
    ContractUploadSignedRequest,
)
from app.services.contract_doc_service import (
    insert_signatures_and_to_pdf,
    render_contract_draft,
    render_standard_contract_draft,
    save_base64_signature_to_minio,
)
from app.services.minio_service import minio_service
from app.services.notification_service import notification_service
from app.utils.data_scope import apply_data_scope, check_data_scope
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import CONTRACT_STATUS_MAP, map_value
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/contracts", tags=["合同管理"])


def _enrich_contract_out(contract, out: ContractOut) -> ContractOut:
    out.customer_name = contract.customer.name if contract.customer else None
    if contract.service_type_obj:
        out.service_type_id = contract.service_type_obj.id
        out.service_type_name = contract.service_type_obj.name
        out.service_type_code = contract.service_type_obj.code
    if contract.standard_doc_url:
        try:
            out.standard_doc_url = minio_service.get_presigned_url(contract.standard_doc_url)
        except Exception:
            out.standard_doc_url = None
    return out


def _enrich_contract_list_out(contract, out: ContractListOut) -> ContractListOut:
    out.customer_name = contract.customer.name if contract.customer else None
    if contract.service_type_obj:
        out.service_type_id = contract.service_type_obj.id
        out.service_type_name = contract.service_type_obj.name
        out.service_type_code = contract.service_type_obj.code
    return out


@router.get("", response_model=PageResponse[ContractListOut])
def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    customer_id: int | None = None,
    status: ContractStatus | None = None,
    keyword: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(Contract).filter(Contract.is_deleted == False)
    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)
    if status:
        query = query.filter(Contract.status == status)
    if keyword:
        query = query.filter(
            (Contract.title.ilike(f"%{keyword}%")) | (Contract.contract_no.ilike(f"%{keyword}%"))
        )
    query = apply_data_scope(query, Contract, current_user)
    total = query.count()
    items = query.order_by(Contract.created_at.desc()).offset(skip).limit(page_size).all()
    # 附加 customer_name
    result = []
    for c in items:
        item = ContractListOut.model_validate(c)
        _enrich_contract_list_out(c, item)
        result.append(item)
    return make_page_response(total, result, page, page_size)


@router.get("/export")
def export_contracts(
    customer_id: int | None = None,
    status: ContractStatus | None = None,
    keyword: str | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    query = db.query(Contract).filter(Contract.is_deleted == False)
    if customer_id:
        query = query.filter(Contract.customer_id == customer_id)
    if status:
        query = query.filter(Contract.status == status)
    if keyword:
        query = query.filter(
            (Contract.title.ilike(f"%{keyword}%")) | (Contract.contract_no.ilike(f"%{keyword}%"))
        )
    query = apply_data_scope(query, Contract, current_user)
    items = query.order_by(Contract.created_at.desc()).all()
    headers = [
        "合同编号",
        "标题",
        "客户名称",
        "服务类型",
        "总金额",
        "签订日期",
        "开始日期",
        "结束日期",
        "状态",
    ]
    rows = []
    for c in items:
        rows.append(
            [
                c.contract_no,
                c.title,
                c.customer.name if c.customer else "",
                c.service_type_obj.name if c.service_type_obj else "",
                str(c.total_amount) if c.total_amount is not None else "",
                c.sign_date.strftime("%Y-%m-%d") if c.sign_date else "",
                c.start_date.strftime("%Y-%m-%d") if c.start_date else "",
                c.end_date.strftime("%Y-%m-%d") if c.end_date else "",
                map_value(c.status.value if c.status else "", CONTRACT_STATUS_MAP),
            ]
        )
    from datetime import datetime

    return export_excel_response(
        f"contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows
    )


@router.post("", response_model=ContractOut, status_code=201)
def create_contract(
    body: ContractCreate,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_CREATE)),
    db: Session = Depends(get_db),
):
    return crud_contract.create(db, obj_in=body, created_by=current_user.id)


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise BusinessError("无权查看该记录", status_code=403)
    result = ContractOut.model_validate(contract)
    _enrich_contract_out(contract, result)
    result.invoiced_amount = crud_contract.get_invoiced_amount(db, contract_id=contract_id)
    result.received_amount = crud_contract.get_received_amount(db, contract_id=contract_id)
    return result


@router.patch("/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: int,
    body: ContractUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if contract.status in (
        ContractStatus.REVIEW,
        ContractStatus.ACTIVE,
        ContractStatus.SIGNED,
        ContractStatus.COMPLETED,
        ContractStatus.TERMINATED,
    ):
        raise BusinessError(f"{contract.status.value} 状态合同不可修改")
    if body.contract_no:
        existing = (
            db.query(Contract)
            .filter(Contract.contract_no == body.contract_no, Contract.is_deleted == False)
            .first()
        )
        if existing and existing.id != contract_id:
            raise DuplicateError("合同编号")
    return crud_contract.update(db, db_obj=contract, obj_in=body)


@router.post("/{contract_id}/status", response_model=ContractOut)
def update_contract_status(
    contract_id: int,
    body: ContractStatusUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    old_status = contract.status
    # 提交审核时自动生草稿并校验模板
    if body.status == ContractStatus.REVIEW and old_status == ContractStatus.DRAFT:
        if contract.template_id:
            template = (
                db.query(ContractTemplate)
                .filter(ContractTemplate.id == contract.template_id)
                .first()
            )
            if not template or not template.file_url:
                raise BusinessError("模板文件不存在")
            draft_object_name = render_contract_draft(contract, template.file_url)
            contract.draft_doc_url = draft_object_name
        else:
            try:
                standard_object_name = render_standard_contract_draft(contract, db)
                if standard_object_name:
                    contract.standard_doc_url = standard_object_name
            except Exception:
                logging.getLogger(__name__).exception("标准合同草稿生成失败，不影响审核提交")
    updated = crud_contract.update_status(
        db,
        db_obj=contract,
        new_status=body.status,
        changed_by=current_user.id,
        remark=body.remark or "",
    )
    creator = db.query(User).filter(User.id == contract.created_by).first()
    customer_name = contract.customer.name if contract.customer else ""
    customer_line = f"客户：{customer_name}\n" if customer_name else ""
    if creator and creator.id != current_user.id:
        total_str = (
            format(contract.total_amount, ".2f") if contract.total_amount is not None else "0.00"
        )
        if body.status == ContractStatus.ACTIVE:
            notification_service.create(
                db,
                user_id=creator.id,
                title="合同审核通过",
                content=(
                    f"您的合同 {contract.title}（{contract.contract_no}）已通过审核。\n"
                    f"{customer_line}"
                    f"合同总金额：{total_str} 元。"
                ),
            )
        elif old_status == ContractStatus.REVIEW and body.status == ContractStatus.DRAFT:
            remark_text = f"备注：{body.remark}" if body.remark else ""
            notification_service.create(
                db,
                user_id=creator.id,
                title="合同审核被驳回",
                content=(
                    f"您的合同 {contract.title}（{contract.contract_no}）审核未通过，已退回草稿。\n"
                    f"{customer_line}"
                    f"合同总金额：{total_str} 元。{remark_text}"
                ).strip(),
            )
    if creator and body.status == ContractStatus.TERMINATED:
        total_str = (
            format(contract.total_amount, ".2f") if contract.total_amount is not None else "0.00"
        )
        notification_service.create(
            db,
            user_id=creator.id,
            title="合同已终止",
            content=(
                f"您的合同 {contract.title}（{contract.contract_no}）已终止。\n"
                f"{customer_line}"
                f"合同总金额：{total_str} 元。"
            ),
        )
    return updated


@router.get("/{contract_id}/draft-url")
def get_contract_draft_url(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if not contract.draft_doc_url:
        raise NotFoundError("合同草稿")
    url = minio_service.get_presigned_url(contract.draft_doc_url)
    return {"url": url}


@router.post("/{contract_id}/generate-draft", response_model=ContractOut)
def generate_contract_draft(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if contract.status in (
        ContractStatus.SIGNED,
        ContractStatus.COMPLETED,
        ContractStatus.TERMINATED,
    ):
        raise BusinessError("已签订/已完成/已终止的合同不可修改")
    if not contract.template_id:
        raise BusinessError("该合同未选择模板，无法生成草稿")

    template = (
        db.query(ContractTemplate).filter(ContractTemplate.id == contract.template_id).first()
    )
    if not template or not template.file_url:
        raise BusinessError("模板文件不存在")

    draft_object_name = render_contract_draft(contract, template.file_url)
    updated = crud_contract.update(db, db_obj=contract, obj_in={"draft_doc_url": draft_object_name})
    result = ContractOut.model_validate(updated)
    result.customer_name = updated.customer.name if updated.customer else None
    result.invoiced_amount = crud_contract.get_invoiced_amount(db, contract_id=contract_id)
    result.received_amount = crud_contract.get_received_amount(db, contract_id=contract_id)
    return result


@router.post("/{contract_id}/sign", response_model=ContractOut)
def sign_contract(
    contract_id: int,
    body: ContractSignRequest,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_SIGN)),
    db: Session = Depends(get_db),
):
    # 加行锁，防止并发重复签订
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.is_deleted == False)
        .with_for_update()
        .first()
    )
    if not contract:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if contract.status == ContractStatus.SIGNED:
        raise BusinessError("合同已签订")
    if contract.status != ContractStatus.ACTIVE:
        raise BusinessError("只有生效中的合同才能签订")
    if not contract.draft_doc_url:
        raise BusinessError("合同草稿不存在，请先生成草稿")

    party_a_object_name = None
    party_b_object_name = None
    try:
        party_a_object_name = save_base64_signature_to_minio(
            body.party_a_signature_base64, prefix=f"contracts/{contract.id}/signatures"
        )
        party_b_object_name = save_base64_signature_to_minio(
            body.party_b_signature_base64, prefix=f"contracts/{contract.id}/signatures"
        )

        final_pdf_object_name = insert_signatures_and_to_pdf(
            contract,
            party_a_name=body.party_a_name,
            party_a_signature_object_name=party_a_object_name,
            party_b_name=body.party_b_name,
            party_b_signature_object_name=party_b_object_name,
        )

        old_status = contract.status.value
        now = datetime.now(UTC)

        # 自动填充签订日期
        update_fields: dict = {
            "status": ContractStatus.SIGNED,
            "signed_at": now,
            "final_pdf_url": final_pdf_object_name,
        }
        if contract.sign_date is None:
            update_fields["sign_date"] = now.date()

        updated = crud_contract.update(db, db_obj=contract, obj_in=update_fields)

        sig_a = ContractSignature(
            contract_id=contract.id,
            party="party_a",
            signed_by=body.party_a_name,
            signature_url=party_a_object_name,
            signed_at=now,
        )
        sig_b = ContractSignature(
            contract_id=contract.id,
            party="party_b",
            signed_by=body.party_b_name,
            signature_url=party_b_object_name,
            signed_at=now,
        )
        db.add_all([sig_a, sig_b])

        change = ContractChange(
            contract_id=contract.id,
            changed_by=current_user.id,
            change_summary=f"状态变更: {old_status} → signed (合同签订)",
            before_status=old_status,
            after_status="signed",
            remark="",
        )
        db.add(change)
        db.commit()
        db.refresh(updated)

        creator = db.query(User).filter(User.id == contract.created_by).first()
        if creator and creator.id != current_user.id:
            notification_service.create(
                db,
                user_id=creator.id,
                title="合同签订完成",
                content=f"合同 {contract.title} 已完成签订。",
            )

        result = ContractOut.model_validate(updated)
        result.customer_name = updated.customer.name if updated.customer else None
        result.invoiced_amount = crud_contract.get_invoiced_amount(db, contract_id=contract_id)
        result.received_amount = crud_contract.get_received_amount(db, contract_id=contract_id)
        return result
    except Exception:
        # 清理已上传的临时签名图片
        if party_a_object_name:
            with contextlib.suppress(Exception):
                minio_service.delete_file(party_a_object_name)
        if party_b_object_name:
            with contextlib.suppress(Exception):
                minio_service.delete_file(party_b_object_name)
        raise


@router.get("/{contract_id}/download-pdf")
def download_contract_pdf(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if not contract.final_pdf_url:
        raise NotFoundError("合同PDF文件")
    url = minio_service.get_presigned_url(contract.final_pdf_url)
    return {"url": url}


@router.delete("/{contract_id}", response_model=ResponseMsg)
def delete_contract(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_DELETE)),
    db: Session = Depends(get_db),
):
    contract = crud_contract.get(db, id=contract_id)
    if not contract or contract.is_deleted:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if contract.status != ContractStatus.DRAFT:
        raise BusinessError("只有草稿状态的合同可以删除")
    has_orders = db.query(ServiceOrder).filter(ServiceOrder.contract_id == contract_id).first()
    has_invoices = db.query(Invoice).filter(Invoice.contract_id == contract_id).first()
    has_payments = db.query(Payment).filter(Payment.contract_id == contract_id).first()
    if has_orders or has_invoices or has_payments:
        raise BusinessError("该合同存在关联的工单、发票或收款记录，不可删除")
    crud_contract.soft_delete(db, contract_id=contract_id)
    return {"message": "删除成功"}


@router.post("/{contract_id}/upload-signed", response_model=ContractOut)
def upload_signed_contract(
    contract_id: int,
    body: ContractUploadSignedRequest,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_SIGN)),
    db: Session = Depends(get_db),
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.is_deleted == False)
        .with_for_update()
        .first()
    )
    if not contract:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if contract.status == ContractStatus.SIGNED:
        raise BusinessError("合同已签订")
    if contract.status != ContractStatus.ACTIVE:
        raise BusinessError("只有生效中的合同才能确认签订")
    if not contract.draft_doc_url:
        raise BusinessError("合同草稿不存在，无法确认签订")

    old_status = contract.status.value
    now = datetime.now(UTC)
    update_fields = {
        "status": ContractStatus.SIGNED,
        "signed_at": now,
        "final_pdf_url": body.file_url,
    }
    if contract.sign_date is None:
        update_fields["sign_date"] = now.date()

    updated = crud_contract.update(db, db_obj=contract, obj_in=update_fields)

    change = ContractChange(
        contract_id=contract.id,
        changed_by=current_user.id,
        change_summary=f"状态变更: {old_status} → signed (上传盖章版)",
        before_status=old_status,
        after_status="signed",
        remark="",
    )
    db.add(change)
    db.commit()
    db.refresh(updated)

    creator = db.query(User).filter(User.id == contract.created_by).first()
    if creator and creator.id != current_user.id:
        notification_service.create(
            db,
            user_id=creator.id,
            title="合同签订完成",
            content=f"合同 {contract.title} 已通过上传盖章版完成签订。",
        )

    result = ContractOut.model_validate(updated)
    result.customer_name = updated.customer.name if updated.customer else None
    result.invoiced_amount = crud_contract.get_invoiced_amount(db, contract_id=contract_id)
    result.received_amount = crud_contract.get_received_amount(db, contract_id=contract_id)
    return result
