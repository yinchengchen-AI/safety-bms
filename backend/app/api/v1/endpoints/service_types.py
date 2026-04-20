from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import PermissionCode
from app.core.exceptions import BusinessError, NotFoundError
from app.crud.service_type import crud_service_type
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.user import User
from app.schemas.common import PageResponse, ResponseMsg
from app.schemas.service_type import ServiceTypeCreate, ServiceTypeOut, ServiceTypeUpdate
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/service-types", tags=["服务类型管理"])


@router.get("", response_model=PageResponse[ServiceTypeOut])
def list_service_types(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    is_active: bool | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = crud_service_type.get_multi(db, skip=skip, limit=page_size, is_active=is_active)
    return make_page_response(total, items, page, page_size)


@router.get("/{service_type_id}", response_model=ServiceTypeOut)
def get_service_type(
    service_type_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    return obj


@router.post("", response_model=ServiceTypeOut, status_code=201)
def create_service_type(
    body: ServiceTypeCreate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_CREATE)),
    db: Session = Depends(get_db),
):
    existing = crud_service_type.get_by_code(db, code=body.code)
    if existing:
        raise BusinessError(f"服务类型 code '{body.code}' 已存在")
    return crud_service_type.create(db, obj_in=body)


@router.put("/{service_type_id}", response_model=ServiceTypeOut)
def update_service_type(
    service_type_id: int,
    body: ServiceTypeUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    if body.code:
        existing = crud_service_type.get_by_code(db, code=body.code)
        if existing and existing.id != service_type_id:
            raise BusinessError(f"服务类型 code '{body.code}' 已存在")
    return crud_service_type.update(db, db_obj=obj, obj_in=body)


@router.delete("/{service_type_id}", response_model=ResponseMsg)
def delete_service_type(
    service_type_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_DELETE)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    usage = crud_service_type.get_usage_counts(db, service_type_id=service_type_id)
    total = usage["contract_count"] + usage["order_count"] + usage["template_count"]
    if total > 0:
        raise BusinessError(
            f"该服务类型正在被引用（合同 {usage['contract_count']} 个，工单 {usage['order_count']} 个，模板 {usage['template_count']} 个），无法删除"
        )
    crud_service_type.remove(db, id=service_type_id)
    return {"message": "删除成功"}


@router.get("/{service_type_id}/usage")
def get_service_type_usage(
    service_type_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    return crud_service_type.get_usage_counts(db, service_type_id=service_type_id)
