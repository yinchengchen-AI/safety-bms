from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import Permission
from app.schemas.role import PermissionCreate, PermissionUpdate


class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Permission | None:
        return db.query(Permission).filter(Permission.code == code).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> tuple[int, list[Permission]]:
        query = db.query(Permission)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items


crud_permission = CRUDPermission(Permission)
