from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: List[T]


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str


class ResponseMsg(BaseModel):
    message: str = "操作成功"


class FileUploadResponse(BaseModel):
    file_url: str
    file_name: str
    file_size: int
