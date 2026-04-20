from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.constants import ContractStatus
from app.core.exceptions import ContractStatusError
from app.crud.contract import ALLOWED_TRANSITIONS, crud_contract
from app.models.contract import Contract, ContractAttachment
from app.models.customer import Customer
from app.models.service_type import ServiceType


def _seed_customer_and_service_type(db_session):
    suffix = uuid4().hex[:8]
    customer = Customer(name=f"合同重写客户-{suffix}")
    service_type = ServiceType(code=f"rewrite-{suffix}", name="合同重写服务", is_active=True)
    db_session.add_all([customer, service_type])
    db_session.flush()
    return customer, service_type


def _unique_contract_no(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _create_contract(
    db_session, *, contract_no: str, status: ContractStatus = ContractStatus.DRAFT
):
    customer, service_type = _seed_customer_and_service_type(db_session)
    contract = Contract(
        contract_no=contract_no,
        title="合同重写测试合同",
        customer_id=customer.id,
        service_type=service_type.id,
        total_amount=Decimal("1000.00"),
        sign_date=date(2026, 4, 20),
        status=status,
    )
    db_session.add(contract)
    db_session.flush()
    return contract


def test_allowed_contract_transitions_collapsed():
    assert ALLOWED_TRANSITIONS[ContractStatus.DRAFT] == {
        ContractStatus.SIGNED,
        ContractStatus.TERMINATED,
    }
    assert ALLOWED_TRANSITIONS[ContractStatus.SIGNED] == {
        ContractStatus.EXECUTING,
        ContractStatus.TERMINATED,
    }


def test_cannot_mark_signed_without_signed_attachment(db_session):
    contract = _create_contract(db_session, contract_no=_unique_contract_no("HT202604200001"))
    db_session.commit()

    with pytest.raises(ContractStatusError, match="请先上传已签合同附件"):
        crud_contract.update_status(
            db_session,
            db_obj=contract,
            new_status=ContractStatus.SIGNED,
            changed_by=1,
        )


def test_can_mark_signed_with_signed_attachment(db_session):
    contract = _create_contract(db_session, contract_no=_unique_contract_no("HT202604200002"))
    db_session.add(
        ContractAttachment(
            contract_id=contract.id,
            file_name="signed-contract.pdf",
            file_url="contracts/signed-contract.pdf",
            file_type="signed",
            uploaded_by=1,
        )
    )
    db_session.commit()

    updated = crud_contract.update_status(
        db_session,
        db_obj=contract,
        new_status=ContractStatus.SIGNED,
        changed_by=1,
    )

    assert updated.status == ContractStatus.SIGNED
    assert updated.attachments[-1].file_type == "signed"


def test_latest_draft_and_signed_attachment_are_separated(db_session):
    contract = _create_contract(db_session, contract_no=_unique_contract_no("HT202604200003"))
    db_session.add_all(
        [
            ContractAttachment(
                contract_id=contract.id,
                file_name="draft.docx",
                file_url="contracts/draft.docx",
                file_type="draft",
                uploaded_by=1,
            ),
            ContractAttachment(
                contract_id=contract.id,
                file_name="signed.pdf",
                file_url="contracts/signed.pdf",
                file_type="signed",
                uploaded_by=1,
            ),
        ]
    )
    db_session.commit()

    db_session.refresh(contract)

    assert [attachment.file_type for attachment in contract.attachments] == ["draft", "signed"]
