from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import PermissionCode
from app.core.exceptions import BusinessError, DuplicateError, NotFoundError
from app.crud.role import crud_role
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.user import Role, User
from app.schemas.common import PageResponse, ResponseMsg
from app.schemas.role import RoleCreate, RoleOut, RoleUpdate
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.get("", response_model=PageResponse[RoleOut])
def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: str | None = None,
    _: User = Depends(require_permissions(PermissionCode.ROLE_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = crud_role.get_multi(db, skip=skip, limit=page_size, keyword=keyword)
    return make_page_response(total, items, page, page_size)


@router.get("/permissions", response_model=list[RoleOut])
def list_roles_with_permissions(
    _: User = Depends(require_permissions(PermissionCode.ROLE_READ)),
    db: Session = Depends(get_db),
):
    items = db.query(Role).all()
    return items


@router.post("", response_model=RoleOut, status_code=201)
def create_role(
    body: RoleCreate,
    _: User = Depends(require_permissions(PermissionCode.ROLE_CREATE)),
    db: Session = Depends(get_db),
):
    if crud_role.get_by_name(db, name=body.name):
        raise DuplicateError("角色名")
    return crud_role.create(db, obj_in=body)


@router.get("/{role_id}", response_model=RoleOut)
def get_role(
    role_id: int,
    _: User = Depends(require_permissions(PermissionCode.ROLE_READ)),
    db: Session = Depends(get_db),
):
    role = crud_role.get(db, id=role_id)
    if not role:
        raise NotFoundError("角色")
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int,
    body: RoleUpdate,
    _: User = Depends(require_permissions(PermissionCode.ROLE_UPDATE)),
    db: Session = Depends(get_db),
):
    role = crud_role.get(db, id=role_id)
    if not role:
        raise NotFoundError("角色")
    if (
        body.name is not None
        and body.name != role.name
        and crud_role.get_by_name(db, name=body.name)
    ):
        raise DuplicateError("角色名")
    return crud_role.update(db, db_obj=role, obj_in=body)


@router.delete("/{role_id}", response_model=ResponseMsg)
def delete_role(
    role_id: int,
    _: User = Depends(require_permissions(PermissionCode.ROLE_DELETE)),
    db: Session = Depends(get_db),
):
    role = crud_role.get(db, id=role_id)
    if not role:
        raise NotFoundError("角色")
    if crud_role.is_predefined(role):
        raise BusinessError("预定义角色不能删除", status_code=403)
    if crud_role.has_users(db, role_id=role_id):
        raise BusinessError("该角色下存在关联用户，不可删除", status_code=403)
    crud_role.remove(db, id=role_id)
    return {"message": "删除成功"}
