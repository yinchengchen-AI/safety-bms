from sqlalchemy.orm import Session

from app.core.constants import ServiceOrderStatus
from app.core.exceptions import BusinessError
from app.crud.base import CRUDBase
from app.models.service import ServiceItem, ServiceOrder, ServiceReport
from app.schemas.service import (
    ServiceItemCreate,
    ServiceItemUpdate,
    ServiceOrderCreate,
    ServiceOrderUpdate,
)


class CRUDServiceOrder(CRUDBase[ServiceOrder, ServiceOrderCreate, ServiceOrderUpdate]):
    def create(self, db: Session, *, obj_in: ServiceOrderCreate) -> ServiceOrder:
        items = obj_in.items
        data = obj_in.model_dump(exclude={"items"})
        db_obj = ServiceOrder(**data)
        db.add(db_obj)
        db.flush()
        for item in items:
            db.add(ServiceItem(**item.model_dump(), order_id=db_obj.id))
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        contract_id: int | None = None,
        assignee_id: int | None = None,
        status: ServiceOrderStatus | None = None,
    ) -> tuple[int, list[ServiceOrder]]:
        query = db.query(ServiceOrder)
        if contract_id:
            query = query.filter(ServiceOrder.contract_id == contract_id)
        if assignee_id:
            query = query.filter(ServiceOrder.assignee_id == assignee_id)
        if status:
            query = query.filter(ServiceOrder.status == status)
        total = query.count()
        items = query.order_by(ServiceOrder.created_at.desc()).offset(skip).limit(limit).all()
        return total, items

    def update_status(
        self, db: Session, *, db_obj: ServiceOrder, new_status: ServiceOrderStatus
    ) -> ServiceOrder:
        from datetime import date

        db_obj.status = new_status
        if new_status == ServiceOrderStatus.IN_PROGRESS and not db_obj.actual_start:
            db_obj.actual_start = date.today()
        if (
            new_status in (ServiceOrderStatus.COMPLETED, ServiceOrderStatus.ACCEPTED)
            and not db_obj.actual_end
        ):
            db_obj.actual_end = date.today()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_report(
        self,
        db: Session,
        *,
        order_id: int,
        uploaded_by: int,
        file_name: str,
        file_url: str,
        file_size: int = 0,
    ) -> ServiceReport:
        report = ServiceReport(
            order_id=order_id,
            uploaded_by=uploaded_by,
            file_name=file_name,
            file_url=file_url,
            file_size=file_size,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def create_item(self, db: Session, *, order_id: int, obj_in: ServiceItemCreate) -> ServiceItem:
        item = ServiceItem(**obj_in.model_dump(), order_id=order_id)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update_item(
        self, db: Session, *, db_obj: ServiceItem, obj_in: ServiceItemUpdate
    ) -> ServiceItem:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_item(self, db: Session, *, item_id: int) -> ServiceItem | None:
        item = db.query(ServiceItem).filter(ServiceItem.id == item_id).first()
        if item:
            db.delete(item)
            db.commit()
        return item

    def delete_report(self, db: Session, *, report_id: int) -> ServiceReport | None:
        report = db.query(ServiceReport).filter(ServiceReport.id == report_id).first()
        if report:
            db.delete(report)
            db.commit()
        return report

    def remove(self, db: Session, *, id: int) -> ServiceOrder | None:
        obj = db.query(ServiceOrder).filter(ServiceOrder.id == id).first()
        if not obj:
            return None
        if obj.status != ServiceOrderStatus.PENDING:
            raise BusinessError("仅允许删除待处理状态的服务工单", status_code=400)
        db.delete(obj)
        db.commit()
        return obj


crud_service = CRUDServiceOrder(ServiceOrder)
