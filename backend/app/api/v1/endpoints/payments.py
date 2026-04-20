from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.core.constants import PermissionCode
from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.crud.payment import crud_payment
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.contract import Contract
from app.models.payment import Payment
from app.models.user import User
from app.schemas.common import FileUploadResponse, PageResponse
from app.schemas.payment import (
    ContractReceivable,
    PaymentCreate,
    PaymentListOut,
    PaymentOut,
    PaymentUpdate,
)
from app.services.minio_service import minio_service
from app.services.notification_service import notification_service
from app.services.payment_service import payment_service
from app.utils.data_scope import apply_data_scope, check_data_scope
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import PAYMENT_METHOD_MAP, map_value
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/payments", tags=["收款管理"])


@router.get("", response_model=PageResponse[PaymentListOut])
def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    contract_id: int | None = None,
    customer_id: int | None = None,
    invoice_id: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(Payment)
    if contract_id:
        query = query.filter(Payment.contract_id == contract_id)
    if customer_id:
        query = query.join(Contract, Payment.contract_id == Contract.id).filter(
            Contract.customer_id == customer_id
        )
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    query = apply_data_scope(query, Payment, current_user)
    total = query.count()
    items = (
        query.options(joinedload(Payment.contract).joinedload(Contract.customer))
        .order_by(Payment.payment_date.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        out = PaymentListOut.model_validate(item)
        out.contract_no = item.contract.contract_no if item.contract else None
        out.customer_name = (
            item.contract.customer.name if item.contract and item.contract.customer else None
        )
        result.append(out)
    return make_page_response(total, result, page, page_size)


@router.get("/export")
def export_payments(
    contract_id: int | None = None,
    customer_id: int | None = None,
    invoice_id: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_READ)),
    db: Session = Depends(get_db),
):
    query = db.query(Payment)
    if contract_id:
        query = query.filter(Payment.contract_id == contract_id)
    if customer_id:
        query = query.join(Contract, Payment.contract_id == Contract.id).filter(
            Contract.customer_id == customer_id
        )
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    query = apply_data_scope(query, Payment, current_user)
    items = (
        query.options(joinedload(Payment.contract).joinedload(Contract.customer))
        .order_by(Payment.payment_date.desc())
        .all()
    )
    headers = ["收款编号", "客户名称", "合同编号", "金额", "收款日期", "收款方式", "创建时间"]
    rows = []
    for item in items:
        rows.append(
            [
                item.payment_no,
                item.contract.customer.name if item.contract and item.contract.customer else "",
                item.contract.contract_no if item.contract else "",
                str(item.amount) if item.amount is not None else "",
                item.payment_date.strftime("%Y-%m-%d") if item.payment_date else "",
                map_value(
                    item.payment_method.value if item.payment_method else "", PAYMENT_METHOD_MAP
                ),
                item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
            ]
        )
    from datetime import datetime

    return export_excel_response(
        f"payments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows
    )


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(
    body: PaymentCreate,
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_CREATE)),
    db: Session = Depends(get_db),
):
    payment = payment_service.create_payment(db, obj_in=body, created_by=current_user.id)
    contract = (
        db.query(Contract)
        .filter(Contract.id == payment.contract_id, Contract.is_deleted == False)
        .first()
    )
    if contract is not None and contract.created_by is not None:
        payment_date = payment.payment_date.isoformat() if payment.payment_date else "未填写"
        method_map = {"bank_transfer": "银行转账", "cash": "现金", "check": "支票"}
        method_label = (
            method_map.get(payment.payment_method.value, payment.payment_method.value)
            if payment.payment_method
            else "未知方式"
        )
        customer_name = contract.customer.name if contract.customer else ""
        customer_line = f"客户：{customer_name}\n" if customer_name else ""
        notification_service.create(
            db,
            user_id=contract.created_by,
            title="新增收款记录",
            content=(
                f"合同 {contract.title}（{contract.contract_no}）新增一笔收款。\n"
                f"{customer_line}"
                f"收款编号：{payment.payment_no}，金额：{format(payment.amount, '.2f')} 元，"
                f"收款日期：{payment_date}，收款方式：{method_label}。"
            ),
        )
    return payment


@router.get("/overdue", response_model=list[ContractReceivable])
def list_overdue(
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_READ)),
    db: Session = Depends(get_db),
):
    return payment_service.get_overdue_contracts(db)


@router.get("/receivable/{contract_id}", response_model=ContractReceivable)
def get_receivable(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_READ)),
    db: Session = Depends(get_db),
):
    return payment_service.get_contract_receivable(db, contract_id=contract_id)


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(
    payment_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_READ)),
    db: Session = Depends(get_db),
):
    payment = crud_payment.get(db, id=payment_id)
    if not payment:
        raise NotFoundError("收款记录")
    if not check_data_scope(payment, current_user):
        raise BusinessError("无权查看该记录", status_code=403)
    return payment


@router.patch("/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: int,
    body: PaymentUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_UPDATE)),
    db: Session = Depends(get_db),
):
    payment = crud_payment.get(db, id=payment_id)
    if not payment:
        raise NotFoundError("收款记录")
    if not check_data_scope(payment, current_user):
        raise PermissionDeniedError()
    return crud_payment.update(db, db_obj=payment, obj_in=body)


@router.post("/{payment_id}/upload", response_model=FileUploadResponse)
def upload_voucher(
    payment_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permissions(PermissionCode.PAYMENT_UPDATE)),
    db: Session = Depends(get_db),
):
    payment = crud_payment.get(db, id=payment_id)
    if not payment:
        raise NotFoundError("收款记录")
    if not check_data_scope(payment, current_user):
        raise PermissionDeniedError()
    result = minio_service.upload_file(file, prefix=f"payments/{payment_id}")
    crud_payment.update(db, db_obj=payment, obj_in={"file_url": result["file_url"]})
    return result
