"""DataUpdateCoordinator for Energy Invoice MK - EVN Macedonia billing."""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    CONF_CONSUMER_NAME,
    CONF_LAST_INVOICE_END,
    CONF_MUNICIPAL_TAX,
    CONF_NETWORK_ACCESS,
    CONF_NOTIFY_ON_PERIOD_END,
    CONF_NOTIFY_SERVICE,
    CONF_NT_RATE,
    CONF_NT_SENSOR,
    CONF_OFFPEAK_ENTITY,
    CONF_PEAK_ENTITY,
    CONF_PERIOD_START_DATE,
    CONF_SNAPSHOT_ENTITY_OFFPEAK,
    CONF_SNAPSHOT_ENTITY_PEAK,
    CONF_SNAPSHOT_OFFPEAK,
    CONF_SNAPSHOT_PEAK,
    CONF_TD_RATE,
    CONF_VAT_PERCENT,
    CONF_VT_BLOCK1_RATE,
    CONF_VT_BLOCK2_RATE,
    CONF_VT_BLOCK3_RATE,
    CONF_VT_BLOCK4_RATE,
    CONF_VT_SENSOR,
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
    DATA_PERIOD_END,
    DATA_PERIOD_HISTORY,
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
    INVOICE_DIR,
    STORAGE_KEY,
    STORAGE_VERSION,
    VT_BLOCK1_LIMIT,
    VT_BLOCK2_LIMIT,
    VT_BLOCK3_LIMIT,
)

_LOGGER = logging.getLogger(__name__)

_D = Decimal  # shorthand


