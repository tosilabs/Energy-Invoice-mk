"""Config flow for Energy Invoice MK - EVN Macedonia."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CONSUMER_ADDRESS,
    CONF_CONSUMER_NAME,
    CONF_METER_NUMBER,
    CONF_MUNICIPAL_TAX,
    CONF_NETWORK_ACCESS,
    CONF_NOTIFY_ON_PERIOD_END,
    CONF_NOTIFY_SERVICE,
    CONF_NT_RATE,
    CONF_OFFPEAK_ENTITY,
    CONF_PEAK_ENTITY,
    CONF_PERIOD_START_DATE,
    CONF_SNAPSHOT_OFFPEAK,
    CONF_SNAPSHOT_PEAK,
    CONF_TD_RATE,
    CONF_VAT_PERCENT,
    CONF_VT_BLOCK1_RATE,
    CONF_VT_BLOCK2_RATE,
    CONF_VT_BLOCK3_RATE,
    CONF_VT_BLOCK4_RATE,
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


def _energy_sensor_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )


def _number(min_val: float, max_val: float, step: float | str = "any") -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_val,
            max=max_val,
            step=step,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _read_sensor_float(hass, entity_id: str | None) -> float | None:
    if not entity_id:
        return None
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unavailable", "unknown", ""):
        return None
    try:
        return float(state.state)
    except (ValueError, TypeError):
        return None


class EnergyInvoiceMKConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Energy Invoice MK."""

    VERSION = 2

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1: Consumer info."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONSUMER_NAME): str,
                    vol.Required(CONF_CONSUMER_ADDRESS): str,
                    vol.Optional(CONF_METER_NUMBER, default=""): str,
                }
            ),
        )

    async def async_step_sensors(self, user_input=None):
        """Step 2: Select peak (VT) and off-peak (NT) accumulative energy sensors."""
        errors: dict = {}
        if user_input is not None:
            peak = user_input.get(CONF_PEAK_ENTITY) or None
            offpeak = user_input.get(CONF_OFFPEAK_ENTITY) or None
            if peak or offpeak:
                self._data[CONF_PEAK_ENTITY] = peak
                self._data[CONF_OFFPEAK_ENTITY] = offpeak
                return await self.async_step_tariffs()
            errors["base"] = "no_sensor_selected"

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_PEAK_ENTITY): _energy_sensor_selector(),
                    vol.Optional(CONF_OFFPEAK_ENTITY): _energy_sensor_selector(),
                }
            ),
            errors=errors,
        )

    async def async_step_tariffs(self, user_input=None):
        """Step 3: Tariff rates (pre-filled with EVN Macedonia 2026 values)."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_billing()

        return self.async_show_form(
            step_id="tariffs",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_VT_BLOCK1_RATE, default=DEFAULT_VT_BLOCK1_RATE): _number(0, 50),
                    vol.Required(CONF_VT_BLOCK2_RATE, default=DEFAULT_VT_BLOCK2_RATE): _number(0, 50),
                    vol.Required(CONF_VT_BLOCK3_RATE, default=DEFAULT_VT_BLOCK3_RATE): _number(0, 50),
                    vol.Required(CONF_VT_BLOCK4_RATE, default=DEFAULT_VT_BLOCK4_RATE): _number(0, 100),
                    vol.Required(CONF_NT_RATE, default=DEFAULT_NT_RATE): _number(0, 50),
                    vol.Required(CONF_TD_RATE, default=DEFAULT_TD_RATE): _number(0, 20),
                    vol.Required(CONF_NETWORK_ACCESS, default=DEFAULT_NETWORK_ACCESS): _number(0, 5000, 0.01),
                    vol.Required(CONF_VAT_PERCENT, default=DEFAULT_VAT_PERCENT): _number(0, 50, 0.5),
                    vol.Required(CONF_MUNICIPAL_TAX, default=DEFAULT_MUNICIPAL_TAX): _number(0, 5000, 0.01),
                }
            ),
        )

    async def async_step_billing(self, user_input=None):
        """Step 4: Billing period start date + optional notifications.

        Also captures the current snapshot from the selected sensors so that
        consumption is calculated from this moment forward.
        """
        if user_input is not None:
            self._data.update(user_input)

            # Capture snapshot at end of setup
            snap_peak = _read_sensor_float(self.hass, self._data.get(CONF_PEAK_ENTITY))
            snap_offpeak = _read_sensor_float(self.hass, self._data.get(CONF_OFFPEAK_ENTITY))
            self._data[CONF_SNAPSHOT_PEAK] = snap_peak
            self._data[CONF_SNAPSHOT_OFFPEAK] = snap_offpeak if snap_offpeak is not None else 0.0

            name = self._data.get(CONF_CONSUMER_NAME, "Energy Invoice MK")
            return self.async_create_entry(title=name, data=self._data)

        return self.async_show_form(
            step_id="billing",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PERIOD_START_DATE): selector.DateSelector(),
                    vol.Optional(CONF_NOTIFY_ON_PERIOD_END, default=False): bool,
                    vol.Optional(CONF_NOTIFY_SERVICE, default="notify.notify"): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EnergyInvoiceMKOptionsFlow(config_entry)


class EnergyInvoiceMKOptionsFlow(config_entries.OptionsFlow):
    """Options flow — update tariffs, sensors, or billing period."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        def get(key, default=None):
            return self._config_entry.options.get(
                key, self._config_entry.data.get(key, default)
            )

        peak = get(CONF_PEAK_ENTITY)
        offpeak = get(CONF_OFFPEAK_ENTITY)
        period_start = get(CONF_PERIOD_START_DATE)

        sensor_schema: dict = {}
        if peak:
            sensor_schema[vol.Optional(CONF_PEAK_ENTITY, default=peak)] = _energy_sensor_selector()
        else:
            sensor_schema[vol.Optional(CONF_PEAK_ENTITY)] = _energy_sensor_selector()
        if offpeak:
            sensor_schema[vol.Optional(CONF_OFFPEAK_ENTITY, default=offpeak)] = _energy_sensor_selector()
        else:
            sensor_schema[vol.Optional(CONF_OFFPEAK_ENTITY)] = _energy_sensor_selector()

        date_schema: dict = {}
        if period_start:
            date_schema[vol.Optional(CONF_PERIOD_START_DATE, default=period_start)] = selector.DateSelector()
        else:
            date_schema[vol.Optional(CONF_PERIOD_START_DATE)] = selector.DateSelector()

        tariff_schema = {
            vol.Required(CONF_VT_BLOCK1_RATE, default=get(CONF_VT_BLOCK1_RATE, DEFAULT_VT_BLOCK1_RATE)): _number(0, 50),
            vol.Required(CONF_VT_BLOCK2_RATE, default=get(CONF_VT_BLOCK2_RATE, DEFAULT_VT_BLOCK2_RATE)): _number(0, 50),
            vol.Required(CONF_VT_BLOCK3_RATE, default=get(CONF_VT_BLOCK3_RATE, DEFAULT_VT_BLOCK3_RATE)): _number(0, 50),
            vol.Required(CONF_VT_BLOCK4_RATE, default=get(CONF_VT_BLOCK4_RATE, DEFAULT_VT_BLOCK4_RATE)): _number(0, 100),
            vol.Required(CONF_NT_RATE, default=get(CONF_NT_RATE, DEFAULT_NT_RATE)): _number(0, 50),
            vol.Required(CONF_TD_RATE, default=get(CONF_TD_RATE, DEFAULT_TD_RATE)): _number(0, 20),
            vol.Required(CONF_NETWORK_ACCESS, default=get(CONF_NETWORK_ACCESS, DEFAULT_NETWORK_ACCESS)): _number(0, 5000, 0.01),
            vol.Required(CONF_VAT_PERCENT, default=get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT)): _number(0, 50, 0.5),
            vol.Required(CONF_MUNICIPAL_TAX, default=get(CONF_MUNICIPAL_TAX, DEFAULT_MUNICIPAL_TAX)): _number(0, 5000, 0.01),
            vol.Optional(CONF_NOTIFY_ON_PERIOD_END, default=get(CONF_NOTIFY_ON_PERIOD_END, False)): bool,
            vol.Optional(CONF_NOTIFY_SERVICE, default=get(CONF_NOTIFY_SERVICE, "notify.notify")): str,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({**sensor_schema, **date_schema, **tariff_schema}),
        )
