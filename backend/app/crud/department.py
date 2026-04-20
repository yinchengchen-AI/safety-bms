from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        keyword: str | None = None,
    ) -> tuple[int, list[Department]]:
        query = db.query(Department)
        if keyword:
            query = query.filter(Department.name.ilike(f"%{keyword}%"))
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items

    def get_tree(self, db: Session) -> list[Department]:
        """获取所有部门（前端自行组装树或后端递归）"""
        return db.query(Department).all()


crud_department = CRUDDepartment(Department)
