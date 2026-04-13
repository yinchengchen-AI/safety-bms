from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.customer import Customer, CustomerContact, CustomerFollowUp
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerContactCreate, CustomerFollowUpCreate
from app.core.constants import CustomerStatus


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def create(self, db: Session, *, obj_in: CustomerCreate, created_by: int | None = None) -> Customer:
        contacts = obj_in.contacts
        data = obj_in.model_dump(exclude={"contacts"})
        db_obj = Customer(**data, created_by=created_by)
        db.add(db_obj)
        db.flush()  # 获取 id，未提交
        for c in contacts:
            contact = CustomerContact(**c.model_dump(), customer_id=db_obj.id)
            db.add(contact)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        status: Optional[CustomerStatus] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[int, List[Customer]]:
        query = db.query(Customer).filter(Customer.is_deleted == False)
        if status:
            query = query.filter(Customer.status == status)
        if keyword:
            query = query.filter(Customer.name.ilike(f"%{keyword}%"))
        total = query.count()
        items = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
        return total, items

    def add_contact(self, db: Session, *, customer_id: int, obj_in: CustomerContactCreate) -> CustomerContact:
        contact = CustomerContact(**obj_in.model_dump(), customer_id=customer_id)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    def add_follow_up(
        self, db: Session, *, customer_id: int, creator_id: int, obj_in: CustomerFollowUpCreate
    ) -> CustomerFollowUp:
        follow_up = CustomerFollowUp(
            **obj_in.model_dump(), customer_id=customer_id, creator_id=creator_id
        )
        db.add(follow_up)
        db.commit()
        db.refresh(follow_up)
        return follow_up

    def get_follow_ups(self, db: Session, *, customer_id: int) -> List[CustomerFollowUp]:
        return (
            db.query(CustomerFollowUp)
            .filter(CustomerFollowUp.customer_id == customer_id)
            .order_by(CustomerFollowUp.follow_up_at.desc())
            .all()
        )

    def soft_delete(self, db: Session, *, customer_id: int) -> None:
        from datetime import datetime, timezone
        customer = db.query(Customer).get(customer_id)
        if customer:
            customer.is_deleted = True
            customer.deleted_at = datetime.now(timezone.utc)
            db.commit()


crud_customer = CRUDCustomer(Customer)
