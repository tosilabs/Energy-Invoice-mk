"""Tests for PDF invoice generation."""
from __future__ import annotations

import os
import tempfile
import pytest

from custom_components.energy_invoice_mk.coordinator import calculate_evn_bill
from custom_components.energy_invoice_mk.const import (
    CONF_CONSUMER_NAME,
    CONF_CONSUMER_ADDRESS,
    CONF_METER_NUMBER,
    CONF_VT_BLOCK1_RATE,
    CONF_VT_BLOCK2_RATE,
    CONF_VT_BLOCK3_RATE,
    CONF_VT_BLOCK4_RATE,
    CONF_NT_RATE,
    CONF_TD_RATE,
    CONF_VAT_PERCENT,
    CONF_NETWORK_ACCESS,
    CONF_MUNICIPAL_TAX,
    DEFAULT_VT_BLOCK1_RATE,
    DEFAULT_VT_BLOCK2_RATE,
    DEFAULT_VT_BLOCK3_RATE,
    DEFAULT_VT_BLOCK4_RATE,
    DEFAULT_NT_RATE,
    DEFAULT_TD_RATE,
    DEFAULT_VAT_PERCENT,
    DEFAULT_NETWORK_ACCESS,
    DEFAULT_MUNICIPAL_TAX,
    DATA_PERIOD_START,
    DATA_DAYS_IN_PERIOD,
)


@pytest.fixture
def sample_bill_data():
    data = calculate_evn_bill(vt_kwh=210.0, nt_kwh=250.0)
    data[DATA_PERIOD_START] = "2026-04-01"
    data[DATA_DAYS_IN_PERIOD] = 30
    return data


@pytest.fixture
def sample_cfg():
    return {
        CONF_CONSUMER_NAME: "Test Consumer",
        CONF_CONSUMER_ADDRESS: "Ул. Македонија 1, Скопје",
        CONF_METER_NUMBER: "MK-99999",
        CONF_VT_BLOCK1_RATE: DEFAULT_VT_BLOCK1_RATE,
        CONF_VT_BLOCK2_RATE: DEFAULT_VT_BLOCK2_RATE,
        CONF_VT_BLOCK3_RATE: DEFAULT_VT_BLOCK3_RATE,
        CONF_VT_BLOCK4_RATE: DEFAULT_VT_BLOCK4_RATE,
        CONF_NT_RATE: DEFAULT_NT_RATE,
        CONF_TD_RATE: DEFAULT_TD_RATE,
        CONF_VAT_PERCENT: DEFAULT_VAT_PERCENT,
        CONF_NETWORK_ACCESS: DEFAULT_NETWORK_ACCESS,
        CONF_MUNICIPAL_TAX: DEFAULT_MUNICIPAL_TAX,
    }


class TestInvoiceGeneration:
    def test_pdf_file_is_created(self, sample_bill_data, sample_cfg):
        """PDF file must be created and have non-zero size."""
        try:
            from custom_components.energy_invoice_mk.invoice import generate_pdf_invoice
        except ImportError:
            pytest.skip("reportlab not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_invoice.pdf")
            generate_pdf_invoice(filepath, sample_bill_data, sample_cfg, month=4, year=2026)
            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 1000, "PDF is unexpectedly small"

    def test_pdf_starts_with_pdf_header(self, sample_bill_data, sample_cfg):
        """Generated file must be a valid PDF (starts with %PDF)."""
        try:
            from custom_components.energy_invoice_mk.invoice import generate_pdf_invoice
        except ImportError:
            pytest.skip("reportlab not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_invoice.pdf")
            generate_pdf_invoice(filepath, sample_bill_data, sample_cfg, month=4, year=2026)
            with open(filepath, "rb") as f:
                header = f.read(4)
            assert header == b"%PDF", f"File does not start with %PDF header, got {header!r}"

    def test_zero_consumption_invoice(self, sample_cfg):
        """Invoice must be generated even with zero consumption."""
        try:
            from custom_components.energy_invoice_mk.invoice import generate_pdf_invoice
        except ImportError:
            pytest.skip("reportlab not installed")

        data = calculate_evn_bill(vt_kwh=0.0, nt_kwh=0.0)
        data[DATA_PERIOD_START] = "2026-04-01"
        data[DATA_DAYS_IN_PERIOD] = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "zero_invoice.pdf")
            generate_pdf_invoice(filepath, data, sample_cfg, month=4, year=2026)
            assert os.path.exists(filepath)
