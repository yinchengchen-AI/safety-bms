from decimal import Decimal

import pytest

from app.services.contract_doc_service import number_to_chinese_upper


@pytest.mark.parametrize(
    "amount,expected",
    [
        (Decimal("0"), "零元整"),
        (Decimal("10"), "壹拾元整"),
        (Decimal("100000"), "壹拾万元整"),
        (Decimal("1004"), "壹仟零肆元整"),
        (Decimal("1010"), "壹仟零壹拾元整"),
        (Decimal("1234.56"), "壹仟贰佰叁拾肆元伍角陆分"),
        (Decimal("0.07"), "柒分"),
        (Decimal("0.50"), "伍角"),
        (Decimal("10.05"), "壹拾元零伍分"),
        (Decimal("100.05"), "壹佰元零伍分"),
        (Decimal("100000001"), "壹亿零壹元整"),
    ],
)
def test_number_to_chinese_upper(amount, expected):
    assert number_to_chinese_upper(amount) == expected
