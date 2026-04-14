from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.schemas.service import (
    ServiceOrderCreate,
    ServiceOrderUpdate,
    ServiceOrderOut,
    ServiceOrderListOut,
    ServiceOrderStatusUpdate,
    ServiceReportOut,
    ServiceItemCreate,
    ServiceItemUpdate,
    ServiceItemOut,
)
from app.schemas.common import PageResponse, ResponseMsg, FileUploadResponse
from app.crud.service import crud_service
from app.dependencies import require_permissions
from app.core.exceptions import NotFoundError, PermissionDeniedError, BusinessError
from app.core.constants import ServiceOrderStatus, PermissionCode
from app.models.service import ServiceOrder
from app.models.contract import Contract
from app.models.user import User
from app.services.minio_service import minio_service
from app.services.notification_service import notification_service
from app.utils.data_scope import apply_data_scope, check_data_scope
from app.utils.pagination import make_page_response
from app.utils.excel_export import export_excel_response

router = APIRouter(prefix="/services", tags=["服务管理"])


def _get_service_order_with_relations(
    db: Session, order_id: int
) -> Optional[ServiceOrder]:
    return (
        db.query(ServiceOrder)
        .options(
            joinedload(ServiceOrder.contract).joinedload(Contract.customer),
            joinedload(ServiceOrder.assignee),
        )
        .filter(ServiceOrder.id == order_id)
        .first()
    )


