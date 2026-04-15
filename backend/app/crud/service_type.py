from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.service_type import ServiceType
from app.schemas.service_type import ServiceTypeCreate, ServiceTypeUpdate


class CRUDServiceType(CRUDBase[ServiceType, ServiceTypeCreate, ServiceTypeUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Optional[ServiceType]:
        return db.query(ServiceType).filter(ServiceType.code == code).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[int, List[ServiceType]]:
        query = db.query(ServiceType)
        if is_active is not None:
            query = query.filter(ServiceType.is_active == is_active)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items

    def get_usage_counts(self, db: Session, *, service_type_id: int) -> dict:
        from app.models.contract import Contract, ContractTemplate
        from app.models.service import ServiceOrder

        contract_count = (
            db.query(func.count(Contract.id))
            .filter(Contract.service_type == service_type_id)
            .scalar()
        )
        order_count = (
            db.query(func.count(ServiceOrder.id))
            .filter(ServiceOrder.service_type == service_type_id)
            .scalar()
        )
        template_count = (
            db.query(func.count(ContractTemplate.id))
            .filter(ContractTemplate.service_type == service_type_id)
            .scalar()
        )
        return {
            "contract_count": contract_count,
            "order_count": order_count,
            "template_count": template_count,
        }


crud_service_type = CRUDServiceType(ServiceType)
