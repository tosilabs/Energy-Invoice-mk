"""Tests for sensor entity definitions."""
from __future__ import annotations

import pytest

from custom_components.energy_invoice_mk.sensor import SENSOR_DESCRIPTIONS
from custom_components.energy_invoice_mk.const import (
    DATA_VT_CONSUMPTION,
    DATA_NT_CONSUMPTION,
    DATA_TOTAL_CONSUMPTION,
    DATA_TOTAL_COST,
    DATA_ESTIMATED_MONTHLY,
)


class TestSensorDescriptions:
    def test_all_sensors_have_unique_keys(self):
        keys = [d.key for d in SENSOR_DESCRIPTIONS]
        assert len(keys) == len(set(keys)), "Duplicate sensor keys found"

    def test_all_sensors_have_data_key(self):
        for desc in SENSOR_DESCRIPTIONS:
            assert desc.data_key, f"Sensor {desc.key} has no data_key"

    def test_kwh_sensors_have_energy_device_class(self):
        from homeassistant.components.sensor import SensorDeviceClass
        from homeassistant.const import UnitOfEnergy

        kwh_sensors = [
            DATA_VT_CONSUMPTION,
            DATA_NT_CONSUMPTION,
            DATA_TOTAL_CONSUMPTION,
        ]
        for desc in SENSOR_DESCRIPTIONS:
            if desc.data_key in kwh_sensors:
                assert desc.device_class == SensorDeviceClass.ENERGY
                assert desc.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR

    def test_cost_sensors_have_monetary_device_class(self):
        from homeassistant.components.sensor import SensorDeviceClass

        cost_sensors = [DATA_TOTAL_COST, DATA_ESTIMATED_MONTHLY]
        for desc in SENSOR_DESCRIPTIONS:
            if desc.data_key in cost_sensors:
                assert desc.device_class == SensorDeviceClass.MONETARY
                assert desc.native_unit_of_measurement == "MKD"

    def test_sensor_count(self):
        assert len(SENSOR_DESCRIPTIONS) == 13
