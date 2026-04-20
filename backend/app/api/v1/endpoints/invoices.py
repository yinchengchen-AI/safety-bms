from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.core.constants import InvoiceStatus, PermissionCode
from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.crud.invoice import crud_invoice
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.common import FileUploadResponse, PageResponse
from app.schemas.invoice import (
    InvoiceAuditRequest,
    InvoiceCreate,
    InvoiceListOut,
    InvoiceOut,
    InvoiceUpdate,
)
from app.services.invoice_service import invoice_service
from app.services.minio_service import minio_service
from app.services.notification_service import notification_service
from app.utils.data_scope import apply_data_scope, check_data_scope
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import INVOICE_STATUS_MAP, INVOICE_TYPE_MAP, map_value
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/invoices", tags=["开票管理"])


@router.get("", response_model=PageResponse[InvoiceListOut])
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    contract_id: int | None = None,
    customer_id: int | None = None,
    status: InvoiceStatus | None = None,
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
            item.contract.customer.name if item.contract and item.contract.customer else None
        )
        result.append(out)
    return make_page_response(total, result, page, page_size)


@router.get("/export")
def export_invoices(
    contract_id: int | None = None,
    customer_id: int | None = None,
    status: InvoiceStatus | None = None,
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
                map_value(item.invoice_type.value if item.invoice_type else "", INVOICE_TYPE_MAP),
                item.contract.customer.name if item.contract and item.contract.customer else "",
                item.contract.contract_no if item.contract else "",
                str(item.amount) if item.amount is not None else "",
                str(item.tax_rate) if item.tax_rate is not None else "",
                map_value(item.status.value if item.status else "", INVOICE_STATUS_MAP),
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
    return invoice_service.create_invoice(db, obj_in=body, applied_by=int(current_user.id))


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
        and getattr(updated, "applied_by", None) is not None
    ):
        applied_by = int(updated.applied_by)
        contract_title = updated.contract.title if updated.contract else ""
        contract_no = updated.contract.contract_no if updated.contract else ""
        customer_name = (
            updated.contract.customer.name if updated.contract and updated.contract.customer else ""
        )
        amount_str = format(updated.amount, ".2f") if updated.amount is not None else "0.00"
        tax_str = format(updated.tax_amount, ".2f") if updated.tax_amount is not None else "0.00"
        invoice_date_value = getattr(updated, "invoice_date", None)
        invoice_date = invoice_date_value.isoformat() if invoice_date_value else "未填写"
        customer_line = f"客户：{customer_name}\n" if customer_name else ""
        if body.status == InvoiceStatus.ISSUED:
            notification_service.create(
                db,
                user_id=applied_by,
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
                user_id=applied_by,
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
    updated = invoice_service.audit_invoice(db, invoice_id=invoice_id, body=body)

    applied_by = getattr(updated, "applied_by", None)
    current_user_id = int(current_user.id)
    if applied_by is not None and int(applied_by) != current_user_id:
        contract_title = updated.contract.title if updated.contract else ""
        contract_no = updated.contract.contract_no if updated.contract else ""
        customer_name = (
            updated.contract.customer.name if updated.contract and updated.contract.customer else ""
        )
        amount_str = format(updated.amount, ".2f") if updated.amount is not None else "0.00"
        customer_line = f"客户：{customer_name}\n" if customer_name else ""

        if body.action == "approve":
            notification_service.create(
                db,
                user_id=int(applied_by),
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
                user_id=int(applied_by),
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
    file_url = getattr(invoice, "file_url", None) if invoice else None
    if not invoice or not file_url:
        raise NotFoundError("发票附件")
    if not check_data_scope(invoice, current_user):
        raise PermissionDeniedError()
    url = minio_service.get_presigned_url(str(file_url))
    return {"url": url}
