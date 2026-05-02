# EVN Macedonia Dashboard

## Quick Setup

### 1. Create Helpers (Settings → Devices & Services → Helpers)

| Helper | Type | ID |
|--------|------|----|
| EVN Calc Start | Date | `input_datetime.evn_calc_start` |
| EVN Calc End | Date | `input_datetime.evn_calc_end` |
| EVN Calc Result | Text | `input_text.evn_calc_result` |

### 2. Add Scripts

Copy the content of `ha_scripts.yaml` into your `scripts.yaml`, or create each script manually via **Settings → Automations & Scenes → Scripts**.

Four scripts are needed:
- `evn_calculate_period` — calls the service and writes result
- `evn_set_last_30_days` — shortcut: fills date pickers with last 30 days
- `evn_set_previous_month` — shortcut: fills with previous calendar month
- `evn_set_this_year` — shortcut: fills with Jan 1 → today

### 3. Add Dashboard

Go to **Settings → Dashboards → Add Dashboard** (or edit an existing one in raw YAML mode) and paste the contents of `lovelace.yaml`.

> **Note:** Entity IDs use the consumer name **"Fatos"**. If your consumer name is different, do a find-and-replace of `fatos` with your name in lowercase (spaces → underscores).

## Entity ID Reference

| Sensor | Entity ID |
|--------|-----------|
| Total Bill | `sensor.fatos_total_bill_current_period` |
| VT Consumption | `sensor.fatos_vt_consumption_current_period` |
| NT Consumption | `sensor.fatos_nt_consumption_current_period` |
| Total Consumption | `sensor.fatos_total_consumption_current_period` |
| Estimated Monthly | `sensor.fatos_estimated_monthly_bill` |
| Daily Average | `sensor.fatos_daily_average_cost` |
| Last 30 Days kWh | `sensor.fatos_last_30_days_consumption` |
| Last 30 Days MKD | `sensor.fatos_last_30_days_cost` |
| Previous Period kWh | `sensor.fatos_previous_billing_period_consumption` |
| Previous Period MKD | `sensor.fatos_previous_billing_period_cost` |
| This Year kWh | `sensor.fatos_this_year_consumption` |
| This Year MKD | `sensor.fatos_this_year_cost` |
