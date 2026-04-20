from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.constants import PermissionCode
from app.core.exceptions import BusinessError, DuplicateError, NotFoundError
from app.core.security import get_password_hash, verify_password
from app.crud.user import crud_user
from app.db.session import get_db
from app.dependencies import get_current_user, require_permissions
from app.models.user import User
from app.schemas.common import FileUploadResponse, PageResponse, ResponseMsg
from app.schemas.user import PasswordChange, RoleOut, UserCreate, UserOut, UserUpdate
from app.services.minio_service import minio_service
from app.utils.data_scope import check_data_scope
from app.utils.excel_export import export_excel_response
from app.utils.export_mappings import USER_ROLE_MAP, map_value
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=PageResponse[UserOut])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    is_active: bool | None = None,
    department_id: int | None = None,
    _: User = Depends(require_permissions(PermissionCode.USER_READ.value)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = crud_user.get_multi(
        db, skip=skip, limit=page_size, is_active=is_active, department_id=department_id
    )
    return make_page_response(total, items, page, page_size)


@router.get("/export")
def export_users(
    is_active: bool | None = None,
    department_id: int | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permissions(PermissionCode.USER_READ.value)),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if department_id is not None:
        query = query.filter(User.department_id == department_id)
    if keyword:
        query = query.filter(
            (User.username.ilike(f"%{keyword}%"))
            | (User.full_name.ilike(f"%{keyword}%"))
            | (User.email.ilike(f"%{keyword}%"))
        )
    items = query.order_by(User.created_at.desc()).all()
    headers = ["用户名", "姓名", "邮箱", "手机号", "部门", "状态", "角色", "创建时间"]
    rows = []
    for u in items:
        rows.append(
            [
                u.username,
                u.full_name or "",
                u.email or "",
                u.phone or "",
                u.department.name if u.department else "",
                "启用" if u.is_active else "禁用",
                ", ".join([map_value(r.name, USER_ROLE_MAP) for r in u.roles]) if u.roles else "",
                u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
            ]
        )
    from datetime import datetime

    return export_excel_response(
        f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows
    )


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    _: User = Depends(require_permissions(PermissionCode.USER_CREATE.value)),
    db: Session = Depends(get_db),
):
    if crud_user.get_by_username(db, username=body.username):
        raise DuplicateError("用户名")
    if crud_user.get_by_email(db, email=body.email):
        raise DuplicateError("邮箱")
    return crud_user.create(db, obj_in=body)


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    _: User = Depends(require_permissions(PermissionCode.ROLE_READ.value)),
    db: Session = Depends(get_db),
):
    return crud_user.get_all_roles(db)


@router.get("/me", response_model=UserOut)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_current_user_info(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = body.model_dump(exclude_unset=True)
    allowed_fields = {"full_name", "phone", "email", "avatar_url"}
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    return crud_user.update(db, db_obj=current_user, obj_in=filtered_data)


@router.post("/me/avatar", response_model=FileUploadResponse)
def upload_current_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = minio_service.upload_file(file, prefix=f"avatars/{current_user.id}")
    current_user.avatar_url = result["file_url"]
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return result


@router.post("/me/password", response_model=ResponseMsg)
def change_current_user_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password, current_user.hashed_password):
        raise BusinessError("旧密码错误", status_code=400)
    current_user.hashed_password = get_password_hash(body.new_password)
    db.add(current_user)
    db.commit()
    return {"message": "密码修改成功"}


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.USER_READ.value)),
    db: Session = Depends(get_db),
):
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError("用户")
    if not check_data_scope(user, current_user):
        raise BusinessError("无权查看该用户", status_code=403)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.USER_UPDATE.value)),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        if body.is_active is False:
            raise BusinessError("不能禁用自己的账号")
        if getattr(body, "is_superuser", None) is False:
            raise BusinessError("不能取消自己的超管权限")
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError("用户")
    if not check_data_scope(user, current_user):
        raise BusinessError("无权修改该用户", status_code=403)
    return crud_user.update(db, db_obj=user, obj_in=body)


@router.delete("/{user_id}", response_model=ResponseMsg)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.USER_DELETE.value)),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise BusinessError("不能删除自己的账号")
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError("用户")
    if not check_data_scope(user, current_user):
        raise BusinessError("无权删除该用户", status_code=403)
    crud_user.remove(db, id=user_id)
    return {"message": "删除成功"}
