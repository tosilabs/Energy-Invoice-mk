"""Energy Invoice MK - Home Assistant integration for EVN Macedonia billing."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_LAST_INVOICE_END,
    CONF_NT_SENSOR,
    CONF_OFFPEAK_ENTITY,
    CONF_PEAK_ENTITY,
    CONF_PERIOD_START_DATE,
    CONF_SNAPSHOT_OFFPEAK,
    CONF_SNAPSHOT_PEAK,
    CONF_VT_SENSOR,
    DOMAIN,
    PLATFORMS,
    UPDATE_INTERVAL_MINUTES,
)
from .coordinator import EnergyInvoiceCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate config entry from v1 to v2."""
    _LOGGER.debug("Migrating Energy Invoice MK entry from version %s", entry.version)

    if entry.version == 1:
        new_data = dict(entry.data)

        # Rename vt_sensor → peak_entity, nt_sensor → offpeak_entity
        if CONF_VT_SENSOR in new_data and CONF_PEAK_ENTITY not in new_data:
            new_data[CONF_PEAK_ENTITY] = new_data.pop(CONF_VT_SENSOR)
        if CONF_NT_SENSOR in new_data and CONF_OFFPEAK_ENTITY not in new_data:
            new_data[CONF_OFFPEAK_ENTITY] = new_data.pop(CONF_NT_SENSOR)

        # Derive period_start_date from last_invoice_end + 1 day
        if CONF_PERIOD_START_DATE not in new_data:
            last_end = new_data.get(CONF_LAST_INVOICE_END)
            if last_end:
                try:
                    period_start = (date.fromisoformat(last_end) + timedelta(days=1)).isoformat()
                    new_data[CONF_PERIOD_START_DATE] = period_start
                except ValueError:
                    new_data[CONF_PERIOD_START_DATE] = date.today().isoformat()
            else:
                new_data[CONF_PERIOD_START_DATE] = date.today().isoformat()

        # Snapshots: try to read current sensor state, else leave as None (coordinator handles it)
        if CONF_SNAPSHOT_PEAK not in new_data:
            peak_entity = new_data.get(CONF_PEAK_ENTITY)
            if peak_entity:
                state = hass.states.get(peak_entity)
                try:
                    new_data[CONF_SNAPSHOT_PEAK] = float(state.state) if state and state.state not in ("unavailable", "unknown") else None
                except (ValueError, TypeError):
                    new_data[CONF_SNAPSHOT_PEAK] = None
            else:
                new_data[CONF_SNAPSHOT_PEAK] = None

        if CONF_SNAPSHOT_OFFPEAK not in new_data:
            offpeak_entity = new_data.get(CONF_OFFPEAK_ENTITY)
            if offpeak_entity:
                state = hass.states.get(offpeak_entity)
                try:
                    new_data[CONF_SNAPSHOT_OFFPEAK] = float(state.state) if state and state.state not in ("unavailable", "unknown") else 0.0
                except (ValueError, TypeError):
                    new_data[CONF_SNAPSHOT_OFFPEAK] = 0.0
            else:
                new_data[CONF_SNAPSHOT_OFFPEAK] = 0.0

        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
        _LOGGER.info("Migrated Energy Invoice MK entry to version 2")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = EnergyInvoiceCoordinator(
        hass,
        entry,
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass, coordinator)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _register_services(hass: HomeAssistant, coordinator: EnergyInvoiceCoordinator) -> None:

    async def handle_generate_invoice(call: ServiceCall) -> None:
        await coordinator.async_generate_invoice(
            month=call.data.get("month"),
            year=call.data.get("year"),
        )

    async def handle_reset_period(call: ServiceCall) -> None:
        await coordinator.async_reset_period()

    async def handle_close_billing_period(call: ServiceCall) -> None:
        raw = call.data.get("period_end_date")
        new_start: date | None = None
        if raw:
            try:
                end = date.fromisoformat(str(raw))
                new_start = end + timedelta(days=1)
            except ValueError:
                _LOGGER.error("Invalid period_end_date: %s", raw)
                return
        await coordinator.async_close_billing_period(new_start_date=new_start)

    async def handle_calculate_period(call: ServiceCall) -> dict:
        start = date.fromisoformat(str(call.data["start_date"]))
        end = date.fromisoformat(str(call.data["end_date"]))
        return await coordinator.async_calculate_period(start_date=start, end_date=end)

    if not hass.services.has_service(DOMAIN, "generate_invoice"):
        hass.services.async_register(DOMAIN, "generate_invoice", handle_generate_invoice)
    if not hass.services.has_service(DOMAIN, "reset_period"):
        hass.services.async_register(DOMAIN, "reset_period", handle_reset_period)
    if not hass.services.has_service(DOMAIN, "close_billing_period"):
        hass.services.async_register(DOMAIN, "close_billing_period", handle_close_billing_period)
    if not hass.services.has_service(DOMAIN, "calculate_period"):
        hass.services.async_register(
            DOMAIN,
            "calculate_period",
            handle_calculate_period,
            supports_response=SupportsResponse.ONLY,
        )
