import contextlib
import uuid
from io import BytesIO

from fastapi import HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error

from app.config import settings

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "wps", "xls", "xlsx", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class MinIOService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error:
            pass  # 服务启动时桶可能尚未就绪，延迟创建

    def upload_file(self, file: UploadFile, prefix: str = "") -> dict:
        """上传文件并返回 MinIO 对象路径"""
        try:
            filename = file.filename or ""
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: .{ext or 'unknown'}，只允许 {', '.join(ALLOWED_EXTENSIONS)}",
                )

            content = file.file.read()
            file_size = len(content)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小({file_size / 1024 / 1024:.2f}MB)超过最大限制({MAX_FILE_SIZE / 1024 / 1024:.0f}MB)",
                )

            object_name = (
                f"{prefix}/{uuid.uuid4().hex}.{ext}" if prefix else f"{uuid.uuid4().hex}.{ext}"
            )
            self.client.put_object(
                self.bucket,
                object_name,
                BytesIO(content),
                length=file_size,
                content_type=file.content_type or "application/octet-stream",
            )
            return {
                "file_url": object_name,
                "file_name": file.filename,
                "file_size": file_size,
            }
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}") from e

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """生成预签名下载URL，通过 nginx /minio/ 代理访问"""
        from datetime import timedelta

        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=expires_seconds),
            )
            # 将内网地址替换为公网 nginx 代理地址
            # nginx 会代理 /minio/ 到 MinIO，并保持 Host: minio:9000 头，使签名验证通过
            public_url = url.replace(
                f"http://{settings.MINIO_ENDPOINT}", "http://43.133.14.168:82/minio"
            ).replace(f"https://{settings.MINIO_ENDPOINT}", "https://43.133.14.168:82/minio")
            return public_url
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"生成下载链接失败: {str(e)}") from e

    def delete_file(self, object_name: str) -> None:
        with contextlib.suppress(S3Error):
            self.client.remove_object(self.bucket, object_name)

    def upload_base64_image(self, base64_data: str, prefix: str = "") -> dict:
        """上传 base64 编码的 PNG 图片并返回 MinIO 对象路径"""
        try:
            import base64
            import re

            # 移除 data:image/png;base64, 前缀
            data = re.sub(r"^data:image/\w+;base64,", "", base64_data)
            content = base64.b64decode(data)
            file_size = len(content)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"图片大小({file_size / 1024 / 1024:.2f}MB)超过最大限制({MAX_FILE_SIZE / 1024 / 1024:.0f}MB)",
                )

            object_name = (
                f"{prefix}/{uuid.uuid4().hex}.png" if prefix else f"{uuid.uuid4().hex}.png"
            )
            self.client.put_object(
                self.bucket,
                object_name,
                BytesIO(content),
                length=file_size,
                content_type="image/png",
            )
            return {
                "file_url": object_name,
                "file_name": object_name.rsplit("/", 1)[-1],
                "file_size": file_size,
            }
        except S3Error as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}") from e


minio_service = MinIOService()