def _d(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def _calculate_vt_cost(
    vt_kwh: Decimal,
    block1_rate: Decimal,
    block2_rate: Decimal,
    block3_rate: Decimal,
    block4_rate: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """Tiered block pricing for VT consumption. Returns (total, b1..b4 kWh, b1..b4 cost)."""
    remaining = vt_kwh

    b1_kwh = min(remaining, _d(VT_BLOCK1_LIMIT))
    remaining -= b1_kwh

    b2_kwh = min(remaining, _d(VT_BLOCK2_LIMIT - VT_BLOCK1_LIMIT))
    remaining -= b2_kwh

    b3_kwh = min(remaining, _d(VT_BLOCK3_LIMIT - VT_BLOCK2_LIMIT))
    remaining -= b3_kwh

    b4_kwh = remaining

    b1_cost = b1_kwh * block1_rate
    b2_cost = b2_kwh * block2_rate
    b3_cost = b3_kwh * block3_rate
    b4_cost = b4_kwh * block4_rate
    total = b1_cost + b2_cost + b3_cost + b4_cost

    return total, b1_kwh, b2_kwh, b3_kwh, b4_kwh, b1_cost, b2_cost, b3_cost, b4_cost


def calculate_evn_bill(
    vt_kwh: float,
    nt_kwh: float,
    vt_block1_rate: float = DEFAULT_VT_BLOCK1_RATE,
    vt_block2_rate: float = DEFAULT_VT_BLOCK2_RATE,
    vt_block3_rate: float = DEFAULT_VT_BLOCK3_RATE,
    vt_block4_rate: float = DEFAULT_VT_BLOCK4_RATE,
    nt_rate: float = DEFAULT_NT_RATE,
    td_rate: float = DEFAULT_TD_RATE,
    network_access: float = DEFAULT_NETWORK_ACCESS,
    vat_percent: float = DEFAULT_VAT_PERCENT,
    municipal_tax: float = DEFAULT_MUNICIPAL_TAX,
) -> dict[str, Any]:
    """Full EVN Macedonia bill calculation using Decimal arithmetic."""
    vt = _d(vt_kwh)
    nt = _d(nt_kwh)
    total_kwh = vt + nt

    (
        vt_cost,
        b1_kwh, b2_kwh, b3_kwh, b4_kwh,
        b1_cost, b2_cost, b3_cost, b4_cost,
    ) = _calculate_vt_cost(vt, _d(vt_block1_rate), _d(vt_block2_rate), _d(vt_block3_rate), _d(vt_block4_rate))

    nt_cost = nt * _d(nt_rate)
    energy_cost = vt_cost + nt_cost
    td_cost = total_kwh * _d(td_rate)
    net_access = _d(network_access)
    subtotal = energy_cost + td_cost + net_access
    vat_amount = subtotal * (_d(vat_percent) / _d(100))
    total_with_vat = subtotal + vat_amount
    mun_tax = _d(municipal_tax)
    grand_total = total_with_vat + mun_tax

    def _f3(d: Decimal) -> float:
        return float(d.quantize(_d("0.001"), rounding=ROUND_HALF_UP))

    def _f2(d: Decimal) -> float:
        return float(d.quantize(_d("0.01"), rounding=ROUND_HALF_UP))

    return {
        DATA_VT_CONSUMPTION: _f3(vt),
        DATA_NT_CONSUMPTION: _f3(nt),
        DATA_TOTAL_CONSUMPTION: _f3(total_kwh),
        DATA_VT_BLOCK1_KWH: _f3(b1_kwh),
        DATA_VT_BLOCK2_KWH: _f3(b2_kwh),
        DATA_VT_BLOCK3_KWH: _f3(b3_kwh),
        DATA_VT_BLOCK4_KWH: _f3(b4_kwh),
        DATA_VT_BLOCK1_COST: _f2(b1_cost),
        DATA_VT_BLOCK2_COST: _f2(b2_cost),
        DATA_VT_BLOCK3_COST: _f2(b3_cost),
        DATA_VT_BLOCK4_COST: _f2(b4_cost),
        DATA_VT_COST: _f2(vt_cost),
        DATA_NT_COST: _f2(nt_cost),
        DATA_ENERGY_COST: _f2(energy_cost),
        DATA_TD_COST: _f2(td_cost),
        DATA_NETWORK_ACCESS: _f2(net_access),
        DATA_SUBTOTAL: _f2(subtotal),
        DATA_VAT_AMOUNT: _f2(vat_amount),
        DATA_TOTAL_WITH_VAT: _f2(total_with_vat),
        DATA_MUNICIPAL_TAX: _f2(mun_tax),
        DATA_TOTAL_COST: _f2(grand_total),
    }


class EnergyInvoiceCoordinator(DataUpdateCoordinator):
    """Coordinates energy data fetching and EVN Macedonia bill calculation."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.entry = entry
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self._stored_data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            await self._load_stored_data()
            return await self._calculate_data()
        except Exception as err:
            raise UpdateFailed(f"Error updating energy invoice data: {err}") from err

    async def _load_stored_data(self) -> None:
        stored = await self._store.async_load()
        self._stored_data = stored if stored else {}

    async def _save_stored_data(self) -> None:
        await self._store.async_save(self._stored_data)

    def _get_sensor_value(self, entity_id: str) -> float | None:
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown", ""):
            _LOGGER.warning("Sensor %s is unavailable or unknown", entity_id)
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Cannot parse sensor value for %s: %s", entity_id, state.state)
            return None

    def _get_cfg(self, key: str, default: Any = None) -> Any:
        return self.entry.options.get(key, self.entry.data.get(key, default))

    def _get_entity_ids(self) -> tuple[str | None, str | None]:
        """Return (peak_entity, offpeak_entity) with v1→v2 fallback."""
        peak = self._get_cfg(CONF_PEAK_ENTITY) or self._get_cfg(CONF_VT_SENSOR)
        offpeak = self._get_cfg(CONF_OFFPEAK_ENTITY) or self._get_cfg(CONF_NT_SENSOR)
        return peak, offpeak

    def _get_tariff_params(self) -> dict[str, float]:
        return {
            "vt_block1_rate": float(self._get_cfg(CONF_VT_BLOCK1_RATE, DEFAULT_VT_BLOCK1_RATE)),
            "vt_block2_rate": float(self._get_cfg(CONF_VT_BLOCK2_RATE, DEFAULT_VT_BLOCK2_RATE)),
            "vt_block3_rate": float(self._get_cfg(CONF_VT_BLOCK3_RATE, DEFAULT_VT_BLOCK3_RATE)),
            "vt_block4_rate": float(self._get_cfg(CONF_VT_BLOCK4_RATE, DEFAULT_VT_BLOCK4_RATE)),
            "nt_rate": float(self._get_cfg(CONF_NT_RATE, DEFAULT_NT_RATE)),
            "td_rate": float(self._get_cfg(CONF_TD_RATE, DEFAULT_TD_RATE)),
            "network_access": float(self._get_cfg(CONF_NETWORK_ACCESS, DEFAULT_NETWORK_ACCESS)),
            "vat_percent": float(self._get_cfg(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT)),
            "municipal_tax": float(self._get_cfg(CONF_MUNICIPAL_TAX, DEFAULT_MUNICIPAL_TAX)),
        }

    def _get_period_start(self) -> date:
        """Get current billing period start date from config."""
        raw = self._get_cfg(CONF_PERIOD_START_DATE)
        if raw:
            try:
                return date.fromisoformat(raw)
            except ValueError:
                pass
        # Legacy: derive from last_invoice_end + 1 day
        last_end = self._get_cfg(CONF_LAST_INVOICE_END)
        if last_end:
            try:
                return date.fromisoformat(last_end) + timedelta(days=1)
            except ValueError:
                pass
        return date.today()

    async def _calculate_data(self) -> dict[str, Any]:
        peak_entity, offpeak_entity = self._get_entity_ids()
        tariff = self._get_tariff_params()

        current_peak = self._get_sensor_value(peak_entity) if peak_entity else None
        current_offpeak = self._get_sensor_value(offpeak_entity) if offpeak_entity else None
        if current_offpeak is None:
            current_offpeak = 0.0

        snap_peak = self._get_cfg(CONF_SNAPSHOT_PEAK)
        snap_offpeak = self._get_cfg(CONF_SNAPSHOT_OFFPEAK)
        snap_entity_peak = self._get_cfg(CONF_SNAPSHOT_ENTITY_PEAK)
        snap_entity_offpeak = self._get_cfg(CONF_SNAPSHOT_ENTITY_OFFPEAK)

        # Re-take snapshot if: (a) no snapshot yet, or (b) sensor was changed
        needs_snapshot = (
            (snap_peak is None and current_peak is not None)
            or (peak_entity and snap_entity_peak and snap_entity_peak != peak_entity)
        )
        if needs_snapshot and current_peak is not None:
            _LOGGER.info(
                "Taking new snapshot for %s = %.3f kWh (reason: %s)",
                peak_entity,
                current_peak,
                "entity changed" if snap_entity_peak and snap_entity_peak != peak_entity else "first run",
            )
            new_data = {
                **self.entry.data,
                CONF_SNAPSHOT_PEAK: current_peak,
                CONF_SNAPSHOT_OFFPEAK: current_offpeak,
                CONF_SNAPSHOT_ENTITY_PEAK: peak_entity,
                CONF_SNAPSHOT_ENTITY_OFFPEAK: offpeak_entity,
            }
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            snap_peak = current_peak
            snap_offpeak = current_offpeak

        _LOGGER.debug(
            "peak_entity=%s current=%.3f snap=%.3f | offpeak_entity=%s current=%.3f snap=%.3f",
            peak_entity, current_peak or 0.0, float(snap_peak or 0),
            offpeak_entity, current_offpeak, float(snap_offpeak or 0),
        )

        vt_consumption = 0.0
        nt_consumption = 0.0
        if current_peak is not None and snap_peak is not None:
            vt_consumption = max(0.0, current_peak - float(snap_peak))
        if snap_offpeak is not None:
            nt_consumption = max(0.0, current_offpeak - float(snap_offpeak))

        bill = calculate_evn_bill(vt_kwh=vt_consumption, nt_kwh=nt_consumption, **tariff)

        period_start = self._get_period_start()
        today = date.today()
        days_in_period = max(1, (today - period_start).days + 1)
        total_cost = bill[DATA_TOTAL_COST]
        daily_avg = total_cost / days_in_period

        # Historical helper data (uses recorder if available)
        hist = await self._calculate_historical_data(peak_entity, offpeak_entity, tariff)

        # Notification on period rollover (legacy support)
        prev_cost = float(self._stored_data.get(DATA_PREVIOUS_MONTH_COST, 0.0))
        prev_kwh = float(self._stored_data.get(DATA_PREVIOUS_MONTH_CONSUMPTION, 0.0))

        if self._get_cfg(CONF_NOTIFY_ON_PERIOD_END):
            stored_period = self._stored_data.get(DATA_PERIOD_START)
            current_period_str = period_start.isoformat()
            if stored_period and stored_period != current_period_str:
                await self._send_monthly_notification(prev_cost, prev_kwh)

        self._stored_data[DATA_PERIOD_START] = period_start.isoformat()
        self._stored_data["current_period_cost"] = total_cost
        self._stored_data["current_period_consumption"] = vt_consumption + nt_consumption
        await self._save_stored_data()

        return {
            **bill,
            DATA_DAILY_AVERAGE_COST: round(daily_avg, 2),
            DATA_ESTIMATED_MONTHLY: round(daily_avg * 30, 2),
            DATA_DAYS_IN_PERIOD: days_in_period,
            DATA_PREVIOUS_MONTH_COST: prev_cost,
            DATA_PREVIOUS_MONTH_CONSUMPTION: prev_kwh,
            DATA_PERIOD_START: period_start.isoformat(),
            DATA_PERIOD_END: (period_start + timedelta(days=days_in_period - 1)).isoformat(),
            **hist,
            # Pass through rates for sensor attributes
            "vt_block1_rate": tariff["vt_block1_rate"],
            "vt_block2_rate": tariff["vt_block2_rate"],
            "vt_block3_rate": tariff["vt_block3_rate"],
            "vt_block4_rate": tariff["vt_block4_rate"],
            "nt_rate": tariff["nt_rate"],
            "td_rate": tariff["td_rate"],
            "vat_percent": tariff["vat_percent"],
            # Diagnostic fields — visible in Developer Tools → States → Attributes
            "_diag_peak_entity": peak_entity,
            "_diag_offpeak_entity": offpeak_entity,
            "_diag_current_peak_kwh": round(current_peak, 3) if current_peak is not None else None,
            "_diag_current_offpeak_kwh": round(current_offpeak, 3),
            "_diag_snapshot_peak_kwh": round(float(snap_peak), 3) if snap_peak is not None else None,
            "_diag_snapshot_offpeak_kwh": round(float(snap_offpeak), 3) if snap_offpeak is not None else None,
            "_diag_sensor_available": current_peak is not None,
        }

    async def _calculate_historical_data(
        self,
        peak_entity: str | None,
        offpeak_entity: str | None,
        tariff: dict[str, float],
    ) -> dict[str, float]:
        """Calculate last-30-days, previous-period, and this-year data via recorder."""
        empty = {
            DATA_LAST_30_DAYS_CONSUMPTION: 0.0,
            DATA_LAST_30_DAYS_COST: 0.0,
            DATA_PREVIOUS_PERIOD_CONSUMPTION: float(self._stored_data.get(DATA_PREVIOUS_MONTH_CONSUMPTION, 0.0)),
            DATA_PREVIOUS_PERIOD_COST: float(self._stored_data.get(DATA_PREVIOUS_MONTH_COST, 0.0)),
            DATA_THIS_YEAR_CONSUMPTION: 0.0,
            DATA_THIS_YEAR_COST: 0.0,
        }
        if not peak_entity:
            return empty

        try:
            today = date.today()
            start_30 = today - timedelta(days=30)
            start_year = date(today.year, 1, 1)

            peak_30_start = await self._get_historical_value(peak_entity, start_30)
            peak_now = self._get_sensor_value(peak_entity)
            offpeak_30_start = await self._get_historical_value(offpeak_entity, start_30) if offpeak_entity else None
            offpeak_now = self._get_sensor_value(offpeak_entity) if offpeak_entity else 0.0

            peak_year_start = await self._get_historical_value(peak_entity, start_year)
            offpeak_year_start = await self._get_historical_value(offpeak_entity, start_year) if offpeak_entity else None

            if peak_30_start is not None and peak_now is not None:
                vt_30 = max(0.0, peak_now - peak_30_start)
                nt_30 = max(0.0, (offpeak_now or 0.0) - (offpeak_30_start or 0.0))
                bill_30 = calculate_evn_bill(vt_kwh=vt_30, nt_kwh=nt_30, **tariff)
                empty[DATA_LAST_30_DAYS_CONSUMPTION] = round(vt_30 + nt_30, 3)
                empty[DATA_LAST_30_DAYS_COST] = bill_30[DATA_TOTAL_COST]

            if peak_year_start is not None and peak_now is not None:
                vt_yr = max(0.0, peak_now - peak_year_start)
                nt_yr = max(0.0, (offpeak_now or 0.0) - (offpeak_year_start or 0.0))
                bill_yr = calculate_evn_bill(vt_kwh=vt_yr, nt_kwh=nt_yr, **tariff)
                empty[DATA_THIS_YEAR_CONSUMPTION] = round(vt_yr + nt_yr, 3)
                empty[DATA_THIS_YEAR_COST] = bill_yr[DATA_TOTAL_COST]

        except Exception as err:
            _LOGGER.debug("Historical data unavailable: %s", err)

        return empty

    async def _get_historical_value(self, entity_id: str, target_date: date) -> float | None:
        """Get sensor value at midnight of target_date via recorder."""
        try:
            from homeassistant.components.recorder import get_instance
            from homeassistant.components.recorder.history import state_changes_during_period

            tz = dt_util.get_default_time_zone()
            start_dt = dt_util.as_utc(datetime.combine(target_date, time(0, 0, 0), tzinfo=tz))
            end_dt = dt_util.as_utc(datetime.combine(target_date, time(1, 0, 0), tzinfo=tz))

            instance = get_instance(self.hass)
            states_map = await instance.async_add_executor_job(
                state_changes_during_period,
                self.hass,
                start_dt,
                end_dt,
                entity_id,
                True,   # no_attributes — faster
                False,
                1,      # limit to 1 result
            )
            entity_states = states_map.get(entity_id, [])
            if entity_states:
                return float(entity_states[0].state)
        except Exception as err:
            _LOGGER.debug("Could not get historical value for %s at %s: %s", entity_id, target_date, err)
        return None

    async def _send_monthly_notification(self, total_cost: float, total_kwh: float) -> None:
        notify_service = self._get_cfg(CONF_NOTIFY_SERVICE, "notify.notify")
        consumer = self._get_cfg(CONF_CONSUMER_NAME, "Konsumator")
        period = self._stored_data.get(DATA_PERIOD_START, "")
        try:
            await self.hass.services.async_call(
                "notify",
                notify_service.replace("notify.", ""),
                {
                    "title": "Fatura e energjisë - EVN",
                    "message": (
                        f"{consumer}: Periudha {period}\n"
                        f"Konsum total: {total_kwh:.1f} kWh\n"
                        f"Fatura totale: {total_cost:.0f} MKD"
                    ),
                },
            )
        except Exception as err:
            _LOGGER.warning("Could not send notification: %s", err)

    async def async_close_billing_period(self, new_start_date: date | None = None) -> None:
        """Archive current period and reset snapshot to current readings."""
        peak_entity, offpeak_entity = self._get_entity_ids()

        current_peak = self._get_sensor_value(peak_entity) if peak_entity else None
        current_offpeak = self._get_sensor_value(offpeak_entity) if offpeak_entity else 0.0
        if current_offpeak is None:
            current_offpeak = 0.0

        new_start = new_start_date or date.today()

        # Archive closed period to history in storage
        if self.data:
            old_start = self._get_cfg(CONF_PERIOD_START_DATE) or self._stored_data.get(DATA_PERIOD_START, "")
            history_entry: dict[str, Any] = {
                "period_start": old_start,
                "period_end": (new_start - timedelta(days=1)).isoformat(),
                "total_cost": self.data.get(DATA_TOTAL_COST, 0.0),
                "total_kwh": self.data.get(DATA_TOTAL_CONSUMPTION, 0.0),
                "vt_kwh": self.data.get(DATA_VT_CONSUMPTION, 0.0),
                "nt_kwh": self.data.get(DATA_NT_CONSUMPTION, 0.0),
            }
            stored = await self._store.async_load() or {}
            history: list[dict[str, Any]] = stored.get(DATA_PERIOD_HISTORY, [])
            history.append(history_entry)
            stored[DATA_PERIOD_HISTORY] = history
            stored[DATA_PREVIOUS_MONTH_COST] = self.data.get(DATA_TOTAL_COST, 0.0)
            stored[DATA_PREVIOUS_MONTH_CONSUMPTION] = self.data.get(DATA_TOTAL_CONSUMPTION, 0.0)
            await self._store.async_save(stored)
            _LOGGER.debug("Archived billing period %s → %s to history", old_start, history_entry["period_end"])

        new_data = {
            **self.entry.data,
            CONF_SNAPSHOT_PEAK: current_peak,
            CONF_SNAPSHOT_OFFPEAK: current_offpeak,
            CONF_PERIOD_START_DATE: new_start.isoformat(),
        }
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        await self.async_refresh()
        _LOGGER.info("Billing period closed. New period starts %s", new_start.isoformat())

    async def async_calculate_period(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Calculate consumption and cost for an arbitrary historical period."""
        peak_entity, offpeak_entity = self._get_entity_ids()
        if not peak_entity:
            raise ValueError("No peak entity configured")

        today = date.today()
        end_date = min(end_date, today)

        if end_date < start_date:
            raise ValueError(f"end_date {end_date} is before start_date {start_date}")

        # Get boundary values from recorder
        peak_start_val = await self._get_historical_value(peak_entity, start_date)
        offpeak_start_val = await self._get_historical_value(offpeak_entity, start_date) if offpeak_entity else None

        # For end: use current value if end_date is today, else recorder
        if end_date == today:
            peak_end_val = self._get_sensor_value(peak_entity)
            offpeak_end_val = self._get_sensor_value(offpeak_entity) if offpeak_entity else 0.0
        else:
            peak_end_val = await self._get_historical_value(peak_entity, end_date)
            offpeak_end_val = await self._get_historical_value(offpeak_entity, end_date) if offpeak_entity else None

        if peak_start_val is None:
            raise ValueError(
                f"No historical data for {peak_entity} on {start_date}. "
                "The sensor may not have existed yet or recorder may have purged this data."
            )
        if peak_end_val is None:
            raise ValueError(f"No data for {peak_entity} on {end_date}.")

        vt_kwh = max(0.0, peak_end_val - peak_start_val)
        nt_kwh = max(0.0, (offpeak_end_val or 0.0) - (offpeak_start_val or 0.0))
        days = (end_date - start_date).days + 1

        tariff = self._get_tariff_params()
        bill = calculate_evn_bill(vt_kwh=vt_kwh, nt_kwh=nt_kwh, **tariff)
        total_kwh = vt_kwh + nt_kwh

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
            "peak_kwh": round(vt_kwh, 3),
            "offpeak_kwh": round(nt_kwh, 3),
            "total_kwh": round(total_kwh, 3),
            "peak_cost": bill[DATA_VT_COST],
            "offpeak_cost": bill[DATA_NT_COST],
            "td_cost": bill[DATA_TD_COST],
            "network_access": bill[DATA_NETWORK_ACCESS],
            "subtotal": bill[DATA_SUBTOTAL],
            "vat": bill[DATA_VAT_AMOUNT],
            "total_with_vat": bill[DATA_TOTAL_WITH_VAT],
            "municipal_tax": bill[DATA_MUNICIPAL_TAX],
            "total_cost": bill[DATA_TOTAL_COST],
            "daily_average_kwh": round(total_kwh / days, 3) if days else 0.0,
            "daily_average_cost": round(bill[DATA_TOTAL_COST] / days, 2) if days else 0.0,
        }

    async def async_generate_invoice(
        self, month: int | None = None, year: int | None = None
    ) -> str:
        from .invoice import generate_pdf_invoice

        now = datetime.now()
        month = month or now.month
        year = year or now.year

        invoice_dir = self.hass.config.path(INVOICE_DIR)
        os.makedirs(invoice_dir, exist_ok=True)

        filename = f"energy_invoice_{year}_{month:02d}.pdf"
        filepath = os.path.join(invoice_dir, filename)

        data = self.data or {}
        cfg_data = {**self.entry.data, **self.entry.options}

        await self.hass.async_add_executor_job(
            generate_pdf_invoice, filepath, data, cfg_data, month, year
        )
        _LOGGER.info("Invoice generated: %s", filepath)
        return filepath

    async def async_reset_period(self) -> None:
        """Legacy: reset snapshot to current readings (same as close_billing_period)."""
        await self.async_close_billing_period()
