# 统一各功能页面风格设计文档

## 目标

对系统现有业务功能页面（Customers、Contracts、Services、Invoices、Payments、Users、Roles、Profile 等）进行轻量级样式统一，消除各页面在筛选栏布局、按钮分组、表格间距、表单抽屉、详情展示上的不一致，提升整体视觉整齐度和用户操作预期一致性。

## 范围

### 包含页面

- `src/pages/Customers/index.tsx`
- `src/pages/Contracts/index.tsx`
- `src/pages/Services/index.tsx`
- `src/pages/Invoices/index.tsx`
- `src/pages/Payments/index.tsx`
- `src/pages/Users/index.tsx`
- `src/pages/Roles/index.tsx`
- `src/pages/Profile/index.tsx`

### 不包含

- Dashboard（已完成并确认满足当前风格）
- Login（独立视觉，无需统一）
- 新增业务逻辑或后端接口改动

## 设计规范

### 1. 列表页顶部操作区

```tsx
<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
  {/* 左侧：搜索 + 筛选 */}
  <Space>
    <Input.Search placeholder="搜索..." allowClear />
    {/* 其他筛选控件 */}
  </Space>
  {/* 右侧：操作按钮 */}
  <Space>
    <Button onClick={handleExport}>导出</Button>
    <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>新建</Button>
  </Space>
</div>
```

- 统一使用 `display: flex; justifyContent: space-between; alignItems: center; marginBottom: 16`
- 搜索框默认宽度 `240px`
- 新建按钮统一带 `PlusOutlined` 图标，`type="primary"`
- 导出按钮统一为默认样式，`type` 不指定

### 2. 表格

- 统一使用 `rowKey="id"`
- 统一使用默认 `pagination`，配置 `showTotal: (t) => \`共 ${t} 条\``
- 页面加载状态统一使用 `loading={isLoading}`
- 操作列按钮统一为 `type="link"`，编辑在前、删除在后
- 删除统一使用 `Popconfirm`

### 3. 表单抽屉（Create / Edit）

- 统一宽度 `width={640}`
- 统一 `Form` 布局 `layout="vertical"`
- 抽屉标题：`editingId ? '编辑xxx' : '新建xxx'`
- 底部 footer 统一右对齐：取消 + 保存（primary，loading）

### 4. 详情展示

- 统一使用 `Drawer` 而非 `Modal`
- 统一宽度 `width={720}`
- 使用 `Descriptions` 或自定义详情布局

### 5. 间距与结构

- 页面最外层统一不加额外 `padding`（由布局组件 `Layout.Content` 控制）
- 列表页内部不嵌套多余 `Card`
- 使用 `Row gutter={[16, 16]}` 的场景（如 Dashboard、Profile）保持不变

### 6. 状态标签颜色

- 复用项目中已有的状态颜色映射，不新增自定义颜色变量
- 标签使用 Ant Design `Tag`，颜色根据现有 `statusColorMap` 或枚举映射

## 实施顺序

按页面依赖复杂度由低到高逐步修改：

1. Roles（结构最简单）
2. Users
3. Profile
4. Customers
5. Payments
6. Invoices
7. Services
8. Contracts（逻辑最复杂，最后处理）

每修改完一个页面即进行类型检查 `npm run build`，确保无 TypeScript 错误。

## 验证方式

1. 运行 `npm run build` 通过类型检查。
2. 启动前端 dev server，逐页确认：
   - 顶部操作区左右分布一致
   - 表格加载、分页、操作列风格一致
   - 新建/编辑抽屉宽度和布局一致
   - 详情展示统一为 Drawer
3. 无功能退化（搜索、筛选、导出、增删改查行为与修改前一致）。
