import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base_all import Base  # noqa: F401
from app.db.session import SessionLocal
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.service import ServiceOrder
from app.models.user import DataScope, Role, User
from app.utils.data_scope import apply_data_scope, check_data_scope, resolve_data_scope


def _make_db() -> Session:
    return SessionLocal()


def _create_user(username: str, data_scope: DataScope, dept_id: int | None = None):
    db = _make_db()
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.close()
        return user
    role = Role(name=f"role_{username}", description="test", data_scope=data_scope)
    db.add(role)
    db.flush()
    user = User(
        username=username,
        email=f"{username}@test.com",
        full_name=username,
        hashed_password=get_password_hash("Test@123456"),
        is_active=True,
        is_superuser=False,
        department_id=dept_id,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def _create_customer(created_by: int, dept_id: int | None = None):
    db = _make_db()
    c = Customer(name="Test Customer", created_by=created_by)
    db.add(c)
    db.commit()
    db.refresh(c)
    db.close()
    return c


def _get_or_create_service_type_id() -> int:
    db = _make_db()
    from app.models.service_type import ServiceType as ServiceTypeModel

    st = db.query(ServiceTypeModel).filter(ServiceTypeModel.is_active == True).first()
    if st:
        db.close()
        return st.id
    st = ServiceTypeModel(code="evaluation", name="安全评价", is_active=True)
    db.add(st)
    db.commit()
    db.refresh(st)
    db.close()
    return st.id


def _create_contract(created_by: int, customer_id: int, total_amount: float = 10000):
    db = _make_db()
    from app.core.constants import ContractStatus

    c = Contract(
        contract_no=f"C-{created_by}-{customer_id}",
        title="Test Contract",
        customer_id=customer_id,
        service_type=_get_or_create_service_type_id(),
        total_amount=total_amount,
        status=ContractStatus.DRAFT,
        created_by=created_by,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    db.close()
    return c


def _create_service_order(contract_id: int, assignee_id: int | None = None):
    db = _make_db()
    from app.core.constants import ServiceOrderStatus

    o = ServiceOrder(
        order_no=f"S-{contract_id}",
        contract_id=contract_id,
        title="Test Order",
        service_type=_get_or_create_service_type_id(),
        status=ServiceOrderStatus.PENDING,
        assignee_id=assignee_id,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    db.close()
    return o


def _create_invoice(contract_id: int, applied_by: int, amount: float = 1000):
    db = _make_db()
    from app.core.constants import InvoiceType

    i = Invoice(
        invoice_no=f"I-{contract_id}",
        contract_id=contract_id,
        invoice_type=InvoiceType.GENERAL,
        amount=amount,
        applied_by=applied_by,
    )
    db.add(i)
    db.commit()
    db.refresh(i)
    db.close()
    return i


def _create_payment(contract_id: int, created_by: int, amount: float = 500):
    db = _make_db()
    from datetime import date

    from app.core.constants import PaymentMethod

    p = Payment(
        payment_no=f"P-{contract_id}",
        contract_id=contract_id,
        amount=amount,
        payment_method=PaymentMethod.BANK_TRANSFER,
        payment_date=date.today(),
        created_by=created_by,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    db.close()
    return p


class TestResolveDataScope:
    def test_superuser_returns_all(self):
        u = _create_user("ds_super", DataScope.SELF)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        user.is_superuser = True
        db.commit()
        assert resolve_data_scope(user) == DataScope.ALL
        db.close()

    def test_all_beats_dept_and_self(self):
        u = _create_user("ds_all", DataScope.ALL)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        assert resolve_data_scope(user) == DataScope.ALL
        db.close()

    def test_dept_beats_self(self):
        u = _create_user("ds_dept", DataScope.DEPT)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        assert resolve_data_scope(user) == DataScope.DEPT
        db.close()

    def test_defaults_to_self(self):
        u = _create_user("ds_self", DataScope.SELF)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        assert resolve_data_scope(user) == DataScope.SELF
        db.close()


class TestApplyDataScope:
    @pytest.mark.parametrize(
        "model_factory,query_model",
        [
            (lambda uid: _create_customer(uid), Customer),
            (lambda uid: _create_contract(uid, _create_customer(uid).id), Contract),
            (
                lambda uid: _create_service_order(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                ServiceOrder,
            ),
            (
                lambda uid: _create_invoice(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                Invoice,
            ),
            (
                lambda uid: _create_payment(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                Payment,
            ),
        ],
    )
    def test_all_scope_returns_all(self, model_factory, query_model):
        owner = _create_user("all_owner", DataScope.ALL)
        other = _create_user("all_other", DataScope.ALL)
        model_factory(owner.id)
        model_factory(other.id)
        db = _make_db()
        user = db.query(User).filter(User.id == owner.id).first()
        q = apply_data_scope(db.query(query_model), query_model, user)
        count = q.count()
        assert count >= 2
        db.close()

    @pytest.mark.parametrize(
        "model_factory,query_model,attr",
        [
            (lambda uid: _create_customer(uid), Customer, "created_by"),
            (lambda uid: _create_contract(uid, _create_customer(uid).id), Contract, "created_by"),
            (
                lambda uid: _create_service_order(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                ServiceOrder,
                "assignee_id",
            ),
            (
                lambda uid: _create_invoice(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                Invoice,
                "applied_by",
            ),
            (
                lambda uid: _create_payment(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                Payment,
                "created_by",
            ),
        ],
    )
    def test_self_scope_filters_to_user(self, model_factory, query_model, attr):
        owner = _create_user("self_owner", DataScope.SELF)
        other = _create_user("self_other", DataScope.SELF)
        model_factory(owner.id)
        model_factory(other.id)
        db = _make_db()
        user = db.query(User).filter(User.id == owner.id).first()
        q = apply_data_scope(db.query(query_model), query_model, user)
        results = q.all()
        for r in results:
            assert getattr(r, attr) == owner.id
        db.close()

    @pytest.mark.parametrize(
        "model_factory,query_model,attr",
        [
            (lambda uid: _create_customer(uid), Customer, "created_by"),
            (lambda uid: _create_contract(uid, _create_customer(uid).id), Contract, "created_by"),
            (
                lambda uid: _create_service_order(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                ServiceOrder,
                "assignee_id",
            ),
            (
                lambda uid: _create_invoice(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                Invoice,
                "applied_by",
            ),
            (
                lambda uid: _create_payment(
                    _create_contract(uid, _create_customer(uid).id).id, uid
                ),
                Payment,
                "created_by",
            ),
        ],
    )
    def test_dept_scope_without_department_falls_back_to_self(
        self, model_factory, query_model, attr
    ):
        owner = _create_user("dept_nofallback", DataScope.DEPT)
        other = _create_user("dept_nofallback_other", DataScope.DEPT)
        model_factory(owner.id)
        model_factory(other.id)
        db = _make_db()
        user = db.query(User).filter(User.id == owner.id).first()
        q = apply_data_scope(db.query(query_model), query_model, user)
        results = q.all()
        for r in results:
            assert getattr(r, attr) == owner.id
        db.close()


class TestCheckDataScope:
    def test_all_allows_any_object(self):
        u = _create_user("chk_all", DataScope.ALL)
        c = _create_customer(u.id)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        assert check_data_scope(c, user) is True
        db.close()

    def test_self_allows_own_record(self):
        u = _create_user("chk_self", DataScope.SELF)
        c = _create_customer(u.id)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        assert check_data_scope(c, user) is True
        db.close()

    def test_self_blocks_others_record(self):
        u = _create_user("chk_self2", DataScope.SELF)
        other = _create_user("chk_other", DataScope.SELF)
        c = _create_customer(other.id)
        db = _make_db()
        user = db.query(User).filter(User.id == u.id).first()
        assert check_data_scope(c, user) is False
        db.close()
