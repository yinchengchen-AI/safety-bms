from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase[ModelType: Base, CreateSchemaType: BaseModel, UpdateSchemaType: BaseModel]:
    def __init__(self, model: type[ModelType]):
        self.model = model

    def _has_soft_delete(self) -> bool:
        return hasattr(self.model, "is_deleted")

    def get(self, db: Session, id: int, include_deleted: bool = False) -> ModelType | None:
        query = db.query(self.model).filter(self.model.id == id)
        if not include_deleted and self._has_soft_delete():
            query = query.filter(self.model.is_deleted == False)  # noqa: E712
        return query.first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 20, include_deleted: bool = False
    ) -> tuple[int, list[ModelType]]:
        query = db.query(self.model)
        if not include_deleted and self._has_soft_delete():
            query = query.filter(self.model.is_deleted == False)  # noqa: E712
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict
    ) -> ModelType:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType | None:
        obj = self.get(db, id, include_deleted=True)
        if not obj:
            return None
        if self._has_soft_delete():
            obj.is_deleted = True
            obj.deleted_at = datetime.now(UTC)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
        db.delete(obj)
        db.commit()
        return obj
