"""Constants for Energy Invoice MK integration - EVN Macedonia."""

DOMAIN = "energy_invoice_mk"
PLATFORMS = ["sensor"]

# Update interval
UPDATE_INTERVAL_MINUTES = 30

# ===========================================================================
# EVN Macedonia tariff rates - valid from 01.01.2026 (ERC decision)
# Source: https://www.erc.org.mk (Калкулатор за сметка за домаќинства)
# ===========================================================================

# VT (Visoka Tarifa / High Tariff) block rates in MKD/kWh
DEFAULT_VT_BLOCK1_RATE = 4.7074   # Block 1:    0 - 210 kWh
DEFAULT_VT_BLOCK2_RATE = 5.8976   # Block 2:  211 - 630 kWh
DEFAULT_VT_BLOCK3_RATE = 7.8537   # Block 3:  631 - 1050 kWh
DEFAULT_VT_BLOCK4_RATE = 19.1904  # Block 4: >1050 kWh

# VT block thresholds (monthly kWh consumed in high tariff)
VT_BLOCK1_LIMIT = 210    # kWh
VT_BLOCK2_LIMIT = 630    # kWh
VT_BLOCK3_LIMIT = 1050   # kWh

# NT (Niska Tarifa / Low Tariff) - flat rate
DEFAULT_NT_RATE = 2.1893  # MKD/kWh

# Transmission and Distribution (Пренос + Дистрибуција) - applied on TOTAL kWh
DEFAULT_TD_RATE = 2.0339   # MKD/kWh (applied to VT+NT combined)

# Network access fixed monthly fee (Пристап до мрежа)
DEFAULT_NETWORK_ACCESS = 200.0  # MKD/month (fixed)

# VAT (ДДВ) for electricity in North Macedonia
DEFAULT_VAT_PERCENT = 18.0  # % (NOTE: 18%, NOT 5%)

# Municipal tax (Комунална такса) - applied AFTER VAT, outside VAT base
DEFAULT_MUNICIPAL_TAX = 184.0  # MKD/month (flat, outside VAT)

# ===========================================================================
# Configuration keys - new architecture (v2)
# ===========================================================================
CONF_PEAK_ENTITY = "peak_entity"        # Accumulative lifetime VT kWh sensor
CONF_OFFPEAK_ENTITY = "offpeak_entity"  # Accumulative lifetime NT kWh sensor
CONF_PERIOD_START_DATE = "period_start_date"   # ISO date when current period started
CONF_SNAPSHOT_PEAK = "snapshot_peak"           # VT reading at period start
CONF_SNAPSHOT_OFFPEAK = "snapshot_offpeak"     # NT reading at period start
CONF_SNAPSHOT_ENTITY_PEAK = "snapshot_entity_peak"       # Entity used for peak snapshot
CONF_SNAPSHOT_ENTITY_OFFPEAK = "snapshot_entity_offpeak" # Entity used for offpeak snapshot

# Kept for migration from v1
CONF_VT_SENSOR = "vt_sensor"
CONF_NT_SENSOR = "nt_sensor"
CONF_LAST_INVOICE_START = "last_invoice_start"
CONF_LAST_INVOICE_END = "last_invoice_end"

# Tariff config keys (unchanged)
CONF_VT_BLOCK1_RATE = "vt_block1_rate"
CONF_VT_BLOCK2_RATE = "vt_block2_rate"
CONF_VT_BLOCK3_RATE = "vt_block3_rate"
CONF_VT_BLOCK4_RATE = "vt_block4_rate"
CONF_NT_RATE = "nt_rate"
CONF_TD_RATE = "td_rate"
CONF_NETWORK_ACCESS = "network_access"
CONF_VAT_PERCENT = "vat_percent"
CONF_MUNICIPAL_TAX = "municipal_tax"
CONF_METER_NUMBER = "meter_number"
CONF_CONSUMER_NAME = "consumer_name"
CONF_CONSUMER_ADDRESS = "consumer_address"
CONF_NOTIFY_ON_PERIOD_END = "notify_on_period_end"
CONF_NOTIFY_SERVICE = "notify_service"

# ===========================================================================
# Data keys used in coordinator output
# ===========================================================================
DATA_VT_CONSUMPTION = "vt_consumption"
DATA_NT_CONSUMPTION = "nt_consumption"
DATA_TOTAL_CONSUMPTION = "total_consumption"

# VT block breakdown (kWh and MKD per block)
DATA_VT_BLOCK1_KWH = "vt_block1_kwh"
DATA_VT_BLOCK2_KWH = "vt_block2_kwh"
DATA_VT_BLOCK3_KWH = "vt_block3_kwh"
DATA_VT_BLOCK4_KWH = "vt_block4_kwh"
DATA_VT_BLOCK1_COST = "vt_block1_cost"
DATA_VT_BLOCK2_COST = "vt_block2_cost"
DATA_VT_BLOCK3_COST = "vt_block3_cost"
DATA_VT_BLOCK4_COST = "vt_block4_cost"

DATA_VT_COST = "vt_cost"           # Total VT energy cost (MKD)
DATA_NT_COST = "nt_cost"           # Total NT energy cost (MKD)
DATA_ENERGY_COST = "energy_cost"   # VT + NT combined (MKD)
DATA_TD_COST = "td_cost"           # Transmission + Distribution (MKD)
DATA_NETWORK_ACCESS = "network_access_cost"  # Fixed network access (MKD)
DATA_SUBTOTAL = "subtotal"         # Energy + T&D + Network access (before VAT)
DATA_VAT_AMOUNT = "vat_amount"     # VAT 18% (MKD)
DATA_TOTAL_WITH_VAT = "total_with_vat"       # Subtotal + VAT
DATA_MUNICIPAL_TAX = "municipal_tax_amount"  # Municipal tax (outside VAT)
DATA_TOTAL_COST = "total_cost"     # Grand total (MKD)

DATA_DAILY_AVERAGE_COST = "daily_average_cost"
DATA_ESTIMATED_MONTHLY = "estimated_monthly"
DATA_DAYS_IN_PERIOD = "days_in_period"
DATA_PREVIOUS_MONTH_COST = "previous_month_cost"
DATA_PREVIOUS_MONTH_CONSUMPTION = "previous_month_consumption"
DATA_PERIOD_START = "period_start"
DATA_PERIOD_END = "period_end"

# Historical helper sensor data keys
DATA_LAST_30_DAYS_CONSUMPTION = "last_30_days_consumption"
DATA_LAST_30_DAYS_COST = "last_30_days_cost"
DATA_PREVIOUS_PERIOD_CONSUMPTION = "previous_period_consumption"
DATA_PREVIOUS_PERIOD_COST = "previous_period_cost"
DATA_THIS_YEAR_CONSUMPTION = "this_year_consumption"
DATA_THIS_YEAR_COST = "this_year_cost"

# Storage keys (internal, kept for migration)
DATA_PERIOD_START_VT = "period_start_vt"
DATA_PERIOD_START_NT = "period_start_nt"
DATA_PERIOD_HISTORY = "period_history"

# ===========================================================================
# Storage and output
# ===========================================================================
STORAGE_KEY = f"{DOMAIN}_storage"
STORAGE_VERSION = 1

INVOICE_DIR = "www/invoices"

# EVN branding colors for PDF invoice
EVN_BLUE = "#003F87"
EVN_YELLOW = "#FFD700"
