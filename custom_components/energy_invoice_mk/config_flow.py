"""Config flow for Energy Invoice MK - EVN Macedonia."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BILLING_DAY,
    CONF_CONSUMER_ADDRESS,
    CONF_CONSUMER_NAME,
    CONF_METER_NUMBER,
    CONF_MUNICIPAL_TAX,
    CONF_NETWORK_ACCESS,
    CONF_NOTIFY_ON_PERIOD_END,
    CONF_NOTIFY_SERVICE,
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


def _energy_sensor_selector() -> selector.EntitySelector:
    # Use domain="sensor" only - no device_class filter.
    # A device_class=energy filter would reject sensors that don't have that
    # attribute explicitly set (common with smart plugs and generic energy sensors).
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )


def _number(min_val: float, max_val: float, step: float = 0.0001) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_val,
            max=max_val,
            step=step,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


class EnergyInvoiceMKConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Energy Invoice MK."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1: Consumer info (name, address, meter number)."""
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
        """Step 2: Select VT and NT energy sensors."""
        errors: dict = {}
        if user_input is not None:
            vt = user_input.get(CONF_VT_SENSOR) or None
            nt = user_input.get(CONF_NT_SENSOR) or None
            if vt or nt:
                self._data[CONF_VT_SENSOR] = vt
                self._data[CONF_NT_SENSOR] = nt
                return await self.async_step_tariffs()
            errors["base"] = "no_sensor_selected"

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_VT_SENSOR): _energy_sensor_selector(),
                    vol.Optional(CONF_NT_SENSOR): _energy_sensor_selector(),
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
        """Step 4: Billing period and optional end-of-period notifications."""
        if user_input is not None:
            self._data.update(user_input)
            name = self._data.get(CONF_CONSUMER_NAME, "Energy Invoice MK")
            return self.async_create_entry(title=name, data=self._data)

        return self.async_show_form(
            step_id="billing",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BILLING_DAY, default=DEFAULT_BILLING_DAY): _number(1, 28, 1),
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
    """Options flow - update tariffs or sensors without re-adding the integration."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        def get(key, default=None):
            return self._config_entry.options.get(
                key, self._config_entry.data.get(key, default)
            )

        # Build sensor fields without a default when value is None to avoid
        # entity selector errors with null defaults.
        vt_sensor = get(CONF_VT_SENSOR)
        nt_sensor = get(CONF_NT_SENSOR)

        sensor_schema: dict = {}
        if vt_sensor:
            sensor_schema[vol.Optional(CONF_VT_SENSOR, default=vt_sensor)] = _energy_sensor_selector()
        else:
            sensor_schema[vol.Optional(CONF_VT_SENSOR)] = _energy_sensor_selector()
        if nt_sensor:
            sensor_schema[vol.Optional(CONF_NT_SENSOR, default=nt_sensor)] = _energy_sensor_selector()
        else:
            sensor_schema[vol.Optional(CONF_NT_SENSOR)] = _energy_sensor_selector()

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
            vol.Required(CONF_BILLING_DAY, default=get(CONF_BILLING_DAY, DEFAULT_BILLING_DAY)): _number(1, 28, 1),
            vol.Optional(CONF_NOTIFY_ON_PERIOD_END, default=get(CONF_NOTIFY_ON_PERIOD_END, False)): bool,
            vol.Optional(CONF_NOTIFY_SERVICE, default=get(CONF_NOTIFY_SERVICE, "notify.notify")): str,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({**sensor_schema, **tariff_schema}),
        )
