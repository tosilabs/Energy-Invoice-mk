"""Energy Invoice MK - Home Assistant integration for EVN Macedonia billing."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, UPDATE_INTERVAL_MINUTES
from .coordinator import EnergyInvoiceCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
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
        month = call.data.get("month")
        year = call.data.get("year")
        await coordinator.async_generate_invoice(month=month, year=year)

    async def handle_reset_period(call: ServiceCall) -> None:
        await coordinator.async_reset_period()

    if not hass.services.has_service(DOMAIN, "generate_invoice"):
        hass.services.async_register(DOMAIN, "generate_invoice", handle_generate_invoice)
    if not hass.services.has_service(DOMAIN, "reset_period"):
        hass.services.async_register(DOMAIN, "reset_period", handle_reset_period)
