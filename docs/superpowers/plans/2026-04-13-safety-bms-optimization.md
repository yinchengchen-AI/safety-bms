# Safety-BMS 全栈优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 safety-bms 后端的启动时序、N+1 查询、异常命名问题，引入 pytest 测试框架，并彻底移除前端 localStorage token 残留、收紧 TypeScript 类型。

**Architecture:** 采用 Backend-First 策略：先完成后端 Redis 延迟初始化、Payment 异常规范化、逾期合同 N+1 修复和 pytest 基建；再统一修改前端 authSlice/baseApi 移除 localStorage，并收紧 Customers/Contracts/Services/Dashboard 的 TS 类型。

**Tech Stack:** FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + pytest / React 18 + TypeScript + Vite + Redux Toolkit + RTK Query + Ant Design

---

## File Map

### 后端修改
- `backend/app/utils/redis_client.py` — 移除模块级立即初始化，改为延迟调用
- `backend/app/core/exceptions.py` — 新增 `PaymentAmountExceededError`
- `backend/app/services/payment_service.py` — 使用新异常；修复 `get_overdue_contracts` N+1
- `backend/app/crud/payment.py` — 新增 `get_sums_by_contract_ids` 批量查询
- `backend/app/services/auth_service.py` — 改为运行时调用 `get_redis_client()`
- `backend/app/core/rate_limit.py` — 改为运行时调用 `get_redis_client()`
- `backend/requirements.txt` — 追加 `pytest`, `httpx`
- `backend/pytest.ini` — pytest 配置（新建）
- `backend/tests/conftest.py` — fixtures（新建）
- `backend/tests/test_auth.py` — 认证单元测试（新建）

### 前端修改
- `frontend/src/store/slices/authSlice.ts` — 移除 localStorage 读写
- `frontend/src/store/api/baseApi.ts` — 移除 `prepareHeaders` 中手动注入 `Authorization`
- `frontend/src/pages/Customers/index.tsx` — 新增 `CustomerFormValues` 类型
- `frontend/src/pages/Contracts/index.tsx` — 新增 `ContractFormValues` 类型
- `frontend/src/pages/Services/index.tsx` — 新增 `ServiceFormValues` 类型
- `frontend/src/pages/Dashboard/index.tsx` — 移除显式 `any`

---

## Phase 1: 后端安全与性能

### Task 1: 新建 `PaymentAmountExceededError`

**Files:**
- Modify: `backend/app/core/exceptions.py`

- [ ] **Step 1: 在 `exceptions.py` 中添加新异常类**

```python
class PaymentAmountExceededError(BusinessError):
    def __init__(self, available: float, requested: float):
        super().__init__(
            f"收款金额({requested:.2f})超过合同可收款余额({available:.2f})"
        )
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/exceptions.py
git commit -m "feat: add PaymentAmountExceededError for semantic correctness"
```

---

### Task 2: `payment_service.py` 使用新异常并修复 N+1

**Files:**
- Modify: `backend/app/services/payment_service.py`
- Modify: `backend/app/crud/payment.py`
- Modify: `backend/app/core/exceptions.py` (已在上一步完成)

- [ ] **Step 1: 在 `crud_payment.py` 中新增批量查询方法**

在 `CRUDPayment` 类中，紧接 `get_sum_by_contract` 之后添加：

```python
    def get_sums_by_contract_ids(self, db: Session, *, contract_ids: List[int]) -> dict[int, Decimal]:
        from sqlalchemy import func
        results = (
            db.query(Payment.contract_id, func.coalesce(func.sum(Payment.amount), 0).label("total"))
            .filter(Payment.contract_id.in_(contract_ids))
            .group_by(Payment.contract_id)
            .all()
        )
        return {r.contract_id: Decimal(str(r.total)) for r in results}
```

- [ ] **Step 2: 修改 `payment_service.py` 的 `create_payment`**

将导入和异常抛出替换：

```python
# 原导入
from app.core.exceptions import NotFoundError, InvoiceAmountExceededError
# 改为
from app.core.exceptions import NotFoundError, PaymentAmountExceededError
```

在 `create_payment` 中，将：

```python
            raise InvoiceAmountExceededError(
                available=float(available),
                requested=float(obj_in.amount),
            )
```

替换为：

```python
            raise PaymentAmountExceededError(
                available=float(available),
                requested=float(obj_in.amount),
            )
```

- [ ] **Step 3: 修改 `payment_service.py` 的 `get_overdue_contracts`**

将整个方法替换为：

