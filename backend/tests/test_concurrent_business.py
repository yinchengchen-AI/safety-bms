import threading
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.constants import ContractStatus, InvoiceType, PaymentMethod
from app.core.security import get_password_hash
from app.crud.invoice import crud_invoice
from app.crud.payment import crud_payment
from app.db.session import SessionLocal
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import DataScope, Role, User
from app.schemas.invoice import InvoiceAuditRequest
from app.schemas.payment import PaymentCreate
from app.services.invoice_service import invoice_service
from app.services.payment_service import payment_service


def _make_db() -> Session:
    return SessionLocal()


def _create_user(username: str):
    db = _make_db()
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.close()
        return user
    role = Role(name=f"role_{username}", description="test", data_scope=DataScope.ALL)
    db.add(role)
    db.flush()
    user = User(
        username=username,
        email=f"{username}@test.com",
        full_name=username,
        hashed_password=get_password_hash("Test@123456"),
        is_active=True,
        is_superuser=False,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def _create_active_contract(contract_no_suffix: str, total_amount: float = 10000) -> Contract:
    db = _make_db()
    user = _create_user(f"conc_user_{contract_no_suffix}")
    customer = Customer(name=f"Test Customer {contract_no_suffix}", created_by=user.id)
    db.add(customer)
    db.commit()
    db.refresh(customer)

    from app.models.service_type import ServiceType as ServiceTypeModel

    st = db.query(ServiceTypeModel).filter(ServiceTypeModel.is_active == True).first()
    if not st:
        st = ServiceTypeModel(code="evaluation", name="安全评价", is_active=True)
        db.add(st)
        db.commit()
        db.refresh(st)

    contract = Contract(
        contract_no=f"CONC-{contract_no_suffix}",
        title="Concurrent Test Contract",
        customer_id=customer.id,
        service_type=st.id,
        total_amount=total_amount,
        status=ContractStatus.ACTIVE,
        created_by=user.id,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    db.close()
    return contract


def _cleanup_contract_and_related(contract_id: int):
    db = _make_db()
    db.query(Payment).filter(Payment.contract_id == contract_id).delete()
    db.query(Invoice).filter(Invoice.contract_id == contract_id).delete()
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        db.delete(contract)
    db.commit()
    db.close()


class TestConcurrentInvoice:
    def test_concurrent_invoice_audit_amount_not_exceeded(self):
        """
        并发审核发票场景：合同总额 10000，已有 ISSUED 发票 4000。
        两张 APPLYING 发票各 4000，两个线程同时审核通过。
        只有一个应该成功（变为 ISSUED），另一个触发 InvoiceAmountExceededError。
        """
        contract = _create_active_contract("inv", total_amount=10000)
        contract_id = contract.id

        db = _make_db()
        # 预先插入一张 ISSUED 发票
        issued = Invoice(
            invoice_no=f"INV-ISSUED-{contract_id}",
            contract_id=contract_id,
            invoice_type=InvoiceType.GENERAL,
            amount=4000,
            status="issued",
            applied_by=contract.created_by,
        )
        db.add(issued)
        # 创建两张 APPLYING 发票
        applying1 = Invoice(
            invoice_no=f"INV-APP1-{contract_id}",
            contract_id=contract_id,
            invoice_type=InvoiceType.GENERAL,
            amount=4000,
            status="applying",
            applied_by=contract.created_by,
        )
        applying2 = Invoice(
            invoice_no=f"INV-APP2-{contract_id}",
            contract_id=contract_id,
            invoice_type=InvoiceType.GENERAL,
            amount=4000,
            status="applying",
            applied_by=contract.created_by,
        )
        db.add(applying1)
        db.add(applying2)
        db.commit()
        invoice_ids = [applying1.id, applying2.id]
        db.close()

        results = {"success": 0, "errors": []}
        lock = threading.Lock()

        def _thread_audit(invoice_id: int):
            db = SessionLocal()
            try:
                invoice_service.audit_invoice(
                    db,
                    invoice_id=invoice_id,
                    body=InvoiceAuditRequest(
                        action="approve",
                        invoice_date=date.today(),
                        actual_invoice_no=f"NO-{invoice_id}",
                    ),
                )
                with lock:
                    results["success"] += 1
            except Exception as exc:
                with lock:
                    results["errors"].append(f"{type(exc).__name__}: {exc}")
            finally:
                db.close()

        t1 = threading.Thread(target=_thread_audit, args=(invoice_ids[0],))
        t2 = threading.Thread(target=_thread_audit, args=(invoice_ids[1],))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # 验证
        db = _make_db()
        total_invoiced = crud_invoice.get_sum_by_contract(db, contract_id=contract_id)
        db.close()

        _cleanup_contract_and_related(contract_id)

        assert (
            results["success"] == 1
        ), f"Expected 1 success, got {results['success']}, errors={results['errors']}"
        assert total_invoiced == Decimal("8000"), f"Expected 8000 invoiced, got {total_invoiced}"
        assert any(
            "InvoiceAmountExceededError" in e for e in results["errors"]
        ), f"Expected InvoiceAmountExceededError in errors, got {results['errors']}"


class TestConcurrentPayment:
    def test_concurrent_payment_amount_not_exceeded(self):
        """
        并取收款场景：两个线程同时尝试给同一合同收款，
        总金额 10000，各收 6000，预期只有一个成功，
        另一个触发 PaymentAmountExceededError。
        """
        contract = _create_active_contract("pay", total_amount=10000)
        contract_id = contract.id
        results = {"success": 0, "errors": []}
        lock = threading.Lock()

        def _thread_payment(thread_no: int):
            db = SessionLocal()
            try:
                payment_service.create_payment(
                    db,
                    obj_in=PaymentCreate(
                        payment_no=f"PAY-{contract_id}-{thread_no}",
                        contract_id=contract_id,
                        amount=Decimal("6000"),
                        payment_method=PaymentMethod.BANK_TRANSFER,
                        payment_date=date.today(),
                    ),
                    created_by=contract.created_by,
                )
                with lock:
                    results["success"] += 1
            except Exception as exc:
                with lock:
                    results["errors"].append(f"{type(exc).__name__}: {exc}")
            finally:
                db.close()

        t1 = threading.Thread(target=_thread_payment, args=(1,))
        t2 = threading.Thread(target=_thread_payment, args=(2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # 验证
        db = _make_db()
        total_received = crud_payment.get_sum_by_contract(db, contract_id=contract_id)
        db.close()

        _cleanup_contract_and_related(contract_id)

        assert (
            results["success"] == 1
        ), f"Expected 1 success, got {results['success']}, errors={results['errors']}"
        assert total_received == Decimal("6000"), f"Expected 6000 received, got {total_received}"
        assert any(
            "PaymentAmountExceededError" in e for e in results["errors"]
        ), f"Expected PaymentAmountExceededError in errors, got {results['errors']}"
