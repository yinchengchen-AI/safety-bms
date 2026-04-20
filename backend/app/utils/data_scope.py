from typing import Any

from sqlalchemy import false
from sqlalchemy.orm import Query

from app.models.user import DataScope, User

_SCOPE_PRIORITY = {
    DataScope.ALL: 3,
    DataScope.DEPT: 2,
    DataScope.SELF: 1,
}

_OWNER_FIELDS = (
    "created_by",
    "assignee_id",
    "uploaded_by",
    "applied_by",
    "changed_by",
    "creator_id",
)


def _resolve_data_scope(current_user: User) -> DataScope:
    """根据用户角色的 data_scope 取优先级最高的值。"""
    if bool(getattr(current_user, "is_superuser", False)):
        return DataScope.ALL
    scopes = []
    for role in list(getattr(current_user, "roles", []) or []):
        ds = getattr(role, "data_scope", None)
        if ds:
            if isinstance(ds, DataScope):
                scopes.append(ds)
            else:
                scopes.append(DataScope(str(ds)))
    if not scopes:
        return DataScope.SELF
    return max(scopes, key=lambda s: _SCOPE_PRIORITY.get(s, 0))


# Public alias for auth_service and other callers
def resolve_data_scope(current_user: User) -> DataScope:
    """解析用户的数据范围。"""
    return _resolve_data_scope(current_user)


def apply_data_scope(query: Query, model_class: Any, current_user: User) -> Query:
    """将数据权限范围应用到查询。"""
    if bool(getattr(current_user, "is_superuser", False)):
        return query

    scope = _resolve_data_scope(current_user)

    if scope == DataScope.ALL:
        return query

    if scope == DataScope.DEPT:
        user_dept_id = getattr(current_user, "department_id", None)
        if user_dept_id is not None and hasattr(model_class, "department_id"):
            return query.filter(model_class.department_id == user_dept_id)
        return _apply_self_filters(query, model_class, current_user)

    # SELF
    return _apply_self_filters(query, model_class, current_user)


def _apply_self_filters(query: Query, model_class: Any, current_user: User) -> Query:
    for field in _OWNER_FIELDS:
        if hasattr(model_class, field):
            return query.filter(getattr(model_class, field) == current_user.id)
    if model_class is User:
        return query.filter(model_class.id == current_user.id)
    return query.filter(false())


def _matches_self_scope(obj: Any, current_user: User) -> bool:
    if isinstance(obj, User):
        return getattr(obj, "id", None) == current_user.id
    for field in _OWNER_FIELDS:
        value = getattr(obj, field, None)
        if value is not None:
            return value == current_user.id
    return False


def check_data_scope(obj: Any, current_user: User) -> bool:
    """检查单条记录是否符合用户的数据权限范围。"""
    if bool(getattr(current_user, "is_superuser", False)):
        return True

    scope = _resolve_data_scope(current_user)

    if scope == DataScope.ALL:
        return True

    if scope == DataScope.DEPT:
        user_dept_id = getattr(current_user, "department_id", None)
        obj_dept_id = getattr(obj, "department_id", None)
        if user_dept_id is not None and obj_dept_id is not None:
            return obj_dept_id == user_dept_id
        return _matches_self_scope(obj, current_user)

    # SELF
    return _matches_self_scope(obj, current_user)