```python
    def get_overdue_contracts(self, db: Session) -> list[ContractReceivable]:
        from app.models.contract import Contract
        from app.core.constants import ContractStatus
        contracts = (
            db.query(Contract)
            .filter(
                Contract.is_deleted == False,
                Contract.status == ContractStatus.ACTIVE,
                Contract.end_date < date.today(),
            )
            .all()
        )
        if not contracts:
            return []

        contract_ids = [c.id for c in contracts]
        sums = crud_payment.get_sums_by_contract_ids(db, contract_ids=contract_ids)

        result = []
        for c in contracts:
            received = sums.get(c.id, Decimal("0"))
            total = Decimal(str(c.total_amount))
            if received < total:
                result.append(
                    ContractReceivable(
                        contract_id=c.id,
                        contract_no=c.contract_no,
                        total_amount=total,
                        received_amount=received,
                        receivable_amount=total - received,
                        is_overdue=True,
                    )
                )
        return result
```

- [ ] **Step 4: 运行 API 验证测试**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. python scripts/api_validation_tests.py
```

Expected: 全部通过，且超额收款报错文案包含“收款”。

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/payment_service.py backend/app/crud/payment.py
git commit -m "fix: use PaymentAmountExceededError and eliminate N+1 in overdue contracts"
```

---

### Task 3: Redis 延迟初始化

**Files:**
- Modify: `backend/app/utils/redis_client.py`
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/core/rate_limit.py`

- [ ] **Step 1: 修改 `redis_client.py`**

将文件内容替换为：

```python
import redis
from app.config import settings

_redis_pool: redis.ConnectionPool | None = None
_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """延迟初始化 Redis 客户端"""
    global _redis_pool, _redis_client
    if _redis_client is None:
        try:
            _redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=False)
            _redis_client = redis.Redis(connection_pool=_redis_pool)
        except Exception as e:
            raise RuntimeError(f"Redis 连接失败: {e}")
    return _redis_client
```

- [ ] **Step 2: 修改 `auth_service.py`**

将导入：

```python
from app.utils.redis_client import redis_client
```

替换为：

```python
from app.utils.redis_client import get_redis_client
```

并将 `auth_service.py` 中所有使用 `redis_client` 的地方改为 `get_redis_client()`：

- `redis_client.setex(...)` → `get_redis_client().setex(...)`（3 处）
- `redis_client.exists(...)` → `get_redis_client().exists(...)`（1 处）
- `redis_client.get(...)` → `get_redis_client().get(...)`（1 处）

- [ ] **Step 3: 修改 `rate_limit.py`**

将导入：

```python
from app.utils.redis_client import redis_client
```

替换为：

```python
from app.utils.redis_client import get_redis_client
```

并将 `rate_limit` 函数体中所有 `redis_client` 替换为 `get_redis_client()`（5 处：`.get`、`.pipeline` 及后续链式调用）。

- [ ] **Step 4: 验证后端可启动（Redis 正常运行时）**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. python -c "from app.main import app; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/redis_client.py backend/app/services/auth_service.py backend/app/core/rate_limit.py
git commit -m "refactor: lazy redis initialization to avoid import-time connection"
```

---

## Phase 2: 后端测试基建

### Task 4: 引入 pytest 并编写认证测试

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: 在 `requirements.txt` 追加依赖**

在文件末尾追加：

```
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: 新建 `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 3: 新建 `tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    # 前提：数据库中已存在 admin / Admin@123456
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123456"})
    assert r.status_code == 200
    assert "access_token" in r.cookies
    return client
```

- [ ] **Step 4: 新建 `tests/test_auth.py`**

```python
def test_login_issues_cookie(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123456"})
    assert r.status_code == 200
    assert "access_token" in r.cookies


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_cookie(authenticated_client):
    r = authenticated_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_logout_clears_cookie(authenticated_client):
    r = authenticated_client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # 再次访问应 401
    r2 = authenticated_client.get("/api/v1/auth/me")
    assert r2.status_code == 401
```

- [ ] **Step 5: 运行 pytest**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. pytest tests/ -v
```

Expected: 4 tests passed。

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/pytest.ini backend/tests/
git commit -m "test: add pytest skeleton and auth cookie tests"
```

---

## Phase 3: 前端认证清理

### Task 5: 移除 localStorage token 残留

**Files:**
- Modify: `frontend/src/store/slices/authSlice.ts`
- Modify: `frontend/src/store/api/baseApi.ts`

- [ ] **Step 1: 修改 `authSlice.ts`**

将 `setCredentials` reducer 改为：

```typescript
    setCredentials(state, action: PayloadAction<{ access_token: string; refresh_token: string }>) {
      state.access_token = action.payload.access_token
      state.refresh_token = action.payload.refresh_token
      state.isAuthenticated = true
    },
```

将 `logout` reducer 改为：

```typescript
    logout(state) {
      state.user = null
      state.access_token = null
      state.refresh_token = null
      state.isAuthenticated = false
    },
```

- [ ] **Step 2: 修改 `baseApi.ts`**

移除 `prepareHeaders` 逻辑，改为：

