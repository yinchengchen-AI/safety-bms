#!/usr/bin/env python3
"""
通知场景验证测试脚本
"""
import requests
from datetime import date, timedelta
import uuid

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USER = {"username": "admin", "password": "Admin@123456"}

session = requests.Session()


def login():
    r = session.post(f"{BASE_URL}/auth/login", json=ADMIN_USER)
    assert r.status_code == 200, f"登录失败: {r.text}"
    data = r.json()
    session.headers["Authorization"] = f"Bearer {data['access_token']}"
    return data


def create_customer() -> int:
    uid = str(uuid.uuid4())[:8]
    payload = {
        "name": f"测试客户-{uid}",
        "credit_code": f"91110105MA{uid}",
        "industry": "IT",
        "address": "北京市",
        "contacts": [{"name": "张三", "phone": "13800138000", "email": "zhangsan@example.com"}],
    }
    r = session.post(f"{BASE_URL}/customers", json=payload)
    assert r.status_code == 201, f"创建客户失败: {r.text}"
    return r.json()["id"]


def create_contract(customer_id: int, total_amount: float = 10000, end_date=None):
    payload = {
        "contract_no": f"C-{date.today().isoformat()}-{total_amount}-{str(uuid.uuid4())[:4]}",
        "title": "测试合同",
        "customer_id": customer_id,
        "service_type": "evaluation",
        "total_amount": total_amount,
        "sign_date": date.today().isoformat(),
        "start_date": date.today().isoformat(),
        "end_date": (end_date or (date.today() + timedelta(days=30))).isoformat(),
    }
    r = session.post(f"{BASE_URL}/contracts", json=payload)
    assert r.status_code == 201, f"创建合同失败: {r.text}"
    return r.json()["id"]


