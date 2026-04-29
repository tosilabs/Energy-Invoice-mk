"""Shared test fixtures for Energy Invoice MK tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from homeassistant.core import HomeAssistant

from custom_components.energy_invoice_mk.const import (
    CONF_BILLING_DAY,
    CONF_CONSUMER_ADDRESS,
    CONF_CONSUMER_NAME,
    CONF_METER_NUMBER,
    CONF_MUNICIPAL_TAX,
    CONF_NETWORK_ACCESS,
    CONF_NT_RATE,
    CONF_NT_SENSOR,
    CONF_TD_RATE,
    CONF_VAT_PERCENT,
    CONF_VT_BLOCK1_RATE,
    CONF_VT_BLOCK2_RATE,
    CONF_VT_BLOCK3_RATE,
    CONF_VT_BLOCK4_RATE,
    CONF_VT_SENSOR,
    DEFAULT_BILLING_DAY,
    DEFAULT_MUNICIPAL_TAX,
    DEFAULT_NETWORK_ACCESS,
    DEFAULT_NT_RATE,
    DEFAULT_TD_RATE,
    DEFAULT_VAT_PERCENT,
    DEFAULT_VT_BLOCK1_RATE,
    DEFAULT_VT_BLOCK2_RATE,
    DEFAULT_VT_BLOCK3_RATE,
    DEFAULT_VT_BLOCK4_RATE,
    DOMAIN,
)

MOCK_VT_ENTITY = "sensor.vt_energy_meter"
MOCK_NT_ENTITY = "sensor.nt_energy_meter"


@pytest.fixture
def mock_config_entry_data():
    return {
        CONF_CONSUMER_NAME: "Test Consumer",
        CONF_CONSUMER_ADDRESS: "Test Address, Skopje",
        CONF_METER_NUMBER: "MK-12345",
        CONF_VT_SENSOR: MOCK_VT_ENTITY,
        CONF_NT_SENSOR: MOCK_NT_ENTITY,
        CONF_VT_BLOCK1_RATE: DEFAULT_VT_BLOCK1_RATE,
        CONF_VT_BLOCK2_RATE: DEFAULT_VT_BLOCK2_RATE,
        CONF_VT_BLOCK3_RATE: DEFAULT_VT_BLOCK3_RATE,
        CONF_VT_BLOCK4_RATE: DEFAULT_VT_BLOCK4_RATE,
        CONF_NT_RATE: DEFAULT_NT_RATE,
        CONF_TD_RATE: DEFAULT_TD_RATE,
        CONF_NETWORK_ACCESS: DEFAULT_NETWORK_ACCESS,
        CONF_VAT_PERCENT: DEFAULT_VAT_PERCENT,
        CONF_MUNICIPAL_TAX: DEFAULT_MUNICIPAL_TAX,
        CONF_BILLING_DAY: DEFAULT_BILLING_DAY,
    }


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.async_add_executor_job = AsyncMock()
    hass.config = MagicMock()
    hass.config.path = lambda *args: "/tmp/" + "/".join(args)
    return hass
