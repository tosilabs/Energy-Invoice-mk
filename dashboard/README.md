# EVN Macedonia Dashboard

---

## 🇦🇱 Shqip (Albanian)

### 1. Krijo Helpers (Cilësimet → Pajisjet → Helpers → Shto)

| Helper | Lloji | ID |
|--------|-------|----|
| EVN Calc Start | Datë | `input_datetime.evn_calc_start` |
| EVN Calc End | Datë | `input_datetime.evn_calc_end` |
| EVN Calc Result | Tekst | `input_text.evn_calc_result` |

### 2. Shto Skriptet

Kopjo përmbajtjen e skedarit `ha_scripts.yaml` në `scripts.yaml` tëndin,
ose krijo çdo skript manualisht tek **Cilësimet → Automatizimet → Skriptet**.

Kërkohen 4 skripte:
- `evn_calculate_period` — thërret shërbimin dhe shkruan rezultatin
- `evn_set_last_30_days` — shkurtore: plotëson zgjedhësin e datave me 30 ditët e fundit
- `evn_set_previous_month` — shkurtore: muaji i kaluar
- `evn_set_this_year` — shkurtore: 1 Janar → sot

### 3. Shto Dashboardin

Shko te **Cilësimet → Panelet → Shto Panel** (ose edito një ekzistues në modalitetin raw YAML)
dhe ngjit përmbajtjen e skedarit `lovelace.yaml`.

> **Shënim:** ID-t e entiteteve përdorin emrin e konsumatorit **"Fatos"**. Nëse emri yt është
> ndryshe, bëj find-and-replace të `fatos` me emrin tënd në shkronja të vogla (hapësirat → nënvizë).

### 4. Karta e Bllokut VT — Si funksionon

Karta **"⚡ Blloku VT — Ku jam tani"** tregon:
- Cilin bllok tarife je aktualisht (🟢 🟡 🔴 🚨)
- Shiritin e progresit me kWh të konsumuara për çdo bllok
- Sa kWh mbeten deri sa të kalosh në bllokun tjetër (me çmim më të lartë)

| Blloku | Kufiri | Çmimi |
|--------|--------|-------|
| Blloku 1 | 0 – 210 kWh | 4.71 MKD/kWh |
| Blloku 2 | 211 – 630 kWh | 5.90 MKD/kWh |
| Blloku 3 | 631 – 1050 kWh | 7.85 MKD/kWh |
| Blloku 4 | > 1050 kWh | 19.19 MKD/kWh |

### 5. Lista e Entiteteve

| Sensorë | Entity ID |
|---------|-----------|
| Fatura totale | `sensor.fatos_total_bill_current_period` |
| Konsumi VT | `sensor.fatos_vt_consumption_current_period` |
| Konsumi NT | `sensor.fatos_nt_consumption_current_period` |
| Konsumi total | `sensor.fatos_total_consumption_current_period` |
| Fatura mujore e parashikuar | `sensor.fatos_estimated_monthly_bill` |
| Mesatare ditore | `sensor.fatos_daily_average_cost` |
| Konsumi 30 ditë | `sensor.fatos_last_30_days_consumption` |
| Kostoja 30 ditë | `sensor.fatos_last_30_days_cost` |
| Konsumi periudha e mëparshme | `sensor.fatos_previous_billing_period_consumption` |
| Kostoja periudha e mëparshme | `sensor.fatos_previous_billing_period_cost` |
| Konsumi këtë vit | `sensor.fatos_this_year_consumption` |
| Kostoja këtë vit | `sensor.fatos_this_year_cost` |

---

## 🇲🇰 Македонски (Macedonian)

### 1. Креирај Helpers (Поставки → Уреди → Helpers → Додај)

| Helper | Тип | ID |
|--------|-----|----|
| EVN Calc Start | Датум | `input_datetime.evn_calc_start` |
| EVN Calc End | Датум | `input_datetime.evn_calc_end` |
| EVN Calc Result | Текст | `input_text.evn_calc_result` |

### 2. Додај Скрипти

Копирај ја содржината на `ha_scripts.yaml` во твојот `scripts.yaml`,
или создај ги рачно преку **Поставки → Автоматизации → Скрипти**.

