from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import PermissionCode
from app.core.exceptions import BusinessError, NotFoundError
from app.crud.department import crud_department
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.department import Department
from app.models.user import User
from app.schemas.common import PageResponse, ResponseMsg
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.utils.excel_export import export_excel_response
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/departments", tags=["部门管理"])


@router.get("", response_model=PageResponse[DepartmentOut])
def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: str | None = None,
    _: User = Depends(require_permissions(PermissionCode.DEPARTMENT_READ.value)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = crud_department.get_multi(db, skip=skip, limit=page_size, keyword=keyword)
    return make_page_response(total, items, page, page_size)


@router.get("/export")
def export_departments(
    keyword: str | None = None,
    _: User = Depends(require_permissions(PermissionCode.DEPARTMENT_READ.value)),
    db: Session = Depends(get_db),
):
    query = db.query(Department)
    if keyword:
        query = query.filter(Department.name.ilike(f"%{keyword}%"))
    items = query.order_by(Department.created_at.desc()).all()
    headers = ["部门名称", "描述", "上级部门", "创建时间"]
    rows = []
    for d in items:
        rows.append(
            [
                d.name,
                d.description or "",
                d.parent.name if d.parent else "",
                d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else "",
            ]
        )
    from datetime import UTC, datetime

    return export_excel_response(
        f"departments_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows
    )


@router.post("", response_model=DepartmentOut, status_code=201)
def create_department(
    body: DepartmentCreate,
    _: User = Depends(require_permissions(PermissionCode.DEPARTMENT_CREATE.value)),
    db: Session = Depends(get_db),
):
    return crud_department.create(db, obj_in=body)


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(
    department_id: int,
    _: User = Depends(require_permissions(PermissionCode.DEPARTMENT_READ.value)),
    db: Session = Depends(get_db),
):
    dept = crud_department.get(db, id=department_id)
    if not dept:
        raise NotFoundError("部门")
    return dept


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: int,
    body: DepartmentUpdate,
    _: User = Depends(require_permissions(PermissionCode.DEPARTMENT_UPDATE.value)),
    db: Session = Depends(get_db),
):
    dept = crud_department.get(db, id=department_id)
    if not dept:
        raise NotFoundError("部门")
    return crud_department.update(db, db_obj=dept, obj_in=body)


@router.delete("/{department_id}", response_model=ResponseMsg)
def delete_department(
    department_id: int,
    _: User = Depends(require_permissions(PermissionCode.DEPARTMENT_DELETE.value)),
    db: Session = Depends(get_db),
):
    dept = crud_department.get(db, id=department_id)
    if not dept:
        raise NotFoundError("部门")
    if crud_department.has_users(db, department_id=department_id):
        raise BusinessError("该部门下存在关联用户，不可删除", status_code=403)
    crud_department.remove(db, id=department_id)
    return {"message": "删除成功"}
