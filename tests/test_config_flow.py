"""Tests for config flow validation logic."""
from __future__ import annotations

import pytest

from custom_components.energy_invoice_mk.const import (
    DEFAULT_VT_BLOCK1_RATE,
    DEFAULT_VT_BLOCK2_RATE,
    DEFAULT_VT_BLOCK3_RATE,
    DEFAULT_VT_BLOCK4_RATE,
    DEFAULT_NT_RATE,
    DEFAULT_TD_RATE,
    DEFAULT_VAT_PERCENT,
    DEFAULT_NETWORK_ACCESS,
    DEFAULT_MUNICIPAL_TAX,
    DEFAULT_BILLING_DAY,
)


class TestDefaultRates:
    """Verify that default tariff constants match the ERC reference values."""

    def test_vt_block1_rate(self):
        assert DEFAULT_VT_BLOCK1_RATE == pytest.approx(4.7074)

    def test_vt_block2_rate(self):
        assert DEFAULT_VT_BLOCK2_RATE == pytest.approx(5.8976)

    def test_vt_block3_rate(self):
        assert DEFAULT_VT_BLOCK3_RATE == pytest.approx(7.8537)

    def test_vt_block4_rate(self):
        assert DEFAULT_VT_BLOCK4_RATE == pytest.approx(19.1904)

    def test_nt_rate(self):
        assert DEFAULT_NT_RATE == pytest.approx(2.1893)

    def test_td_rate(self):
        assert DEFAULT_TD_RATE == pytest.approx(2.0339)

    def test_vat_is_18_percent(self):
        """Critical: VAT must be 18%, not 5%."""
        assert DEFAULT_VAT_PERCENT == 18.0

    def test_network_access_fee(self):
        assert DEFAULT_NETWORK_ACCESS == 200.0

    def test_municipal_tax(self):
        assert DEFAULT_MUNICIPAL_TAX == 184.0

    def test_default_billing_day(self):
        assert DEFAULT_BILLING_DAY == 1
