# Energy Invoice MK - Home Assistant Integration

Home Assistant custom integration for tracking and calculating electricity bills using **EVN Macedonia** tariff structure.

## Features

- Tracks VT (Visoka Tarifa / High Tariff) and NT (Niska Tarifa / Low Tariff) consumption
- Calculates your monthly bill using the official **EVN Macedonia tiered block pricing** (ERC decision, valid from 01.01.2026)
- Generates **PDF invoices** matching the EVN bill format
- Sends **monthly notifications** at the end of each billing period
- Provides a **Lovelace dashboard** YAML for quick setup
- **HACS compatible**

## Tariff Structure (01.01.2026)

| Component | Rate |
|---|---|
| VT Block 1 (0–210 kWh) | 4.7074 MKD/kWh |
| VT Block 2 (211–630 kWh) | 5.8976 MKD/kWh |
| VT Block 3 (631–1050 kWh) | 7.8537 MKD/kWh |
| VT Block 4 (>1050 kWh) | 19.1904 MKD/kWh |
| NT (flat rate) | 2.1893 MKD/kWh |
| Transmission + Distribution | 2.0339 MKD/kWh (on total kWh) |
| Network access (fixed) | 200 MKD/month |
| VAT (ДДВ) | 18% |
| Municipal tax (after VAT) | 184 MKD/month |

> **Note:** All rates are configurable via the Options flow in case EVN updates them.

## Bill Calculation

```
VT cost     = tiered_block_price(vt_kwh)
NT cost     = nt_kwh × 2.1893
Energy cost = VT cost + NT cost
T&D fee     = total_kwh × 2.0339 + 200 (fixed)
Subtotal    = Energy cost + T&D fee          ← VAT base
VAT (18%)   = Subtotal × 0.18
+ VAT total = Subtotal + VAT
Municipal   = 184 MKD                        ← outside VAT
TOTAL       = + VAT total + Municipal
```

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → Custom Repositories
2. Add `https://github.com/tosilabs/Energy-Invoice-mk` (category: Integration)
3. Search for "Energy Invoice MK" and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/energy_invoice_mk/` to your HA `/config/custom_components/`
2. Restart Home Assistant

## Setup

1. Go to **Settings → Integrations → Add Integration**
2. Search for **"Energy Invoice MK"**
3. Follow the 4-step setup wizard:
   - **Step 1:** Consumer name, address, meter number
   - **Step 2:** Select your VT and NT energy sensors (from Energy Dashboard)
   - **Step 3:** Confirm tariff rates (pre-filled with 2026 EVN rates)
   - **Step 4:** Set billing day and optional notifications

## Sensors Created

| Sensor | Unit | Description |
|---|---|---|
| VT Consumption (current period) | kWh | High-tariff consumption since billing start |
| NT Consumption (current period) | kWh | Low-tariff consumption since billing start |
| Total Consumption (current period) | kWh | VT + NT combined |
| VT Energy Cost | MKD | VT cost with block pricing |
| NT Energy Cost | MKD | NT cost (flat rate) |
| Energy Cost (VT+NT) | MKD | Combined energy cost |
| Transmission & Distribution Cost | MKD | Пренос + Дистрибуција |
| VAT (DDV 18%) | MKD | 18% on subtotal |
| **Total Bill (current period)** | **MKD** | **Grand total including municipal tax** |
| Daily Average Cost | MKD | Cost per day in this period |
| Estimated Monthly Bill | MKD | Linear projection for full month |
| Previous Month Bill | MKD | Last period total |
| Previous Month Consumption | kWh | Last period kWh |

## Services

### `energy_invoice_mk.generate_invoice`

Generates a PDF invoice and saves it to `/config/www/invoices/energy_invoice_YYYY_MM.pdf`.

```yaml
service: energy_invoice_mk.generate_invoice
data:
  month: 4   # optional, defaults to current month
  year: 2026 # optional, defaults to current year
```

The PDF is accessible at: `http://homeassistant.local:8123/local/invoices/energy_invoice_2026_04.pdf`

### `energy_invoice_mk.reset_period`

Resets the billing period snapshot to current meter readings.

```yaml
service: energy_invoice_mk.reset_period
```

## Lovelace Dashboard

Add this to your dashboard YAML:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Energy Invoice MK
    entities:
      - entity: sensor.total_bill_current_period
        name: Total Bill
      - entity: sensor.estimated_monthly_bill
        name: Estimated Monthly
      - entity: sensor.vt_consumption_current_period
        name: VT Consumption
      - entity: sensor.nt_consumption_current_period
        name: NT Consumption
      - entity: sensor.daily_average_cost
        name: Daily Average

  - type: gauge
    entity: sensor.total_bill_current_period
    name: Current Bill (MKD)
    min: 0
    max: 5000
    severity:
      green: 0
      yellow: 2500
      red: 4000

  - type: history-graph
    entities:
      - entity: sensor.total_bill_current_period
    hours_to_show: 720
    title: Bill History (30 days)
```

## Automation: Monthly Invoice

```yaml
automation:
  alias: Generate EVN Invoice on billing day
  trigger:
    platform: time
    at: "08:00:00"
  condition:
    condition: template
    value_template: "{{ now().day == 1 }}"  # adjust to your billing day
  action:
    service: energy_invoice_mk.generate_invoice
```

## Updating Tariffs

When EVN updates rates, go to:
**Settings → Integrations → Energy Invoice MK → Configure**

All tariff rates can be updated without re-adding the integration.

## Sources

- [ERC Calculator (erc.org.mk)](https://www.erc.org.mk)
- [kilovat.mk](https://kilovat.mk)
