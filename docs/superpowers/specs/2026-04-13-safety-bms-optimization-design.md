# Safety-BMS 全栈优化设计文档

## 背景与目标

`safety-bms` 项目经过前几轮安全与业务逻辑修复后，后端核心竞态条件和权限漏洞已得到控制。但代码中仍存在启动时序脆弱、N+1 查询、异常命名不一致、前端认证残留 localStorage、TypeScript 类型宽松、以及测试覆盖不足等问题。本设计文档将这些问题打包为一个可实施的大批次优化方案，采用 **Backend-First** 策略：先完成后端与认证链路改造，再统一收紧前端类型并移除历史残留。

## 优化范围

### 1. 后端安全与健壮性

#### 1.1 Redis 延迟初始化
- **现状**：`app/utils/redis_client.py` 在模块导入时即调用 `get_redis_client()` 并将结果赋值给 `redis_client`。若 Redis 尚未启动，整个后端应用无法启动。
- **方案**：
  - 移除模块级 `redis_client = get_redis_client()`
  - 所有消费 Redis 的模块（`auth_service.py`、`rate_limit.py` 等）改为在运行时调用 `get_redis_client()`
  - 保留 `_redis_pool` 的单例缓存，避免重复创建连接池
- **验收标准**：关闭 Redis 后启动后端应用不报错；首次请求打到需要 Redis 的逻辑时才报连接失败（且不影响无关接口）。

#### 1.2 异常命名规范化
- **现状**：`PaymentService.create_payment` 在收款超额时复用 `InvoiceAmountExceededError`，语义错误。
- **方案**：
  - 在 `app/core/exceptions.py` 中新建 `PaymentAmountExceededError`，提示文案为 `收款金额({requested:.2f})超过合同可收款余额({available:.2f})`
  - `payment_service.py` 改为抛出 `PaymentAmountExceededError`
- **验收标准**：API 测试脚本中触发超额收款时返回 400，且 `detail` 文案包含“收款”。

### 2. 后端性能

#### 2.1 修复 `get_overdue_contracts` N+1 查询
- **现状**：`payment_service.py` 的 `get_overdue_contracts` 先查出所有逾期候选合同，再 `for` 循环逐个调用 `crud_payment.get_sum_by_contract()`，导致 N+1 查询。
- **方案**：
  - 在 `crud_payment.py` 中新增 `get_sums_by_contract_ids(db, contract_ids: List[int]) -> Dict[int, Decimal]`
  - 使用一次查询：`SELECT contract_id, SUM(amount) FROM payments WHERE contract_id IN (...) GROUP BY contract_id`
  - `get_overdue_contracts` 先批量查出合同列表，再一次性查收款总额字典，最后在 Python 中过滤和组装 `ContractReceivable`
- **验收标准**：查询 100 条逾期合同时，SQL 日志中支付相关查询仅 1 条（原 100+1 条）。

### 3. 认证体系收尾

#### 3.1 后端 Cookie 认证稳定化
- **现状**：后端 `/auth/login`、`/auth/refresh` 已下发 `httpOnly` Cookie，且 `dependencies.py` 优先读取 Cookie，但 `/auth/logout` 仍要求 `get_current_user` 依赖，可能导致 token 过期后无法退出。
- **方案**：保持不变，当前逻辑已足够。本次仅确认 `refresh_token` Cookie 也在 `/auth/login` 时正确下发。

### 4. 前端工程化

#### 4.1 彻底移除 localStorage token 残留
- **现状**：
  - `authSlice.ts` 的 `setCredentials` 仍在 `localStorage.setItem('access_token', ...)`
  - `baseApi.ts` 的 `prepareHeaders` 手动从 Redux 读取 token 并注入 `Authorization`
- **方案**：
  - `authSlice.ts`：移除 `localStorage` 读写；`setCredentials` 仅更新 Redux state；`logout` 仅清理 Redux state
  - `baseApi.ts`：移除 `prepareHeaders` 中手动注入 `Authorization` 的逻辑。浏览器在 `withCredentials` 或同域场景下会自动携带 Cookie，后端目前无需 Header fallback（过渡期已过）
  - 若未来需要跨域无 Cookie 场景，可再添加 Header 注入
