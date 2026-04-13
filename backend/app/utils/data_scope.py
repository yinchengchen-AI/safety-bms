from typing import Any
from sqlalchemy.orm import Query

from app.models.user import User, DataScope


_SCOPE_PRIORITY = {
    DataScope.ALL: 3,
    DataScope.DEPT: 2,
    DataScope.SELF: 1,
}


def _resolve_data_scope(current_user: User) -> DataScope:
    """根据用户角色的 data_scope 取优先级最高的值。"""
    if current_user.is_superuser:
        return DataScope.ALL
    scopes = []
    for role in current_user.roles:
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
    if current_user.is_superuser:
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
    if hasattr(model_class, "created_by"):
        return query.filter(model_class.created_by == current_user.id)
    if hasattr(model_class, "assignee_id"):
        return query.filter(model_class.assignee_id == current_user.id)
    if hasattr(model_class, "uploaded_by"):
        return query.filter(model_class.uploaded_by == current_user.id)
    if hasattr(model_class, "applied_by"):
        return query.filter(model_class.applied_by == current_user.id)
    if hasattr(model_class, "changed_by"):
        return query.filter(model_class.changed_by == current_user.id)
    if hasattr(model_class, "creator_id"):
        return query.filter(model_class.creator_id == current_user.id)
    return query


def check_data_scope(obj: Any, current_user: User) -> bool:
    """检查单条记录是否符合用户的数据权限范围。"""
    if current_user.is_superuser:
        return True

    scope = _resolve_data_scope(current_user)

    if scope == DataScope.ALL:
        return True

    if scope == DataScope.DEPT:
        user_dept_id = getattr(current_user, "department_id", None)
        obj_dept_id = getattr(obj, "department_id", None)
        if user_dept_id is not None and obj_dept_id is not None:
            return obj_dept_id == user_dept_id
        created_by = getattr(obj, "created_by", None)
        if created_by is not None:
            return created_by == current_user.id
        return True

    # SELF
    created_by = getattr(obj, "created_by", None)
    if created_by is not None:
        return created_by == current_user.id
    assignee_id = getattr(obj, "assignee_id", None)
    if assignee_id is not None:
        return assignee_id == current_user.id
    uploaded_by = getattr(obj, "uploaded_by", None)
    if uploaded_by is not None:
        return uploaded_by == current_user.id
    applied_by = getattr(obj, "applied_by", None)
    if applied_by is not None:
        return applied_by == current_user.id
    changed_by = getattr(obj, "changed_by", None)
    if changed_by is not None:
        return changed_by == current_user.id
    creator_id = getattr(obj, "creator_id", None)
    if creator_id is not None:
        return creator_id == current_user.id

    return True
