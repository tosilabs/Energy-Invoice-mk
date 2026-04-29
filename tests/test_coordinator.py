"""Tests for the EVN bill calculation logic in the coordinator."""
from __future__ import annotations

import pytest

from custom_components.energy_invoice_mk.coordinator import calculate_evn_bill
from custom_components.energy_invoice_mk.const import (
    DATA_ENERGY_COST,
    DATA_MUNICIPAL_TAX,
    DATA_NETWORK_ACCESS,
    DATA_NT_CONSUMPTION,
    DATA_NT_COST,
    DATA_SUBTOTAL,
    DATA_TD_COST,
    DATA_TOTAL_CONSUMPTION,
    DATA_TOTAL_COST,
    DATA_TOTAL_WITH_VAT,
    DATA_VAT_AMOUNT,
    DATA_VT_BLOCK1_COST,
    DATA_VT_BLOCK1_KWH,
    DATA_VT_BLOCK2_COST,
    DATA_VT_BLOCK2_KWH,
    DATA_VT_BLOCK3_KWH,
    DATA_VT_BLOCK4_KWH,
    DATA_VT_CONSUMPTION,
    DATA_VT_COST,
    DEFAULT_MUNICIPAL_TAX,
    DEFAULT_NETWORK_ACCESS,
    DEFAULT_NT_RATE,
    DEFAULT_TD_RATE,
    DEFAULT_VAT_PERCENT,
    DEFAULT_VT_BLOCK1_RATE,
    DEFAULT_VT_BLOCK2_RATE,
    DEFAULT_VT_BLOCK3_RATE,
    DEFAULT_VT_BLOCK4_RATE,
)


