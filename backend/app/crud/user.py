from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        role_ids = obj_in.role_ids
        data = obj_in.model_dump(exclude={"password", "role_ids"})
        db_obj = User(**data, hashed_password=get_password_hash(obj_in.password))
        if role_ids:
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            db_obj.roles = roles
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate | dict) -> User:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        role_ids = update_data.pop("role_ids", None)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        if role_ids is not None:
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            db_obj.roles = roles
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, username: str, password: str) -> User | None:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
        department_id: int | None = None,
    ) -> tuple[int, list[User]]:
        query = db.query(User)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if department_id is not None:
            query = query.filter(User.department_id == department_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items

    def get_all_roles(self, db: Session) -> list[Role]:
        return db.query(Role).all()


crud_user = CRUDUser(User)
