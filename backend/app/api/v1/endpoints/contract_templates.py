from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.constants import PermissionCode
from app.core.exceptions import NotFoundError
from app.crud.contract import crud_contract_template
from app.db.session import get_db
from app.dependencies import require_permissions
from app.models.contract import ContractTemplate
from app.models.user import User
from app.schemas.common import FileUploadResponse, PageResponse, ResponseMsg
from app.schemas.contract import ContractTemplateCreate, ContractTemplateOut
from app.services.minio_service import minio_service
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/contract-templates", tags=["合同模板"])


@router.get("", response_model=PageResponse[ContractTemplateOut])
def list_contract_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    service_type: int | None = None,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = db.query(ContractTemplate)
    if service_type:
        query = query.filter(ContractTemplate.service_type == service_type)
    total = query.count()
    items = query.order_by(ContractTemplate.created_at.desc()).offset(skip).limit(page_size).all()
    items_out = []
    for t in items:
        out = ContractTemplateOut.model_validate(t)
        if t.service_type_obj:
            out.service_type_id = t.service_type_obj.id
            out.service_type_name = t.service_type_obj.name
            out.service_type_code = t.service_type_obj.code
        items_out.append(out)
    return make_page_response(total, items_out, page, page_size)


@router.post("", response_model=ContractTemplateOut, status_code=201)
def create_contract_template(
    body: ContractTemplateCreate,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_CREATE)),
    db: Session = Depends(get_db),
):
    return crud_contract_template.create(db, obj_in=body, created_by=current_user.id)


@router.post("/{template_id}/upload", response_model=FileUploadResponse)
def upload_template_file(
    template_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    template = crud_contract_template.get(db, id=template_id)
    if not template:
        raise NotFoundError("合同模板")
    result = minio_service.upload_file(file, prefix=f"contract-templates/{template_id}")
    crud_contract_template.update(db, db_obj=template, obj_in={"file_url": result["file_url"]})
    return result


@router.get("/{template_id}/download-url")
def get_template_download_url(
    template_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_READ)),
    db: Session = Depends(get_db),
):
    template = crud_contract_template.get(db, id=template_id)
    if not template or not template.file_url:
        raise NotFoundError("模板文件")
    url = minio_service.get_presigned_url(template.file_url, inline=True)
    return {"url": url}


@router.delete("/{template_id}", response_model=ResponseMsg)
def delete_contract_template(
    template_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_DELETE)),
    db: Session = Depends(get_db),
):
    template = crud_contract_template.get(db, id=template_id)
    if not template:
        raise NotFoundError("合同模板")
    if template.file_url:
        minio_service.delete_file(template.file_url)
    crud_contract_template.remove(db, id=template_id)
    return {"message": "删除成功"}