def activate_contract(contract_id: int):
    """通过数据库直接设置合同为 active，避免模板依赖"""
    import psycopg2, os
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "safety_bms"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )
    cur = conn.cursor()
    cur.execute("UPDATE contracts SET status = 'ACTIVE' WHERE id = %s", (contract_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_notifications() -> list:
    r = session.get(f"{BASE_URL}/notifications")
    assert r.status_code == 200, f"获取通知失败: {r.text}"
    return r.json().get("items", [])


def clear_notifications():
    r = session.delete(f"{BASE_URL}/notifications/clear-all")
    assert r.status_code == 200, f"清空通知失败: {r.text}"


def test_invoice_issued_notification():
    clear_notifications()
    customer_id = create_customer()
    contract_id = create_contract(customer_id)
    activate_contract(contract_id)
    # 创建发票
    invoice_payload = {
        "contract_id": contract_id,
        "invoice_no": f"INV-{contract_id}-{str(uuid.uuid4())[:4]}",
        "invoice_type": "special",
        "amount": 1000,
        "tax_rate": 0.06,
        "invoice_date": date.today().isoformat(),
    }
    r = session.post(f"{BASE_URL}/invoices", json=invoice_payload)
    assert r.status_code == 201, f"创建发票失败: {r.text}"
    invoice_id = r.json()["id"]

    before = get_notifications()
    # 更新状态为 issued
    r = session.patch(f"{BASE_URL}/invoices/{invoice_id}", json={"status": "issued"})
    assert r.status_code == 200, f"更新发票状态失败: {r.text}"
    after = get_notifications()

    assert len(after) > len(before), "发票 issued 后未收到通知"
    before_ids = {n["id"] for n in before}
    new_titles = [n["title"] for n in after if n["id"] not in before_ids]
    assert "发票已开具" in new_titles, f"未找到'发票已开具'通知, 新增: {new_titles}"
    print("✅ 发票已开具通知通过")


def test_invoice_sent_notification():
    clear_notifications()
    customer_id = create_customer()
    contract_id = create_contract(customer_id)
    activate_contract(contract_id)
    invoice_payload = {
        "contract_id": contract_id,
        "invoice_no": f"INV-{contract_id}-{str(uuid.uuid4())[:4]}",
        "invoice_type": "special",
        "amount": 1000,
        "tax_rate": 0.06,
        "invoice_date": date.today().isoformat(),
    }
    r = session.post(f"{BASE_URL}/invoices", json=invoice_payload)
    assert r.status_code == 201, f"创建发票失败: {r.text}"
    invoice_id = r.json()["id"]

    # 先变 issued
    r = session.patch(f"{BASE_URL}/invoices/{invoice_id}", json={"status": "issued"})
    assert r.status_code == 200, f"更新发票为 issued 失败: {r.text}"
    before = get_notifications()
    # 再变 sent
    r = session.patch(f"{BASE_URL}/invoices/{invoice_id}", json={"status": "sent"})
    assert r.status_code == 200, f"更新发票状态失败: {r.text}"
    after = get_notifications()

    assert len(after) > len(before), f"发票 sent 后未收到通知, before={len(before)}, after={len(after)}"
    before_ids = {n["id"] for n in before}
    new_titles = [n["title"] for n in after if n["id"] not in before_ids]
    assert "发票已寄出" in new_titles, f"未找到'发票已寄出'通知, 新增: {new_titles}"
    print("✅ 发票已寄出通知通过")


def test_payment_notification():
    clear_notifications()
    customer_id = create_customer()
    contract_id = create_contract(customer_id)
    before = get_notifications()
    payment_payload = {
        "contract_id": contract_id,
        "payment_no": f"PAY-{contract_id}-{str(uuid.uuid4())[:4]}",
        "amount": 500,
        "payment_date": date.today().isoformat(),
        "payment_method": "bank_transfer",
    }
    r = session.post(f"{BASE_URL}/payments", json=payment_payload)
    assert r.status_code == 201, f"创建收款失败: {r.text}"
    after = get_notifications()

    assert len(after) > len(before), "新增收款后未收到通知"
    before_ids = {n["id"] for n in before}
    new_titles = [n["title"] for n in after if n["id"] not in before_ids]
    assert "新增收款记录" in new_titles, f"未找到'新增收款记录'通知, 新增: {new_titles}"
    print("✅ 新增收款记录通知通过")


def test_contract_terminated_notification():
    clear_notifications()
    customer_id = create_customer()
    contract_id = create_contract(customer_id)
    before = get_notifications()
    r = session.post(f"{BASE_URL}/contracts/{contract_id}/status", json={"status": "terminated"})
    assert r.status_code == 200, f"终止合同失败: {r.text}"
    after = get_notifications()

    assert len(after) > len(before), "合同终止后未收到通知"
    before_ids = {n["id"] for n in before}
    new_titles = [n["title"] for n in after if n["id"] not in before_ids]
    assert "合同已终止" in new_titles, f"未找到'合同已终止'通知, 新增: {new_titles}"
    print("✅ 合同已终止通知通过")


def test_cli_notification_tasks():
    """验证 CLI 脚本可正常执行不报错（依赖数据库中有对应数据）"""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "app/cli/notification_tasks.py"],
        capture_output=True,
        text=True,
        cwd="/Users/yinchengchen/ClaudeCode/safety-bms/backend",
        env={"PYTHONPATH": "."},
    )
    assert result.returncode == 0, f"CLI 执行失败: {result.stderr}"
    assert "发送即将到期提醒" in result.stdout, f"CLI 输出异常: {result.stdout}"
    assert "发送逾期应收提醒" in result.stdout, f"CLI 输出异常: {result.stdout}"
    print("✅ CLI 定时通知脚本执行通过")


def main():
    print("=" * 50)
    print("开始通知场景验证测试")
    print("=" * 50)
    login()
    test_invoice_issued_notification()
    test_invoice_sent_notification()
    test_payment_notification()
    test_contract_terminated_notification()
    test_cli_notification_tasks()
    print("=" * 50)
    print("🎉 全部通知测试通过")
    print("=" * 50)


if __name__ == "__main__":
    main()
