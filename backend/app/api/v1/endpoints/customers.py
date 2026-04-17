from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerOut, CustomerListOut,
    CustomerContactCreate, CustomerContactOut, CustomerFollowUpCreate, CustomerFollowUpOut,
)
from app.schemas.common import PageResponse, ResponseMsg
from app.crud.customer import crud_customer
from app.dependencies import require_permissions
from app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessError
from app.core.constants import CustomerStatus, PermissionCode
from app.utils.data_scope import apply_data_scope, check_data_scope
from app.models.customer import Customer
from app.models.user import User
from app.services.minio_service import minio_service
from app.utils.pagination import make_page_response
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import CUSTOMER_STATUS_MAP, map_value

router = APIRouter(prefix="/customers", tags=["客户管理"])


@router.get("", response_model=PageResponse[CustomerListOut])
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[CustomerStatus] = None,
    keyword: Optional[str] = None,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(Customer).filter(Customer.is_deleted == False)
    if status:
        query = query.filter(Customer.status == status)
    if keyword:
        query = query.filter(Customer.name.ilike(f"%{keyword}%"))
    query = apply_data_scope(query, Customer, current_user)
    total = query.count()
    items = query.order_by(Customer.created_at.desc()).offset(skip).limit(page_size).all()
    return make_page_response(total, items, page, page_size)


@router.get("/export")
def export_customers(
    status: Optional[CustomerStatus] = None,
    keyword: Optional[str] = None,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_READ)),
    db: Session = Depends(get_db),
):
    query = db.query(Customer).filter(Customer.is_deleted == False)
    if status:
        query = query.filter(Customer.status == status)
    if keyword:
        query = query.filter(Customer.name.ilike(f"%{keyword}%"))
    query = apply_data_scope(query, Customer, current_user)
    items = query.order_by(Customer.created_at.desc()).all()
    headers = ["客户名称", "统一信用代码", "行业", "规模", "地址", "联系人", "联系电话", "状态", "创建时间"]
    rows = []
    for c in items:
        rows.append([
            c.name, c.credit_code or "", c.industry or "", c.scale or "", c.address or "",
            c.contact_name or "", c.contact_phone or "", map_value(c.status.value if c.status else "", CUSTOMER_STATUS_MAP),
            c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
        ])
    from datetime import datetime
    return export_excel_response(f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows)


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    body: CustomerCreate,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_CREATE)),
    db: Session = Depends(get_db),
):
    return crud_customer.create(db, obj_in=body, created_by=current_user.id)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_READ)),
    db: Session = Depends(get_db),
):
    customer = crud_customer.get(db, id=customer_id)
    if not customer or customer.is_deleted:
        raise NotFoundError("客户")
    if not check_data_scope(customer, current_user):
        raise BusinessError("无权查看该记录", status_code=403)
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_UPDATE)),
    db: Session = Depends(get_db),
):
    customer = crud_customer.get(db, id=customer_id)
    if not customer or customer.is_deleted:
        raise NotFoundError("客户")
    if not check_data_scope(customer, current_user):
        raise PermissionDeniedError()
    return crud_customer.update(db, db_obj=customer, obj_in=body)


@router.delete("/{customer_id}", response_model=ResponseMsg)
def delete_customer(
    customer_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_DELETE)),
    db: Session = Depends(get_db),
):
    customer = crud_customer.get(db, id=customer_id)
    if not customer or customer.is_deleted:
        raise NotFoundError("客户")
    if not check_data_scope(customer, current_user):
        raise PermissionDeniedError()
    crud_customer.soft_delete(db, customer_id=customer_id)
    return {"message": "删除成功"}


@router.post("/{customer_id}/contacts", response_model=CustomerContactOut, status_code=201)
def add_contact(
    customer_id: int,
    body: CustomerContactCreate,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_UPDATE)),
    db: Session = Depends(get_db),
):
    customer = crud_customer.get(db, id=customer_id)
    if not customer or customer.is_deleted:
        raise NotFoundError("客户")
    if not check_data_scope(customer, current_user):
        raise PermissionDeniedError()
    return crud_customer.add_contact(db, customer_id=customer_id, obj_in=body)


@router.post("/{customer_id}/follow-ups", response_model=CustomerFollowUpOut, status_code=201)
def add_follow_up(
    customer_id: int,
    body: CustomerFollowUpCreate,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_UPDATE)),
    db: Session = Depends(get_db),
):
    customer = crud_customer.get(db, id=customer_id)
    if not customer or customer.is_deleted:
        raise NotFoundError("客户")
    if not check_data_scope(customer, current_user):
        raise PermissionDeniedError()
    return crud_customer.add_follow_up(db, customer_id=customer_id, creator_id=current_user.id, obj_in=body)


@router.get("/{customer_id}/follow-ups", response_model=list[CustomerFollowUpOut])
def list_follow_ups(
    customer_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CUSTOMER_READ)),
    db: Session = Depends(get_db),
):
    customer = crud_customer.get(db, id=customer_id)
    if not customer or customer.is_deleted:
        raise NotFoundError("客户")
    if not check_data_scope(customer, current_user):
        raise PermissionDeniedError()
    return crud_customer.get_follow_ups(db, customer_id=customer_id)