Потребни се 4 скрипти:
- `evn_calculate_period` — го повикува сервисот и го запишува резултатот
- `evn_set_last_30_days` — кратенка: ги пополнува датумите со последните 30 дена
- `evn_set_previous_month` — кратенка: претходниот календарски месец
- `evn_set_this_year` — кратенка: 1 Јануари → денес

### 3. Додај Дашборд

Оди на **Поставки → Дашборди → Додај Дашборд** (или уреди постоечки во raw YAML режим)
и залепи ја содржината на `lovelace.yaml`.

> **Забелешка:** Entity ID-ата го користат потрошувачкото име **"Fatos"**. Ако твоето
> е различно, замени го `fatos` со твоето име во мали букви (празни места → долна црта).

### 4. Картичка за VT Блок — Како работи

Картичката **"⚡ Blloku VT — Ku jam tani"** прикажува:
- Во кој тарифен блок се наоѓаш моментално (🟢 🟡 🔴 🚨)
- Лента за напредок со потрошени kWh по блок
- Колку kWh остануваат до следниот блок (со повисока цена)

| Блок | Граница | Цена |
|------|---------|------|
| Блок 1 | 0 – 210 kWh | 4.71 MKD/kWh |
| Блок 2 | 211 – 630 kWh | 5.90 MKD/kWh |
| Блок 3 | 631 – 1050 kWh | 7.85 MKD/kWh |
| Блок 4 | > 1050 kWh | 19.19 MKD/kWh |

### 5. Листа на Ентитети

| Сензор | Entity ID |
|--------|-----------|
| Вкупна сметка | `sensor.fatos_total_bill_current_period` |
| VT потрошувачка | `sensor.fatos_vt_consumption_current_period` |
| NT потрошувачка | `sensor.fatos_nt_consumption_current_period` |
| Вкупна потрошувачка | `sensor.fatos_total_consumption_current_period` |
| Проценка месечна сметка | `sensor.fatos_estimated_monthly_bill` |
| Дневен просек | `sensor.fatos_daily_average_cost` |
| Потрошувачка 30 дена | `sensor.fatos_last_30_days_consumption` |
| Трошок 30 дена | `sensor.fatos_last_30_days_cost` |
| Потрошувачка претходен период | `sensor.fatos_previous_billing_period_consumption` |
| Трошок претходен период | `sensor.fatos_previous_billing_period_cost` |
| Потрошувачка оваа година | `sensor.fatos_this_year_consumption` |
| Трошок оваа година | `sensor.fatos_this_year_cost` |

---

## 🇬🇧 English

### 1. Create Helpers (Settings → Devices & Services → Helpers → Add)

| Helper | Type | ID |
|--------|------|----|
| EVN Calc Start | Date | `input_datetime.evn_calc_start` |
| EVN Calc End | Date | `input_datetime.evn_calc_end` |
| EVN Calc Result | Text | `input_text.evn_calc_result` |

### 2. Add Scripts

Copy the content of `ha_scripts.yaml` into your `scripts.yaml`,
or create each script manually via **Settings → Automations & Scenes → Scripts**.

Four scripts are needed:
- `evn_calculate_period` — calls the service and writes result
- `evn_set_last_30_days` — shortcut: fills date pickers with last 30 days
- `evn_set_previous_month` — shortcut: fills with previous calendar month
- `evn_set_this_year` — shortcut: fills with Jan 1 → today

### 3. Add Dashboard

Go to **Settings → Dashboards → Add Dashboard** (or edit an existing one in raw YAML mode)
and paste the contents of `lovelace.yaml`.

> **Note:** Entity IDs use the consumer name **"Fatos"**. If your consumer name is different,
> do a find-and-replace of `fatos` with your name in lowercase (spaces → underscores).

### 4. VT Block Card — How it works

The **"⚡ Blloku VT — Ku jam tani"** card shows:
- Which tariff block you are currently in (🟢 🟡 🔴 🚨)
- A progress bar with kWh consumed per block
- How many kWh remain until you enter the next (more expensive) block

| Block | Range | Rate |
|-------|-------|------|
| Block 1 | 0 – 210 kWh | 4.71 MKD/kWh |
| Block 2 | 211 – 630 kWh | 5.90 MKD/kWh |
| Block 3 | 631 – 1050 kWh | 7.85 MKD/kWh |
| Block 4 | > 1050 kWh | 19.19 MKD/kWh |
