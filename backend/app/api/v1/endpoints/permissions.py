from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.role import PermissionCreate, PermissionUpdate, PermissionOut
from app.schemas.common import PageResponse, ResponseMsg
from app.crud.permission import crud_permission
from app.dependencies import require_permissions
from app.core.exceptions import NotFoundError, DuplicateError
from app.models.user import User
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/permissions", tags=["权限管理"])


@router.get("", response_model=PageResponse[PermissionOut])
def list_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = None,
    _: User = Depends(require_permissions()),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(crud_permission.model)
    if keyword:
        query = query.filter(
            crud_permission.model.name.ilike(f"%{keyword}%")
            | crud_permission.model.code.ilike(f"%{keyword}%")
        )
    total = query.count()
    items = query.offset(skip).limit(page_size).all()
    return make_page_response(total, items, page, page_size)


@router.post("", response_model=PermissionOut, status_code=201)
def create_permission(
    body: PermissionCreate,
    _: User = Depends(require_permissions()),
    db: Session = Depends(get_db),
):
    if crud_permission.get_by_code(db, code=body.code):
        raise DuplicateError("权限码")
    return crud_permission.create(db, obj_in=body)


@router.get("/{permission_id}", response_model=PermissionOut)
def get_permission(
    permission_id: int,
    _: User = Depends(require_permissions()),
    db: Session = Depends(get_db),
):
    perm = crud_permission.get(db, id=permission_id)
    if not perm:
        raise NotFoundError("权限")
    return perm


@router.put("/{permission_id}", response_model=PermissionOut)
def update_permission(
    permission_id: int,
    body: PermissionUpdate,
    _: User = Depends(require_permissions()),
    db: Session = Depends(get_db),
):
    perm = crud_permission.get(db, id=permission_id)
    if not perm:
        raise NotFoundError("权限")
    return crud_permission.update(db, db_obj=perm, obj_in=body)


@router.delete("/{permission_id}", response_model=ResponseMsg)
def delete_permission(
    permission_id: int,
    _: User = Depends(require_permissions()),
    db: Session = Depends(get_db),
):
    perm = crud_permission.get(db, id=permission_id)
    if not perm:
        raise NotFoundError("权限")
    crud_permission.remove(db, id=permission_id)
    return {"message": "删除成功"}