@router.get("", response_model=PageResponse[ServiceOrderListOut])
def list_service_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    contract_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[ServiceOrderStatus] = None,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(ServiceOrder)
    if contract_id:
        query = query.filter(ServiceOrder.contract_id == contract_id)
    if assignee_id:
        query = query.filter(ServiceOrder.assignee_id == assignee_id)
    if status:
        query = query.filter(ServiceOrder.status == status)
    query = apply_data_scope(query, ServiceOrder, current_user)
    total = query.count()
    items = (
        query.options(
            joinedload(ServiceOrder.contract).joinedload(Contract.customer),
            joinedload(ServiceOrder.assignee),
        )
        .order_by(ServiceOrder.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        out = ServiceOrderListOut.model_validate(item)
        out.customer_name = (
            item.contract.customer.name
            if item.contract and item.contract.customer
            else None
        )
        out.assignee_name = item.assignee.full_name if item.assignee else None
        result.append(out)
    return make_page_response(total, result, page, page_size)


@router.get("/export")
def export_service_orders(
    contract_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[ServiceOrderStatus] = None,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    query = db.query(ServiceOrder)
    if contract_id:
        query = query.filter(ServiceOrder.contract_id == contract_id)
    if assignee_id:
        query = query.filter(ServiceOrder.assignee_id == assignee_id)
    if status:
        query = query.filter(ServiceOrder.status == status)
    query = apply_data_scope(query, ServiceOrder, current_user)
    items = (
        query.options(
            joinedload(ServiceOrder.contract).joinedload(Contract.customer),
            joinedload(ServiceOrder.assignee),
        )
        .order_by(ServiceOrder.created_at.desc())
        .all()
    )
    headers = [
        "工单编号",
        "标题",
        "客户名称",
        "服务类型",
        "负责人",
        "状态",
        "计划开始",
        "计划结束",
        "创建时间",
    ]
    rows = []
    for item in items:
        rows.append(
            [
                item.order_no,
                item.title,
                item.contract.customer.name
                if item.contract and item.contract.customer
                else "",
                item.service_type.value if item.service_type else "",
                item.assignee.full_name if item.assignee else "",
                item.status.value if item.status else "",
                item.planned_start.strftime("%Y-%m-%d") if item.planned_start else "",
                item.planned_end.strftime("%Y-%m-%d") if item.planned_end else "",
                item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
            ]
        )
    from datetime import datetime

    return export_excel_response(
        f"service_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", headers, rows
    )


@router.post("", response_model=ServiceOrderOut, status_code=201)
def create_service_order(
    body: ServiceOrderCreate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_CREATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.create(db, obj_in=body)
    if body.assignee_id and body.assignee_id != current_user.id:
        assignee = db.query(User).filter(User.id == body.assignee_id).first()
        if assignee:
            notification_service.create(
                db,
                user_id=assignee.id,
                title="新服务工单分配",
                content=f"您被分配了新的服务工单：{order.title}。",
            )
    return order


@router.get("/{order_id}", response_model=ServiceOrderOut)
def get_service_order(
    order_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    order = _get_service_order_with_relations(db, order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise BusinessError("无权查看该记录", status_code=403)
    result = ServiceOrderOut.model_validate(order)
    result.customer_name = (
        order.contract.customer.name
        if order.contract and order.contract.customer
        else None
    )
    result.assignee_name = order.assignee.full_name if order.assignee else None
    return result


@router.patch("/{order_id}", response_model=ServiceOrderOut)
def update_service_order(
    order_id: int,
    body: ServiceOrderUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = _get_service_order_with_relations(db, order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    updated = crud_service.update(db, db_obj=order, obj_in=body)
    result = ServiceOrderOut.model_validate(updated)
    result.customer_name = (
        updated.contract.customer.name
        if updated.contract and updated.contract.customer
        else None
    )
    result.assignee_name = updated.assignee.full_name if updated.assignee else None
    return result


@router.post("/{order_id}/status", response_model=ServiceOrderOut)
def update_status(
    order_id: int,
    body: ServiceOrderStatusUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = _get_service_order_with_relations(db, order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    old_status = order.status
    updated = crud_service.update_status(db, db_obj=order, new_status=body.status)
    if updated.assignee_id and updated.assignee_id != current_user.id:
        if (
            body.status == ServiceOrderStatus.IN_PROGRESS
            and old_status != ServiceOrderStatus.IN_PROGRESS
        ):
            notification_service.create(
                db,
                user_id=updated.assignee_id,
                title="服务工单开始处理",
                content=f"服务工单 {updated.title} 已开始处理。",
            )
        elif (
            body.status == ServiceOrderStatus.COMPLETED
            and old_status != ServiceOrderStatus.COMPLETED
        ):
            notification_service.create(
                db,
                user_id=updated.assignee_id,
                title="服务工单已完成",
                content=f"服务工单 {updated.title} 已完成。",
            )
    result = ServiceOrderOut.model_validate(updated)
    result.customer_name = (
        updated.contract.customer.name
        if updated.contract and updated.contract.customer
        else None
    )
    result.assignee_name = updated.assignee.full_name if updated.assignee else None
    return result


@router.post("/{order_id}/reports", response_model=FileUploadResponse)
def upload_report(
    order_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.get(db, id=order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    result = minio_service.upload_file(file, prefix=f"service-reports/{order_id}")
    crud_service.add_report(
        db,
        order_id=order_id,
        uploaded_by=current_user.id,
        file_name=result["file_name"],
        file_url=result["file_url"],
        file_size=result["file_size"],
    )
    return result


# ---- ServiceItem CRUD ----


@router.post("/{order_id}/items", response_model=ServiceItemOut, status_code=201)
def create_service_item(
    order_id: int,
    body: ServiceItemCreate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.get(db, id=order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    item = crud_service.create_item(db, order_id=order_id, obj_in=body)
    return item


@router.patch("/{order_id}/items/{item_id}", response_model=ServiceItemOut)
def update_service_item(
    order_id: int,
    item_id: int,
    body: ServiceItemUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.get(db, id=order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    item = crud_service.delete_item(db, item_id=item_id)
    if not item:
        raise NotFoundError("服务项")
    if item.order_id != order_id:
        raise NotFoundError("服务项")
    updated = crud_service.update_item(db, db_obj=item, obj_in=body)
    return updated


@router.delete("/{order_id}/items/{item_id}")
def delete_service_item(
    order_id: int,
    item_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.get(db, id=order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    item = crud_service.delete_item(db, item_id=item_id)
    if not item:
        raise NotFoundError("服务项")
    if item.order_id != order_id:
        raise NotFoundError("服务项")
    return {"message": "删除成功"}


# ---- ServiceReport Delete ----


@router.delete("/{order_id}/reports/{report_id}")
def delete_service_report(
    order_id: int,
    report_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.get(db, id=order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    report = crud_service.delete_report(db, report_id=report_id)
    if not report:
        raise NotFoundError("服务报告")
    if report.order_id != order_id:
        raise NotFoundError("服务报告")
    return {"message": "删除成功"}


# ---- ServiceOrder Delete ----


@router.delete("/{order_id}")
def delete_service_order(
    order_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    order = crud_service.get(db, id=order_id)
    if not order:
        raise NotFoundError("服务工单")
    if not check_data_scope(order, current_user):
        raise PermissionDeniedError()
    crud_service.remove(db, id=order_id)
    return {"message": "删除成功"}
