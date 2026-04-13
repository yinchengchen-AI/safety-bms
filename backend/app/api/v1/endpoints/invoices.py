from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceOut, InvoiceListOut
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
        query = query.join(Contract, Invoice.contract_id == Contract.id).filter(Contract.customer_id == customer_id)
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
        out.customer_name = item.contract.customer.name if item.contract and item.contract.customer else None
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
        query = query.join(Contract, Invoice.contract_id == Contract.id).filter(Contract.customer_id == customer_id)
    if status:
        query = query.filter(Invoice.status == status)
    query = apply_data_scope(query, Invoice, current_user)
    items = query.options(joinedload(Invoice.contract).joinedload(Contract.customer)).order_by(Invoice.created_at.desc()).all()
    headers = ["发票编号", "发票类型", "客户名称", "合同编号", "金额", "税率", "状态", "开票日期", "创建时间"]
    rows = []
    for item in items:
        rows.append([
            item.invoice_no, item.invoice_type.value if item.invoice_type else "",
            item.contract.customer.name if item.contract and item.contract.customer else "",
            item.contract.contract_no if item.contract else "", str(item.amount) if item.amount is not None else "",
            str(item.tax_rate) if item.tax_rate is not None else "", item.status.value if item.status else "",
            item.invoice_date.strftime("%Y-%m-%d") if item.invoice_date else "",
            item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
        ])
    from datetime import datetime
    return export_excel_response(f"invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows)


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
    return crud_invoice.update(db, db_obj=invoice, obj_in=body)


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
