from fastapi import HTTPException, status


class BusinessError(HTTPException):
    """业务逻辑错误基类"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(BusinessError):
    def __init__(self, resource: str = "资源"):
        super().__init__(f"{resource}不存在", status_code=status.HTTP_404_NOT_FOUND)


class DuplicateError(BusinessError):
    def __init__(self, resource: str = "资源"):
        super().__init__(f"{resource}已存在", status_code=status.HTTP_409_CONFLICT)


class InvoiceAmountExceededError(BusinessError):
    def __init__(self, available: float, requested: float):
        super().__init__(
            f"开票金额({requested:.2f})超过合同可开票余额({available:.2f})"
        )


class PaymentAmountExceededError(BusinessError):
    def __init__(self, available: float, requested: float):
        super().__init__(
            f"收款金额({requested:.2f})超过合同可收款余额({available:.2f})"
        )


class ContractStatusError(BusinessError):
    def __init__(self, detail: str = "合同状态不允许此操作"):
        super().__init__(detail)


class PermissionDeniedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