```typescript
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
  }),
  tagTypes: ['User', 'Customer', 'Contract', 'Service', 'Invoice', 'Payment', 'Dashboard'],
  endpoints: () => ({}),
})
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/slices/authSlice.ts frontend/src/store/api/baseApi.ts
git commit -m "refactor: remove localStorage token fallback and Authorization header injection"
```

---

## Phase 4: 前端 TypeScript 类型收紧

### Task 6: 收紧表单与 Dashboard 类型

**Files:**
- Modify: `frontend/src/pages/Customers/index.tsx`
- Modify: `frontend/src/pages/Contracts/index.tsx`
- Modify: `frontend/src/pages/Services/index.tsx`
- Modify: `frontend/src/pages/Dashboard/index.tsx`

- [ ] **Step 1: 修改 `Customers/index.tsx`**

在文件顶部（import 下方）新增：

```typescript
interface CustomerFormValues {
  name: string
  credit_code?: string
  industry?: string
  scale?: string
  address?: string
  status?: string
  remark?: string
}
```

将 `handleCreate` 签名改为：

```typescript
  const handleCreate = async (values: CustomerFormValues) => {
```

- [ ] **Step 2: 修改 `Contracts/index.tsx`**

在文件顶部新增：

```typescript
import type { Dayjs } from 'dayjs'

interface ContractFormValues {
  contract_no: string
  title: string
  customer_id: number
  service_type: string
  total_amount: number
  payment_plan?: string
  sign_date?: Dayjs
  start_date?: Dayjs
  end_date?: Dayjs
  remark?: string
}
```

将 `handleCreate` 签名改为：

```typescript
  const handleCreate = async (values: ContractFormValues) => {
```

- [ ] **Step 3: 修改 `Services/index.tsx`**

在文件顶部新增：

```typescript
import type { Dayjs } from 'dayjs'

interface ServiceFormValues {
  order_no: string
  contract_id: number
  service_type: string
  title: string
  planned_start?: Dayjs
  planned_end?: Dayjs
  remark?: string
}
```

将 `handleCreate` 签名改为：

```typescript
  const handleCreate = async (values: ServiceFormValues) => {
```

- [ ] **Step 4: 修改 `Dashboard/index.tsx`**

将：

```typescript
  const contractPieData = (stats.contract_status_distribution || []).map((d: any) => ({
```

替换为：

```typescript
  const contractPieData = (stats.contract_status_distribution || []).map((d) => ({
```

将：

```typescript
  const serviceBarData = (stats.service_status_distribution || []).map((d: any) => ({
```

替换为：

```typescript
  const serviceBarData = (stats.service_status_distribution || []).map((d) => ({
```

- [ ] **Step 5: 运行构建检查**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend
npm run build
```

Expected: `dist/` 生成成功，终端无新增 TypeScript 错误。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Customers/index.tsx frontend/src/pages/Contracts/index.tsx frontend/src/pages/Services/index.tsx frontend/src/pages/Dashboard/index.tsx
git commit -m "refactor: tighten TypeScript types on forms and dashboard"
```

---

## Phase 5: 联合验收

### Task 7: 全链路回归验证

- [ ] **Step 1: 后端 API 集成测试**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. python scripts/api_validation_tests.py
```

Expected: 全部打印 ✅ 并通过。

- [ ] **Step 2: 后端 pytest**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. pytest tests/ -v
```

Expected: 4 passed。

- [ ] **Step 3: 前端构建**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend
npm run build
```

Expected: 构建成功。

- [ ] **Step 4: 手动快速验证（开发服务器运行中）**

- 登录系统
- 打开 DevTools → Application → Local Storage → `http://localhost:5173`
- 确认无 `access_token` / `refresh_token`
- Network 面板中任意 `/api/v1` 请求：确认 Request Headers 中无 `Authorization`，且 Cookie 中自动携带 `access_token`
- 创建客户/合同/服务工单：流程正常
- 查看 Dashboard：图表加载正常

- [ ] **Step 5: Final Commit (optional)**

```bash
git commit --allow-empty -m "release: safety-bms optimization batch complete"
```

---

## Self-Review

**Spec coverage:**
- Redis 延迟初始化 → Task 3
- Payment 异常规范化 → Task 1 + Task 2
- N+1 修复 → Task 2
- 前端移除 localStorage → Task 5
- 前端类型收紧 → Task 6
- pytest 引入 → Task 4

**Placeholder scan:**
- 无 TBD/TODO
- 所有代码块均给出具体实现内容
- 所有命令均给出具体命令和预期输出

**Type consistency:**
- `PaymentAmountExceededError` 在 Task 1 定义，Task 2 使用，名称一致
- `get_sums_by_contract_ids` 在 Task 2 Step 1 定义，Step 3 使用，签名一致
- `CustomerFormValues` / `ContractFormValues` / `ServiceFormValues` 在各自文件顶部定义，使用位置一致