class TestCalculateEvnBill:
    """Tests for calculate_evn_bill using ERC reference example."""

    def test_reference_example_from_erc_calculator(self):
        """
        Verify against the official ERC calculator example:
          VT = 210 kWh, NT = 250 kWh
          Expected total = 3,337 MKD
        """
        result = calculate_evn_bill(vt_kwh=210.0, nt_kwh=250.0)

        assert result[DATA_VT_CONSUMPTION] == 210.0
        assert result[DATA_NT_CONSUMPTION] == 250.0
        assert result[DATA_TOTAL_CONSUMPTION] == 460.0

        # VT: 210 kWh fully in block 1 → 210 × 4.7074 = 988.55 ≈ 989
        assert result[DATA_VT_BLOCK1_KWH] == 210.0
        assert result[DATA_VT_BLOCK2_KWH] == 0.0
        assert abs(result[DATA_VT_BLOCK1_COST] - 988.55) < 1.0
        assert result[DATA_VT_COST] == pytest.approx(989.0, abs=1.0)

        # NT: 250 × 2.1893 = 547.33 ≈ 547
        assert result[DATA_NT_COST] == pytest.approx(547.0, abs=1.0)

        # Energy subtotal: 989 + 547 = 1,536
        assert result[DATA_ENERGY_COST] == pytest.approx(1536.0, abs=2.0)

        # T&D: 460 × 2.0339 = 935.59 ≈ 936, plus 200 fixed → 1,136
        assert result[DATA_TD_COST] == pytest.approx(936.0, abs=2.0)
        assert result[DATA_NETWORK_ACCESS] == 200.0

        # Subtotal (before VAT): 1,536 + 936 + 200 = 2,672
        assert result[DATA_SUBTOTAL] == pytest.approx(2672.0, abs=3.0)

        # VAT 18%: 2,672 × 0.18 = 480.96 ≈ 481
        assert result[DATA_VAT_AMOUNT] == pytest.approx(481.0, abs=2.0)

        # Total with VAT: 2,672 + 481 = 3,153
        assert result[DATA_TOTAL_WITH_VAT] == pytest.approx(3153.0, abs=3.0)

        # Municipal tax outside VAT: 184
        assert result[DATA_MUNICIPAL_TAX] == 184.0

        # Grand total: 3,153 + 184 = 3,337
        assert result[DATA_TOTAL_COST] == pytest.approx(3337.0, abs=4.0)

    def test_vat_is_18_percent(self):
        """VAT must be 18%, not 5%."""
        result = calculate_evn_bill(vt_kwh=100.0, nt_kwh=0.0)
        vat = result[DATA_VAT_AMOUNT]
        subtotal = result[DATA_SUBTOTAL]
        assert abs(vat / subtotal - 0.18) < 0.001

    def test_municipal_tax_outside_vat(self):
        """Municipal tax must be added after VAT, not included in VAT base."""
        result = calculate_evn_bill(vt_kwh=100.0, nt_kwh=0.0)
        assert result[DATA_TOTAL_COST] == pytest.approx(
            result[DATA_TOTAL_WITH_VAT] + result[DATA_MUNICIPAL_TAX], abs=0.01
        )

    def test_vt_block1_only(self):
        """200 kWh VT falls entirely in block 1."""
        result = calculate_evn_bill(vt_kwh=200.0, nt_kwh=0.0)
        assert result[DATA_VT_BLOCK1_KWH] == 200.0
        assert result[DATA_VT_BLOCK2_KWH] == 0.0
        assert result[DATA_VT_COST] == pytest.approx(200.0 * DEFAULT_VT_BLOCK1_RATE, abs=0.01)

    def test_vt_spans_block1_and_block2(self):
        """400 kWh VT: 210 in block 1, 190 in block 2."""
        result = calculate_evn_bill(vt_kwh=400.0, nt_kwh=0.0)
        assert result[DATA_VT_BLOCK1_KWH] == 210.0
        assert result[DATA_VT_BLOCK2_KWH] == 190.0
        assert result[DATA_VT_BLOCK3_KWH] == 0.0
        expected = 210.0 * DEFAULT_VT_BLOCK1_RATE + 190.0 * DEFAULT_VT_BLOCK2_RATE
        assert result[DATA_VT_COST] == pytest.approx(expected, abs=0.01)

    def test_vt_spans_all_four_blocks(self):
        """1100 kWh VT spans all 4 blocks."""
        result = calculate_evn_bill(vt_kwh=1100.0, nt_kwh=0.0)
        assert result[DATA_VT_BLOCK1_KWH] == 210.0
        assert result[DATA_VT_BLOCK2_KWH] == 420.0   # 630 - 210
        assert result[DATA_VT_BLOCK3_KWH] == 420.0   # 1050 - 630
        assert result[DATA_VT_BLOCK4_KWH] == 50.0    # 1100 - 1050
        expected = (
            210 * DEFAULT_VT_BLOCK1_RATE
            + 420 * DEFAULT_VT_BLOCK2_RATE
            + 420 * DEFAULT_VT_BLOCK3_RATE
            + 50 * DEFAULT_VT_BLOCK4_RATE
        )
        assert result[DATA_VT_COST] == pytest.approx(expected, abs=0.01)

    def test_zero_consumption(self):
        """Zero kWh still produces fixed charges (network + municipal)."""
        result = calculate_evn_bill(vt_kwh=0.0, nt_kwh=0.0)
        assert result[DATA_VT_COST] == 0.0
        assert result[DATA_NT_COST] == 0.0
        assert result[DATA_TD_COST] == 0.0
        assert result[DATA_NETWORK_ACCESS] == DEFAULT_NETWORK_ACCESS
        # Subtotal = 0 + 0 + 200 = 200, VAT = 36, total+VAT = 236, +184 municipal = 420
        assert result[DATA_SUBTOTAL] == pytest.approx(200.0, abs=0.01)
        assert result[DATA_TOTAL_COST] == pytest.approx(200.0 * 1.18 + 184.0, abs=0.5)

    def test_single_tariff_nt_zero(self):
        """Single-tariff meter: NT = 0 should not affect calculation."""
        result = calculate_evn_bill(vt_kwh=300.0, nt_kwh=0.0)
        assert result[DATA_NT_CONSUMPTION] == 0.0
        assert result[DATA_NT_COST] == 0.0
        assert result[DATA_TOTAL_CONSUMPTION] == 300.0

    def test_td_applied_on_total_kwh(self):
        """T&D fee must be applied on VT+NT combined, not separately."""
        vt, nt = 100.0, 100.0
        result = calculate_evn_bill(vt_kwh=vt, nt_kwh=nt)
        expected_td = (vt + nt) * DEFAULT_TD_RATE
        assert result[DATA_TD_COST] == pytest.approx(expected_td, abs=0.01)

    def test_custom_rates(self):
        """Custom rate override is respected."""
        result = calculate_evn_bill(
            vt_kwh=100.0,
            nt_kwh=0.0,
            vt_block1_rate=10.0,
            nt_rate=5.0,
            td_rate=3.0,
            network_access=300.0,
            vat_percent=20.0,
            municipal_tax=200.0,
        )
        vt_cost = 100.0 * 10.0
        td_cost = 100.0 * 3.0
        subtotal = vt_cost + td_cost + 300.0
        vat = subtotal * 0.20
        expected_total = subtotal + vat + 200.0
        assert result[DATA_TOTAL_COST] == pytest.approx(expected_total, abs=0.01)
