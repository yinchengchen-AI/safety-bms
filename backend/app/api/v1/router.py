from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    auth,
    users,
    roles,
    departments,
    customers,
    contracts,
    services,
    invoices,
    payments,
    dashboard,
    contract_templates,
    notifications,
    permissions,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(departments.router)
api_router.include_router(customers.router)
api_router.include_router(contracts.router)
api_router.include_router(contract_templates.router)
api_router.include_router(services.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(permissions.router)