- **验收标准**：DevTools Application > Local Storage 中登录后不再出现 `access_token` / `refresh_token`；Network 面板中 `/api/v1` 请求自动携带 Cookie，`Authorization` Header 不再出现。

#### 4.2 TypeScript 类型收紧
- **现状**：多个页面表单处理使用 `values: any`，Dashboard 中使用 `d: any`。
- **方案**：
  - `Customers/index.tsx`：新增 `CustomerFormValues` 接口，替换 `handleCreate(values: any)`
  - `Contracts/index.tsx`：新增 `ContractFormValues` 接口，日期字段类型为 `dayjs.Dayjs`
  - `Services/index.tsx`：新增 `ServiceFormValues` 接口，日期字段类型为 `dayjs.Dayjs`
  - `Dashboard/index.tsx`：移除 `contractPieData.map((d: any)` 和 `serviceBarData.map((d: any)` 中的显式 `any`，使用内部推导类型或从 `stats` 推断
- **验收标准**：`npm run build` 零新增报错，且 `any` 显式使用数量减少。

### 5. 测试与基建

#### 5.1 后端引入 pytest
- **现状**：仅有一个集成测试脚本 `scripts/api_validation_tests.py`。
- **方案**：
  - `requirements.txt` 增加 `pytest`、`httpx`
  - 新建 `backend/pytest.ini`：
    ```ini
    [pytest]
    testpaths = tests
    pythonpath = .
    ```
  - 新建 `backend/tests/conftest.py`：
    - 提供 `TestClient` fixture（使用 `app.main:app`）
    - 提供 `authenticated_client` fixture（先登录获取 Cookie，再复用 Session）
  - 新建 `backend/tests/test_auth.py`：验证 Cookie 下发、logout 黑名单、刷新接口
- **验收标准**：`PYTHONPATH=. pytest tests/` 全部通过。

## 实施顺序（Backend-First）

1. **后端阶段**
   - Redis 延迟初始化
   - 新建 `PaymentAmountExceededError` 并替换引用
   - 修复 `get_overdue_contracts` N+1
   - 引入 pytest + 编写基础测试
   - 运行 `api_validation_tests.py` 确认后端稳定

2. **前端阶段**
   - 移除 `localStorage` 与 `Authorization` Header 注入
   - 收紧 `Customers`、`Contracts`、`Services`、`Dashboard` 类型
   - 运行 `npm run build` 确认编译通过

3. **联合验收**
   - 登录/登出流程端到端验证
   - 逾期合同列表加载性能对比（可选：打印 SQL 计数）
   - pytest 全绿 + build 全绿

## 文件变更清单

### 后端
- `backend/app/utils/redis_client.py`
- `backend/app/core/exceptions.py`
- `backend/app/services/payment_service.py`
- `backend/app/crud/payment.py`
- `backend/app/services/auth_service.py`
- `backend/app/core/rate_limit.py`
- `backend/requirements.txt`
- `backend/pytest.ini`（新建）
- `backend/tests/conftest.py`（新建）
- `backend/tests/test_auth.py`（新建）

### 前端
- `frontend/src/store/slices/authSlice.ts`
- `frontend/src/store/api/baseApi.ts`
- `frontend/src/pages/Customers/index.tsx`
- `frontend/src/pages/Contracts/index.tsx`
- `frontend/src/pages/Services/index.tsx`
- `frontend/src/pages/Dashboard/index.tsx`

## 风险评估

| 风险 | 缓解措施 |
|------|---------|
| 移除 localStorage 后某些边缘场景（如无痕模式）失效 | Cookie + Session 在无脑模式下本就无法持久化，与 localStorage 行为一致，无额外风险 |
| 移除 `Authorization` Header 后，若后端 Cookie 解析有 bug，前端全部 401 | 已在 `api_validation_tests.py` 中覆盖 Cookie 认证；修改后先跑端到端测试再合入 |
| `get_overdue_contracts` 批量查询改写错误导致金额计算偏差 | 保持旧逻辑作为对照，或编写单元测试断言同数据集下新旧函数结果一致 |
