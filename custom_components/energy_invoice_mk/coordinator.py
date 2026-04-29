"""DataUpdateCoordinator for Energy Invoice MK - EVN Macedonia billing."""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONSUMER_ADDRESS,
    CONF_CONSUMER_NAME,
    CONF_LAST_INVOICE_END,
    CONF_LAST_INVOICE_START,
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
    DATA_DAILY_AVERAGE_COST,
    DATA_DAYS_IN_PERIOD,
    DATA_ENERGY_COST,
    DATA_ESTIMATED_MONTHLY,
    DATA_MUNICIPAL_TAX,
    DATA_NETWORK_ACCESS,
    DATA_NT_CONSUMPTION,
    DATA_NT_COST,
    DATA_PERIOD_START,
    DATA_PERIOD_START_NT,
    DATA_PERIOD_START_VT,
    DATA_PREVIOUS_MONTH_CONSUMPTION,
    DATA_PREVIOUS_MONTH_COST,
    DATA_SUBTOTAL,
    DATA_TD_COST,
    DATA_TOTAL_CONSUMPTION,
    DATA_PERIOD_END,
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


def _calculate_vt_cost(
    vt_kwh: float,
    block1_rate: float,
    block2_rate: float,
    block3_rate: float,
    block4_rate: float,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    """
    Tiered block pricing for VT (high tariff) consumption.

    Structure per ERC decision, valid from 01.01.2026:
      Block 1:    0 - 210 kWh  → block1_rate MKD/kWh
      Block 2:  211 - 630 kWh  → block2_rate MKD/kWh
      Block 3:  631 - 1050 kWh → block3_rate MKD/kWh
      Block 4: >1050 kWh       → block4_rate MKD/kWh

    Returns: (total_vt_cost, b1_kwh, b2_kwh, b3_kwh, b4_kwh, b1_cost, b2_cost, b3_cost, b4_cost)
    """
    remaining = vt_kwh

    b1_kwh = min(remaining, float(VT_BLOCK1_LIMIT))
    remaining -= b1_kwh

    b2_kwh = min(remaining, float(VT_BLOCK2_LIMIT - VT_BLOCK1_LIMIT))
    remaining -= b2_kwh

    b3_kwh = min(remaining, float(VT_BLOCK3_LIMIT - VT_BLOCK2_LIMIT))
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
    """
    Full EVN Macedonia bill calculation per ERC tariff structure.

    Calculation order (as per official ERC calculator):
      1. VT cost     = tiered block pricing on vt_kwh
      2. NT cost     = nt_kwh × nt_rate
      3. Energy cost = VT cost + NT cost
      4. T&D fee     = total_kwh × td_rate  (Пренос+Дистрибуција per kWh)
      5. Network     = network_access (fixed monthly, Пристап до мрежа)
      6. Subtotal    = Energy + T&D + Network  (ДДВ base)
      7. VAT (18%)   = Subtotal × (vat_percent / 100)
      8. Total+VAT   = Subtotal + VAT
      9. Municipal   = municipal_tax  (Комунална такса - outside VAT, added last)
     10. Grand total = Total+VAT + Municipal
    """
    total_kwh = vt_kwh + nt_kwh

    (
        vt_cost,
        b1_kwh, b2_kwh, b3_kwh, b4_kwh,
        b1_cost, b2_cost, b3_cost, b4_cost,
    ) = _calculate_vt_cost(vt_kwh, vt_block1_rate, vt_block2_rate, vt_block3_rate, vt_block4_rate)

    nt_cost = nt_kwh * nt_rate
    energy_cost = vt_cost + nt_cost

    td_cost = total_kwh * td_rate
    subtotal = energy_cost + td_cost + network_access

    vat_amount = subtotal * (vat_percent / 100.0)
    total_with_vat = subtotal + vat_amount
    grand_total = total_with_vat + municipal_tax

    return {
        DATA_VT_CONSUMPTION: round(vt_kwh, 3),
        DATA_NT_CONSUMPTION: round(nt_kwh, 3),
        DATA_TOTAL_CONSUMPTION: round(total_kwh, 3),
        DATA_VT_BLOCK1_KWH: round(b1_kwh, 3),
        DATA_VT_BLOCK2_KWH: round(b2_kwh, 3),
        DATA_VT_BLOCK3_KWH: round(b3_kwh, 3),
        DATA_VT_BLOCK4_KWH: round(b4_kwh, 3),
        DATA_VT_BLOCK1_COST: round(b1_cost, 2),
        DATA_VT_BLOCK2_COST: round(b2_cost, 2),
        DATA_VT_BLOCK3_COST: round(b3_cost, 2),
        DATA_VT_BLOCK4_COST: round(b4_cost, 2),
        DATA_VT_COST: round(vt_cost, 2),
        DATA_NT_COST: round(nt_cost, 2),
        DATA_ENERGY_COST: round(energy_cost, 2),
        DATA_TD_COST: round(td_cost, 2),
        DATA_NETWORK_ACCESS: round(network_access, 2),
        DATA_SUBTOTAL: round(subtotal, 2),
        DATA_VAT_AMOUNT: round(vat_amount, 2),
        DATA_TOTAL_WITH_VAT: round(total_with_vat, 2),
        DATA_MUNICIPAL_TAX: round(municipal_tax, 2),
        DATA_TOTAL_COST: round(grand_total, 2),
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
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _get_billing_period(self) -> tuple[date, date]:
        """
        Calculate current billing period start and end dates based on the
        last invoice dates provided during setup.

        Logic:
          - period_days = last_invoice_end - last_invoice_start + 1
          - current period starts the day after last_invoice_end
          - advance by period_days until current_start + period_days > today
          - period_end = current_start + period_days - 1
        """
        last_start_str = self._get_cfg(CONF_LAST_INVOICE_START)
        last_end_str = self._get_cfg(CONF_LAST_INVOICE_END)

        today = date.today()

        # Fallback: if dates not configured, use today as start
        if not last_start_str or not last_end_str:
            return today, today + timedelta(days=29)

        last_start = date.fromisoformat(last_start_str)
        last_end = date.fromisoformat(last_end_str)
        period_days = (last_end - last_start).days + 1  # e.g. 30

        # Current period starts the day after the last invoice ended
        current_start = last_end + timedelta(days=1)

        # Advance by full periods until the next start would be in the future
        while current_start + timedelta(days=period_days) <= today:
            current_start += timedelta(days=period_days)

        current_end = current_start + timedelta(days=period_days - 1)
        return current_start, current_end

    def _get_cfg(self, key: str, default: Any = None) -> Any:
        return self.entry.options.get(key, self.entry.data.get(key, default))

    async def _calculate_data(self) -> dict[str, Any]:
        vt_sensor = self._get_cfg(CONF_VT_SENSOR)
        nt_sensor = self._get_cfg(CONF_NT_SENSOR)

        # Tariff parameters
        vt_block1 = float(self._get_cfg(CONF_VT_BLOCK1_RATE, DEFAULT_VT_BLOCK1_RATE))
        vt_block2 = float(self._get_cfg(CONF_VT_BLOCK2_RATE, DEFAULT_VT_BLOCK2_RATE))
        vt_block3 = float(self._get_cfg(CONF_VT_BLOCK3_RATE, DEFAULT_VT_BLOCK3_RATE))
        vt_block4 = float(self._get_cfg(CONF_VT_BLOCK4_RATE, DEFAULT_VT_BLOCK4_RATE))
        nt_rate = float(self._get_cfg(CONF_NT_RATE, DEFAULT_NT_RATE))
        td_rate = float(self._get_cfg(CONF_TD_RATE, DEFAULT_TD_RATE))
        network_access = float(self._get_cfg(CONF_NETWORK_ACCESS, DEFAULT_NETWORK_ACCESS))
        vat_pct = float(self._get_cfg(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT))
        municipal_tax = float(self._get_cfg(CONF_MUNICIPAL_TAX, DEFAULT_MUNICIPAL_TAX))

        current_vt = self._get_sensor_value(vt_sensor) if vt_sensor else None
        current_nt = self._get_sensor_value(nt_sensor) if nt_sensor else 0.0
        if current_nt is None:
            current_nt = 0.0

        period_start, period_end = self._get_billing_period()
        period_start_str = period_start.isoformat()

        stored_period_start = self._stored_data.get(DATA_PERIOD_START)
        if stored_period_start != period_start_str:
            # Billing cycle changed - archive previous period totals
            prev_bill = self._stored_data.get("current_period_cost", 0.0)
            prev_kwh = self._stored_data.get("current_period_consumption", 0.0)

            self._stored_data[DATA_PERIOD_START] = period_start_str
            self._stored_data[DATA_PERIOD_START_VT] = current_vt
            self._stored_data[DATA_PERIOD_START_NT] = current_nt
            if stored_period_start is not None:
                self._stored_data[DATA_PREVIOUS_MONTH_COST] = prev_bill
                self._stored_data[DATA_PREVIOUS_MONTH_CONSUMPTION] = prev_kwh
            await self._save_stored_data()

        start_vt = self._stored_data.get(DATA_PERIOD_START_VT)
        start_nt = self._stored_data.get(DATA_PERIOD_START_NT)

        vt_consumption = 0.0
        nt_consumption = 0.0

        if current_vt is not None and start_vt is not None:
            vt_consumption = max(0.0, current_vt - float(start_vt))
        if start_nt is not None:
            nt_consumption = max(0.0, current_nt - float(start_nt))

        # Calculate bill using correct EVN structure
        bill = calculate_evn_bill(
            vt_kwh=vt_consumption,
            nt_kwh=nt_consumption,
            vt_block1_rate=vt_block1,
            vt_block2_rate=vt_block2,
            vt_block3_rate=vt_block3,
            vt_block4_rate=vt_block4,
            nt_rate=nt_rate,
            td_rate=td_rate,
            network_access=network_access,
            vat_percent=vat_pct,
            municipal_tax=municipal_tax,
        )

        today = date.today()
        days_in_period = max(1, (today - period_start).days + 1)
        total_cost = bill[DATA_TOTAL_COST]
        daily_avg = total_cost / days_in_period
        estimated_monthly = daily_avg * 30

        self._stored_data["current_period_cost"] = total_cost
        self._stored_data["current_period_consumption"] = vt_consumption + nt_consumption
        await self._save_stored_data()

        if self._get_cfg(CONF_NOTIFY_ON_PERIOD_END) and stored_period_start and stored_period_start != period_start_str:
            await self._send_monthly_notification(
                self._stored_data.get(DATA_PREVIOUS_MONTH_COST, 0.0),
                self._stored_data.get(DATA_PREVIOUS_MONTH_CONSUMPTION, 0.0),
            )

        return {
            **bill,
            DATA_DAILY_AVERAGE_COST: round(daily_avg, 2),
            DATA_ESTIMATED_MONTHLY: round(estimated_monthly, 2),
            DATA_DAYS_IN_PERIOD: days_in_period,
            DATA_PREVIOUS_MONTH_COST: round(float(self._stored_data.get(DATA_PREVIOUS_MONTH_COST, 0.0)), 2),
            DATA_PREVIOUS_MONTH_CONSUMPTION: round(float(self._stored_data.get(DATA_PREVIOUS_MONTH_CONSUMPTION, 0.0)), 3),
            DATA_PERIOD_START: period_start_str,
            DATA_PERIOD_END: period_end.isoformat(),
            "vt_block1_rate": vt_block1,
            "vt_block2_rate": vt_block2,
            "vt_block3_rate": vt_block3,
            "vt_block4_rate": vt_block4,
            "nt_rate": nt_rate,
            "td_rate": td_rate,
            "vat_percent": vat_pct,
        }

    async def _send_monthly_notification(self, total_cost: float, total_kwh: float) -> None:
        notify_service = self._get_cfg(CONF_NOTIFY_SERVICE, "notify.notify")
        consumer = self._get_cfg(CONF_CONSUMER_NAME, "Konsumator")
        period = self._stored_data.get(DATA_PERIOD_START, "")
        try:
            await self.hass.services.async_call(
                "notify",
                notify_service.replace("notify.", ""),
                {
                    "title": "Fatura mujore e energjisë - EVN",
                    "message": (
                        f"{consumer}: Periudha {period}\n"
                        f"Konsum total: {total_kwh:.1f} kWh\n"
                        f"Fatura totale: {total_cost:.0f} MKD"
                    ),
                },
            )
        except Exception as err:
            _LOGGER.warning("Could not send monthly notification: %s", err)

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
        vt_sensor = self._get_cfg(CONF_VT_SENSOR)
        nt_sensor = self._get_cfg(CONF_NT_SENSOR)

        current_vt = self._get_sensor_value(vt_sensor) if vt_sensor else None
        current_nt = self._get_sensor_value(nt_sensor) if nt_sensor else 0.0
        if current_nt is None:
            current_nt = 0.0

        self._stored_data[DATA_PERIOD_START] = date.today().isoformat()
        self._stored_data[DATA_PERIOD_START_VT] = current_vt
        self._stored_data[DATA_PERIOD_START_NT] = current_nt
        await self._save_stored_data()
        await self.async_refresh()
