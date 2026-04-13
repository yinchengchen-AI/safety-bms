from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate


PREDEFINED_ROLES = {"admin", "manager", "sales", "finance", "viewer"}


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
    ) -> Tuple[int, List[Role]]:
        query = db.query(Role)
        if keyword:
            query = query.filter(Role.name.ilike(f"%{keyword}%"))
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items

    def create(self, db: Session, *, obj_in: RoleCreate) -> Role:
        permission_ids = obj_in.permission_ids or []
        role_data = obj_in.model_dump(exclude={"permission_ids"})
        db_obj = Role(**role_data)
        if permission_ids:
            perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            db_obj.permissions.extend(perms)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Role, obj_in: RoleUpdate | dict) -> Role:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        permission_ids = update_data.pop("permission_ids", None)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        if permission_ids is not None:
            db_obj.permissions = []
            perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            db_obj.permissions.extend(perms)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def is_predefined(self, role: Role) -> bool:
        return role.name.lower() in PREDEFINED_ROLES


crud_role = CRUDRole(Role)
