#!/usr/bin/env python3
"""
初始化默认合同模板：上传模板文件到 MinIO 并在数据库中创建默认记录。
"""
import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.base_all import Base  # noqa: F401
from app.models.contract import ContractTemplate
from app.models.service_type import ServiceType
from app.services.minio_service import minio_service


TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "contracts" / "安全生产社会化服务_template.docx"
MINIO_OBJECT_NAME = "contract-templates/default-安全生产社会化服务_template.docx"


def seed(db: Session) -> None:
    if not TEMPLATE_PATH.exists():
        print(f"模板文件不存在: {TEMPLATE_PATH}")
        sys.exit(1)

    service_type = db.query(ServiceType).filter(ServiceType.is_active == True).first()
    if not service_type:
        print("错误：数据库中不存在可用的服务类型，请先创建服务类型")
        sys.exit(1)

    file_bytes = TEMPLATE_PATH.read_bytes()
    minio_service.client.put_object(
        minio_service.bucket,
        MINIO_OBJECT_NAME,
        BytesIO(file_bytes),
        length=len(file_bytes),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    existing = db.query(ContractTemplate).filter(ContractTemplate.is_default == True).first()
    if existing:
        existing.name = "安全生产社会化服务标准模板"
        existing.file_url = MINIO_OBJECT_NAME
        existing.service_type = service_type.id
        db.commit()
        db.refresh(existing)
        print(f"✅ 默认模板已更新: {existing.name} (id={existing.id}, service_type={service_type.name})")
        return

    template = ContractTemplate(
        name="安全生产社会化服务标准模板",
        service_type=service_type.id,
        file_url=MINIO_OBJECT_NAME,
        is_default=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    print(f"✅ 默认模板已创建: {template.name} (id={template.id}, service_type={service_type.name})")


def main():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
