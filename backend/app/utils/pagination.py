from typing import Any


def make_page_response(total: int, items: list[Any], page: int, page_size: int) -> dict:
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
