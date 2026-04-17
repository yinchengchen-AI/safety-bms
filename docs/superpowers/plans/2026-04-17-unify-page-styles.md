# 统一各功能页面风格 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对 React + Ant Design 前端的所有业务功能页面进行轻量级样式统一，使筛选栏、表格、抽屉表单、详情展示在各页面保持一致。

**Architecture:** 不引入新设计系统，仅通过调整现有页面的布局参数（Drawer 宽度、按钮样式、分页配置）实现统一。每个页面独立修改，修改后运行类型检查确认无误。

**Tech Stack:** React, TypeScript, Ant Design 5, Vite

---

## File Mapping

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/pages/Users/index.tsx` | Drawer 宽度 480 → 640 |
| `frontend/src/pages/ContractTemplates/index.tsx` | 新建模板 Modal → Drawer (640)；操作列按钮规范化；删除加 Popconfirm |
| `frontend/src/pages/Customers/index.tsx` | 新建 Drawer 520 → 640；详情 Drawer 600 → 720 |
| `frontend/src/pages/Payments/index.tsx` | Drawer 宽度 480 → 640 |
| `frontend/src/pages/Invoices/index.tsx` | Drawer 宽度 480 → 640 |
| `frontend/src/pages/Services/index.tsx` | 新建/编辑 Drawer 480 → 640；详情 Drawer 700 → 720 |
| `frontend/src/pages/Contracts/index.tsx` | 新建/编辑 Drawer 560 → 640；详情 Drawer 680 → 720 |

---

## Task 1: Users 页面

**Files:**
- Modify: `frontend/src/pages/Users/index.tsx`

- [ ] **Step 1: 修改新建用户 Drawer 宽度**

```tsx
// 将 width={480} 改为 width={640}
<Drawer title="新建用户" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
```

- [ ] **Step 2: 修改编辑用户 Drawer 宽度**

```tsx
// 将 width={480} 改为 width={640}
<Drawer title="编辑用户" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null) }} width={640} footer={
```

- [ ] **Step 3: 验证类型检查**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Users/index.tsx
git commit -m "style(users): unify drawer width to 640px"
```

---

## Task 2: ContractTemplates 页面

**Files:**
- Modify: `frontend/src/pages/ContractTemplates/index.tsx`

- [ ] **Step 1: 引入 Drawer 和 Popconfirm**

```tsx
import { Table, Button, Space, Select, Input, message, Drawer, Form, Upload, Tag, Popconfirm } from 'antd'
```

移除未使用的 `Modal`、`DeleteOutlined`（若删除按钮不再使用图标）。

- [ ] **Step 2: 将新建模板 Modal 替换为 Drawer**

删除：
```tsx
<Modal
  title="新建合同模板"
  open={createOpen}
  onCancel={() => { setCreateOpen(false); form.resetFields(); setCreateFile(null) }}
  onOk={() => form.submit()}
  confirmLoading={creating || uploading}
>
```

替换为：
```tsx
<Drawer
  title="新建合同模板"
  open={createOpen}
  onClose={() => { setCreateOpen(false); form.resetFields(); setCreateFile(null) }}
  width={640}
  footer={
    <Space style={{ float: 'right' }}>
      <Button onClick={() => { setCreateOpen(false); form.resetFields(); setCreateFile(null) }}>取消</Button>
      <Button type="primary" loading={creating || uploading} onClick={() => form.submit()}>创建</Button>
    </Space>
  }
>
```

注意：将 Modal 的 `onCancel` 逻辑平移到 Drawer 的 `onClose`。

- [ ] **Step 3: 规范操作列按钮**

将操作列渲染改为：

```tsx
{
  title: '操作',
  key: 'action',
  render: (_: any, r: ContractTemplate) => (
    <Space>
      {r.file_url && (
        <PermissionButton permission="contract:read" type="link" size="small" icon={<EyeOutlined />} onClick={() => handlePreview(r.id)}>预览</PermissionButton>
      )}
      {!r.file_url && (
        <Upload
          beforeUpload={(file) => {
            uploadTemplateFile({ id: r.id, file }).unwrap().then(() => message.success('上传成功')).catch(() => message.error('上传失败'))
            return false
          }}
          showUploadList={false}
          accept=".docx"
        >
          <PermissionButton permission="contract:update" type="link" size="small" icon={<UploadOutlined />}>上传</PermissionButton>
        </Upload>
      )}
      <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id)}>
        <PermissionButton permission="contract:delete" type="link" danger size="small">删除</PermissionButton>
      </Popconfirm>
    </Space>
  ),
}
```

- [ ] **Step 4: 验证类型检查**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ContractTemplates/index.tsx
git commit -m "style(contract-templates): switch create to drawer, unify action buttons"
```

---

## Task 3: Customers 页面

**Files:**
- Modify: `frontend/src/pages/Customers/index.tsx`

- [ ] **Step 1: 修改新建客户 Drawer 宽度**

```tsx
<Drawer title="新建客户" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
```

- [ ] **Step 2: 修改客户详情 Drawer 宽度**

```tsx
<Drawer title="客户详情" open width={720} onClose={onClose}>
```

- [ ] **Step 3: 验证类型检查并 Commit**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

```bash
git add frontend/src/pages/Customers/index.tsx
git commit -m "style(customers): unify drawer widths"
```

---

## Task 4: Payments 页面

**Files:**
- Modify: `frontend/src/pages/Payments/index.tsx`

- [ ] **Step 1: 修改新建收款记录 Drawer 宽度**

```tsx
<Drawer title="新建收款记录" open={createOpen} onClose={() => { setCreateOpen(false); setContractId(undefined) }} width={640} footer={
```

- [ ] **Step 2: 修改编辑收款记录 Drawer 宽度**

```tsx
<Drawer title="编辑收款记录" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null); setContractId(undefined) }} width={640} footer={
```

- [ ] **Step 3: 验证类型检查并 Commit**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

```bash
git add frontend/src/pages/Payments/index.tsx
git commit -m "style(payments): unify drawer widths to 640px"
```

---

## Task 5: Invoices 页面

**Files:**
- Modify: `frontend/src/pages/Invoices/index.tsx`

- [ ] **Step 1: 修改新建开票 Drawer 宽度**

```tsx
<Drawer title="新建开票申请" open={createOpen} onClose={() => { setCreateOpen(false); setCustomerId(undefined); setContractId(undefined) }} width={640} footer={
```

- [ ] **Step 2: 修改编辑发票 Drawer 宽度**

```tsx
<Drawer title="编辑发票" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null); setCustomerId(undefined); setContractId(undefined) }} width={640} footer={
```

- [ ] **Step 3: 验证类型检查并 Commit**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

```bash
git add frontend/src/pages/Invoices/index.tsx
git commit -m "style(invoices): unify drawer widths to 640px"
```

---

## Task 6: Services 页面

**Files:**
- Modify: `frontend/src/pages/Services/index.tsx`

- [ ] **Step 1: 修改新建服务工单 Drawer 宽度**

```tsx
<Drawer title="新建服务工单" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
```

- [ ] **Step 2: 编辑服务工单 Drawer 宽度**

```tsx
<Drawer title="编辑服务工单" open={editOpen} onClose={() => setEditOpen(false)} width={640} footer={
```

- [ ] **Step 3: 修改工单详情 Drawer 宽度**

```tsx
<Drawer title="工单详情" open width={720} onClose={onClose} footer={footerButtons}>
```

- [ ] **Step 4: 验证类型检查并 Commit**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

```bash
git add frontend/src/pages/Services/index.tsx
git commit -m "style(services): unify drawer widths"
```

---

## Task 7: Contracts 页面

**Files:**
- Modify: `frontend/src/pages/Contracts/index.tsx`

- [ ] **Step 1: 修改新建合同 Drawer 宽度**

```tsx
<Drawer title="新建合同" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
```

- [ ] **Step 2: 修改编辑合同 Drawer 宽度**

```tsx
<Drawer title="编辑合同" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null) }} width={640} footer={
```

- [ ] **Step 3: 修改合同详情 Drawer 宽度**

```tsx
<Drawer title="合同详情" open width={720} onClose={onClose}
```

- [ ] **Step 4: 验证类型检查并 Commit**

Run: `cd frontend && npm run build`
Expected: 无 TypeScript 错误

```bash
git add frontend/src/pages/Contracts/index.tsx
git commit -m "style(contracts): unify drawer widths"
```

---

## Task 8: 全局类型检查与验证

- [ ] **Step 1: 运行完整构建**

Run: `cd frontend && npm run build`
Expected: 构建成功，无 TypeScript 错误

- [ ] **Step 2: Commit 总结（如需要）**

若前面各任务已分别 commit，本步骤无需额外 commit。若用户要求合并，可执行：

```bash
git log --oneline -10
```

---

## Self-Review Checklist

- [x] **Spec coverage**: 所有页面的 Drawer 宽度统一已覆盖；ContractTemplates 的 Modal→Drawer 已覆盖；操作列按钮规范化已覆盖。
- [x] **Placeholder scan**: 无 TBD/TODO。
- [x] **Type consistency**: Drawer width 统一为 640（详情为 720），footer 结构一致，无类型冲突。
