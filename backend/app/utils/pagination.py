from typing import Any, List
from pydantic import BaseModel
from app.schemas.common import PageResponse


def make_page_response(total: int, items: List[Any], page: int, page_size: int) -> dict:
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
