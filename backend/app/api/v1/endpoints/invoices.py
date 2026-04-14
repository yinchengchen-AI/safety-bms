from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceOut,
    InvoiceListOut,
    InvoiceAuditRequest,
)
from app.schemas.common import PageResponse, ResponseMsg, FileUploadResponse
from app.crud.invoice import crud_invoice
from app.dependencies import require_permissions
from app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessError
from app.core.constants import InvoiceStatus, PermissionCode
from app.models.invoice import Invoice
from app.models.contract import Contract
from app.models.user import User
from app.services.invoice_service import invoice_service
from app.services.minio_service import minio_service
from app.services.notification_service import notification_service
from app.utils.data_scope import apply_data_scope, check_data_scope
from app.utils.pagination import make_page_response
from app.utils.excel_export import export_excel_response

router = APIRouter(prefix="/invoices", tags=["开票管理"])


@router.get("", response_model=PageResponse[InvoiceListOut])
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    contract_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(Invoice)
    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)
    if customer_id:
        query = query.join(Contract, Invoice.contract_id == Contract.id).filter(
            Contract.customer_id == customer_id
        )
    if status:
        query = query.filter(Invoice.status == status)
    query = apply_data_scope(query, Invoice, current_user)
    total = query.count()
    items = (
        query.options(joinedload(Invoice.contract).joinedload(Contract.customer))
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        out = InvoiceListOut.model_validate(item)
        out.customer_name = (
            item.contract.customer.name
            if item.contract and item.contract.customer
            else None
        )
        result.append(out)
    return make_page_response(total, result, page, page_size)


@router.get("/export")
def export_invoices(
    contract_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    status: Optional[InvoiceStatus] = None,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_READ)),
    db: Session = Depends(get_db),
):
    query = db.query(Invoice)
    if contract_id:
        query = query.filter(Invoice.contract_id == contract_id)
    if customer_id:
        query = query.join(Contract, Invoice.contract_id == Contract.id).filter(
            Contract.customer_id == customer_id
        )
    if status:
        query = query.filter(Invoice.status == status)
    query = apply_data_scope(query, Invoice, current_user)
    items = (
        query.options(joinedload(Invoice.contract).joinedload(Contract.customer))
        .order_by(Invoice.created_at.desc())
        .all()
    )
    headers = [
        "发票编号",
        "发票类型",
        "客户名称",
        "合同编号",
        "金额",
        "税率",
        "状态",
        "开票日期",
        "创建时间",
    ]
    rows = []
    for item in items:
        rows.append(
            [
                item.invoice_no,
                item.invoice_type.value if item.invoice_type else "",
                item.contract.customer.name
                if item.contract and item.contract.customer
                else "",
                item.contract.contract_no if item.contract else "",
                str(item.amount) if item.amount is not None else "",
                str(item.tax_rate) if item.tax_rate is not None else "",
                item.status.value if item.status else "",
                item.invoice_date.strftime("%Y-%m-%d") if item.invoice_date else "",
                item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
            ]
        )
    from datetime import datetime

    return export_excel_response(
        f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows
    )


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(
    body: InvoiceCreate,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_CREATE)),
    db: Session = Depends(get_db),
):
    return invoice_service.create_invoice(db, obj_in=body, applied_by=current_user.id)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_READ)),
    db: Session = Depends(get_db),
):
    invoice = crud_invoice.get(db, id=invoice_id)
    if not invoice:
        raise NotFoundError("发票")
    if not check_data_scope(invoice, current_user):
        raise BusinessError("无权查看该记录", status_code=403)
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: int,
    body: InvoiceUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_UPDATE)),
    db: Session = Depends(get_db),
):
    invoice = crud_invoice.get(db, id=invoice_id)
    if not invoice:
        raise NotFoundError("发票")
    if not check_data_scope(invoice, current_user):
        raise PermissionDeniedError()
    old_status = invoice.status
    updated = crud_invoice.update(db, db_obj=invoice, obj_in=body)
    if (
        body.status is not None
        and body.status != old_status
        and updated.applied_by is not None
    ):
        contract_title = updated.contract.title if updated.contract else ""
        contract_no = updated.contract.contract_no if updated.contract else ""
        customer_name = (
            updated.contract.customer.name
            if updated.contract and updated.contract.customer
            else ""
        )
        amount_str = (
            format(updated.amount, ".2f") if updated.amount is not None else "0.00"
        )
        tax_str = (
            format(updated.tax_amount, ".2f")
            if updated.tax_amount is not None
            else "0.00"
        )
        invoice_date = (
            updated.invoice_date.isoformat() if updated.invoice_date else "未填写"
        )
        customer_line = f"客户：{customer_name}\n" if customer_name else ""
        if body.status == InvoiceStatus.ISSUED:
            notification_service.create(
                db,
                user_id=updated.applied_by,
                title="发票已开具",
                content=(
                    f"发票 {updated.invoice_no} 已开具。\n"
                    f"合同：{contract_title}（{contract_no}）\n"
                    f"{customer_line}"
                    f"开票日期：{invoice_date}，金额：{amount_str} 元，税额：{tax_str} 元。"
                ),
            )
        elif body.status == InvoiceStatus.SENT:
            notification_service.create(
                db,
                user_id=updated.applied_by,
                title="发票已寄出",
                content=(
                    f"发票 {updated.invoice_no} 已寄出。\n"
                    f"合同：{contract_title}（{contract_no}）\n"
                    f"{customer_line}"
                    f"开票日期：{invoice_date}，金额：{amount_str} 元，税额：{tax_str} 元。"
                ),
            )
    return updated


