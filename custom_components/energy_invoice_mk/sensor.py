"""Sensor entities for Energy Invoice MK - EVN Macedonia."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CONSUMER_NAME,
    DATA_DAILY_AVERAGE_COST,
    DATA_DAYS_IN_PERIOD,
    DATA_ENERGY_COST,
    DATA_ESTIMATED_MONTHLY,
    DATA_LAST_30_DAYS_CONSUMPTION,
    DATA_LAST_30_DAYS_COST,
    DATA_MUNICIPAL_TAX,
    DATA_NETWORK_ACCESS,
    DATA_NT_CONSUMPTION,
    DATA_NT_COST,
    DATA_PERIOD_START,
    DATA_PREVIOUS_MONTH_CONSUMPTION,
    DATA_PREVIOUS_MONTH_COST,
    DATA_PREVIOUS_PERIOD_CONSUMPTION,
    DATA_PREVIOUS_PERIOD_COST,
    DATA_SUBTOTAL,
    DATA_TD_COST,
    DATA_THIS_YEAR_CONSUMPTION,
    DATA_THIS_YEAR_COST,
    DATA_TOTAL_CONSUMPTION,
    DATA_TOTAL_COST,
    DATA_TOTAL_WITH_VAT,
    DATA_VAT_AMOUNT,
    DATA_VT_BLOCK1_COST,
    DATA_VT_BLOCK1_KWH,
    DATA_VT_BLOCK2_COST,
    DATA_VT_BLOCK2_KWH,
    DATA_VT_BLOCK3_COST,
    DATA_VT_BLOCK3_KWH,
    DATA_VT_BLOCK4_COST,
    DATA_VT_BLOCK4_KWH,
    DATA_VT_CONSUMPTION,
    DATA_VT_COST,
    DOMAIN,
)
from .coordinator import EnergyInvoiceCoordinator

UNIT_MKD = "MKD"


@dataclass(frozen=True)
class EnergyInvoiceSensorDescription(SensorEntityDescription):
    data_key: str = ""


SENSOR_DESCRIPTIONS: tuple[EnergyInvoiceSensorDescription, ...] = (
    EnergyInvoiceSensorDescription(
        key="vt_consumption",
        data_key=DATA_VT_CONSUMPTION,
        name="VT Consumption (current period)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
    ),
    EnergyInvoiceSensorDescription(
        key="nt_consumption",
        data_key=DATA_NT_CONSUMPTION,
        name="NT Consumption (current period)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt-outline",
    ),
    EnergyInvoiceSensorDescription(
        key="total_consumption",
        data_key=DATA_TOTAL_CONSUMPTION,
        name="Total Consumption (current period)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:counter",
    ),
    EnergyInvoiceSensorDescription(
        key="vt_cost",
        data_key=DATA_VT_COST,
        name="VT Energy Cost",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash",
    ),
    EnergyInvoiceSensorDescription(
        key="nt_cost",
        data_key=DATA_NT_COST,
        name="NT Energy Cost",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-minus",
    ),
    EnergyInvoiceSensorDescription(
        key="energy_cost",
        data_key=DATA_ENERGY_COST,
        name="Energy Cost (VT+NT)",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash-multiple",
    ),
    EnergyInvoiceSensorDescription(
        key="td_cost",
        data_key=DATA_TD_COST,
        name="Transmission & Distribution Cost",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    EnergyInvoiceSensorDescription(
        key="vat_amount",
        data_key=DATA_VAT_AMOUNT,
        name="VAT (DDV 18%)",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
    ),
    EnergyInvoiceSensorDescription(
        key="total_cost",
        data_key=DATA_TOTAL_COST,
        name="Total Bill (current period)",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:receipt-text",
    ),
    EnergyInvoiceSensorDescription(
        key="daily_average_cost",
        data_key=DATA_DAILY_AVERAGE_COST,
        name="Daily Average Cost",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-today",
    ),
    EnergyInvoiceSensorDescription(
        key="estimated_monthly",
        data_key=DATA_ESTIMATED_MONTHLY,
        name="Estimated Monthly Bill",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line",
    ),
    EnergyInvoiceSensorDescription(
        key="previous_month_cost",
        data_key=DATA_PREVIOUS_MONTH_COST,
        name="Previous Month Bill",
        native_unit_of_measurement=UNIT_MKD,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:receipt-text-clock",
    ),
    EnergyInvoiceSensorDescription(
        key="previous_month_consumption",
        data_key=DATA_PREVIOUS_MONTH_CONSUMPTION,
        name="Previous Month Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:history",
    ),
    EnergyInvoiceSensorDescription(
        key="last_30_days_consumption",
        data_key=DATA_LAST_30_DAYS_CONSUMPTION,
        name="Last 30 Days Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:calendar-month",
    ),
    EnergyInvoiceSensorDescription(
        key="last_30_days_cost",
        data_key=DATA_LAST_30_DAYS_COST,
        name="Last 30 Days Cost",
        native_unit_of_measurement="MKD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-clock",
    ),
    EnergyInvoiceSensorDescription(
        key="previous_period_consumption",
        data_key=DATA_PREVIOUS_PERIOD_CONSUMPTION,
        name="Previous Billing Period Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:history",
    ),
    EnergyInvoiceSensorDescription(
        key="previous_period_cost",
        data_key=DATA_PREVIOUS_PERIOD_COST,
        name="Previous Billing Period Cost",
        native_unit_of_measurement="MKD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:receipt-text-clock",
    ),
    EnergyInvoiceSensorDescription(
        key="this_year_consumption",
        data_key=DATA_THIS_YEAR_CONSUMPTION,
        name="This Year Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:calendar-year",
    ),
    EnergyInvoiceSensorDescription(
        key="this_year_cost",
        data_key=DATA_THIS_YEAR_COST,
        name="This Year Cost",
        native_unit_of_measurement="MKD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-multiple",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EnergyInvoiceCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EnergyInvoiceSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EnergyInvoiceSensor(CoordinatorEntity[EnergyInvoiceCoordinator], RestoreSensor):
    """A sensor that displays one field from the EVN bill calculation."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: EnergyInvoiceCoordinator,
        entry: ConfigEntry,
        description: EnergyInvoiceSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._data_key = description.data_key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        consumer_name = entry.data.get(CONF_CONSUMER_NAME, "EVN Meter")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=consumer_name,
            manufacturer="EVN Macedonia",
            model="Energy Invoice MK",
            entry_type="service",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = last.native_value

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        if not data:
            return {}

        # Rich attributes on the total_cost sensor (for Lovelace cards and automations)
        if self._data_key == DATA_TOTAL_COST:
            return {
                "period_start": data.get(DATA_PERIOD_START),
                "days_in_period": data.get(DATA_DAYS_IN_PERIOD),
                "vt_kwh": data.get(DATA_VT_CONSUMPTION),
                "nt_kwh": data.get(DATA_NT_CONSUMPTION),
                # Diagnostic — use Developer Tools → States to verify sensor is read correctly
                "diag_peak_entity": data.get("_diag_peak_entity"),
                "diag_offpeak_entity": data.get("_diag_offpeak_entity"),
                "diag_current_peak_kwh": data.get("_diag_current_peak_kwh"),
                "diag_snapshot_peak_kwh": data.get("_diag_snapshot_peak_kwh"),
                "diag_current_offpeak_kwh": data.get("_diag_current_offpeak_kwh"),
                "diag_snapshot_offpeak_kwh": data.get("_diag_snapshot_offpeak_kwh"),
                "diag_sensor_available": data.get("_diag_sensor_available"),
                "vt_block1_kwh": data.get(DATA_VT_BLOCK1_KWH),
                "vt_block2_kwh": data.get(DATA_VT_BLOCK2_KWH),
                "vt_block3_kwh": data.get(DATA_VT_BLOCK3_KWH),
                "vt_block4_kwh": data.get(DATA_VT_BLOCK4_KWH),
                "vt_block1_cost_mkd": data.get(DATA_VT_BLOCK1_COST),
                "vt_block2_cost_mkd": data.get(DATA_VT_BLOCK2_COST),
                "vt_block3_cost_mkd": data.get(DATA_VT_BLOCK3_COST),
                "vt_block4_cost_mkd": data.get(DATA_VT_BLOCK4_COST),
                "vt_cost_mkd": data.get(DATA_VT_COST),
                "nt_cost_mkd": data.get(DATA_NT_COST),
                "energy_cost_mkd": data.get(DATA_ENERGY_COST),
                "td_cost_mkd": data.get(DATA_TD_COST),
                "network_access_mkd": data.get(DATA_NETWORK_ACCESS),
                "subtotal_before_vat_mkd": data.get(DATA_SUBTOTAL),
                "vat_18pct_mkd": data.get(DATA_VAT_AMOUNT),
                "total_with_vat_mkd": data.get(DATA_TOTAL_WITH_VAT),
                "municipal_tax_mkd": data.get(DATA_MUNICIPAL_TAX),
                "vt_rate_block1": data.get("vt_block1_rate"),
                "vt_rate_block2": data.get("vt_block2_rate"),
                "vt_rate_block3": data.get("vt_block3_rate"),
                "vt_rate_block4": data.get("vt_block4_rate"),
                "nt_rate": data.get("nt_rate"),
                "td_rate": data.get("td_rate"),
                "vat_percent": data.get("vat_percent"),
            }

        if self._data_key == DATA_ESTIMATED_MONTHLY:
            return {
                "based_on_days": data.get(DATA_DAYS_IN_PERIOD),
                "period_start": data.get(DATA_PERIOD_START),
                "daily_average_mkd": data.get(DATA_DAILY_AVERAGE_COST),
            }

        return {}