@router.post("/{invoice_id}/audit", response_model=InvoiceOut)
def audit_invoice(
    invoice_id: int,
    body: InvoiceAuditRequest,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_UPDATE)),
    db: Session = Depends(get_db),
):
    invoice = crud_invoice.get(db, id=invoice_id)
    if not invoice:
        raise NotFoundError("发票")
    if not check_data_scope(invoice, current_user):
        raise PermissionDeniedError()
    if invoice.status != InvoiceStatus.APPLYING:
        raise BusinessError("只有申请中的发票才能审核")

    update_data: dict = {}

    if body.action == "approve":
        if not body.invoice_date:
            raise BusinessError("审核通过时必须填写开票日期")
        if not body.actual_invoice_no:
            raise BusinessError("审核通过时必须填写发票号")
        update_data = {
            "status": InvoiceStatus.ISSUED,
            "invoice_date": body.invoice_date,
            "actual_invoice_no": body.actual_invoice_no,
            "remark": body.remark,
        }
    elif body.action == "reject":
        if not body.remark:
            raise BusinessError("驳回时必须填写驳回原因")
        update_data = {
            "status": InvoiceStatus.REJECTED,
            "remark": body.remark,
        }
    else:
        raise BusinessError("无效的审核动作，仅支持 approve 或 reject")

    updated = crud_invoice.update(db, db_obj=invoice, obj_in=update_data)

    if updated.applied_by and updated.applied_by != current_user.id:
        contract_title = updated.contract.title if updated.contract else ""
        contract_no = updated.contract.contract_no if updated.contract else ""
        customer_name = (
            updated.contract.customer.name
            if updated.contract and updated.contract.customer
            else ""
        )
        amount_str = (
            format(updated.amount, ".2f") if updated.amount is not None else "0.00"
        )
        customer_line = f"客户：{customer_name}\n" if customer_name else ""

        if body.action == "approve":
            notification_service.create(
                db,
                user_id=updated.applied_by,
                title="发票已开具",
                content=(
                    f"您的开票申请 {updated.invoice_no} 已通过审核，发票已开具。\n"
                    f"合同：{contract_title}（{contract_no}）\n"
                    f"{customer_line}"
                    f"发票号：{body.actual_invoice_no}\n"
                    f"开票日期：{body.invoice_date}\n"
                    f"金额：{amount_str} 元。"
                ),
            )
        else:
            notification_service.create(
                db,
                user_id=updated.applied_by,
                title="开票申请被驳回",
                content=(
                    f"您的开票申请 {updated.invoice_no} 未通过审核。\n"
                    f"合同：{contract_title}（{contract_no}）\n"
                    f"{customer_line}"
                    f"申请金额：{amount_str} 元。\n"
                    f"驳回原因：{body.remark}"
                ),
            )

    return updated


@router.post("/{invoice_id}/upload", response_model=FileUploadResponse)
def upload_invoice_file(
    invoice_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_UPDATE)),
    db: Session = Depends(get_db),
):
    invoice = crud_invoice.get(db, id=invoice_id)
    if not invoice:
        raise NotFoundError("发票")
    if not check_data_scope(invoice, current_user):
        raise PermissionDeniedError()
    result = minio_service.upload_file(file, prefix=f"invoices/{invoice_id}")
    crud_invoice.update(db, db_obj=invoice, obj_in={"file_url": result["file_url"]})
    return result


@router.get("/{invoice_id}/download-url")
def get_download_url(
    invoice_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.INVOICE_READ)),
    db: Session = Depends(get_db),
):
    invoice = crud_invoice.get(db, id=invoice_id)
    if not invoice or not invoice.file_url:
        raise NotFoundError("发票附件")
    if not check_data_scope(invoice, current_user):
        raise PermissionDeniedError()
    url = minio_service.get_presigned_url(invoice.file_url)
    return {"url": url}
