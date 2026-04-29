"""PDF invoice generator for EVN Macedonia bills."""
from __future__ import annotations

import os
from datetime import date
from typing import Any

# reportlab imports - available via manifest.json requirements
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .const import (
    DATA_DAYS_IN_PERIOD,
    DATA_ENERGY_COST,
    DATA_ESTIMATED_MONTHLY,
    DATA_MUNICIPAL_TAX,
    DATA_NETWORK_ACCESS,
    DATA_NT_CONSUMPTION,
    DATA_NT_COST,
    DATA_PERIOD_START,
    DATA_SUBTOTAL,
    DATA_TD_COST,
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
    DEFAULT_VT_BLOCK1_RATE,
    DEFAULT_VT_BLOCK2_RATE,
    DEFAULT_VT_BLOCK3_RATE,
    DEFAULT_VT_BLOCK4_RATE,
    DEFAULT_NT_RATE,
    DEFAULT_TD_RATE,
    DEFAULT_VAT_PERCENT,
    DEFAULT_NETWORK_ACCESS,
    DEFAULT_MUNICIPAL_TAX,
    CONF_CONSUMER_NAME,
    CONF_CONSUMER_ADDRESS,
    CONF_METER_NUMBER,
    CONF_VT_BLOCK1_RATE,
    CONF_VT_BLOCK2_RATE,
    CONF_VT_BLOCK3_RATE,
    CONF_VT_BLOCK4_RATE,
    CONF_NT_RATE,
    CONF_TD_RATE,
    CONF_VAT_PERCENT,
    CONF_NETWORK_ACCESS,
    CONF_MUNICIPAL_TAX,
    EVN_BLUE,
    EVN_YELLOW,
)

_EVN_BLUE = colors.HexColor(EVN_BLUE)
_EVN_YELLOW = colors.HexColor(EVN_YELLOW)
_LIGHT_GRAY = colors.HexColor("#F5F5F5")
_DARK_GRAY = colors.HexColor("#333333")


def _mkd(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _kwh(value: float) -> str:
    return f"{value:.1f}"


def _rate(value: float) -> str:
    return f"{value:.4f}"


def generate_pdf_invoice(
    filepath: str,
    data: dict[str, Any],
    cfg: dict[str, Any],
    month: int,
    year: int,
) -> None:
    """Generate an A4 PDF invoice in EVN Macedonia format."""

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # -----------------------------------------------------------------------
    # Helper styles
    # -----------------------------------------------------------------------
    header_style = ParagraphStyle(
        "header",
        parent=styles["Normal"],
        fontSize=22,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )
    subheader_style = ParagraphStyle(
        "subheader",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.white,
        fontName="Helvetica",
    )
    section_title_style = ParagraphStyle(
        "section_title",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        spaceAfter=0,
    )
    body_style = ParagraphStyle(
        "body",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
    )
    bold_style = ParagraphStyle(
        "bold",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
    )

    # -----------------------------------------------------------------------
    # Header band (EVN Blue)
    # -----------------------------------------------------------------------
    month_names = {
        1: "Јануари", 2: "Февруари", 3: "Март", 4: "Април",
        5: "Мај", 6: "Јуни", 7: "Јули", 8: "Август",
        9: "Септември", 10: "Октомври", 11: "Ноември", 12: "Декември",
    }
    period_label = f"{month_names.get(month, str(month))} {year}"

    header_table = Table(
        [[
            Paragraph("EVN Macedonia", header_style),
            Paragraph(f"СМЕТКА ЗА ЕЛЕКТРИЧНА ЕНЕРГИЈА\n{period_label}", subheader_style),
        ]],
        colWidths=[9 * cm, 9 * cm],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _EVN_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5 * cm))

    # -----------------------------------------------------------------------
    # Consumer info block
    # -----------------------------------------------------------------------
    consumer_name = cfg.get(CONF_CONSUMER_NAME, "—")
    consumer_address = cfg.get(CONF_CONSUMER_ADDRESS, "—")
    meter_number = cfg.get(CONF_METER_NUMBER, "—")
    period_start = data.get(DATA_PERIOD_START, "—")
    days_in_period = data.get(DATA_DAYS_IN_PERIOD, 0)

    info_data = [
        [
            Paragraph("ПОТРОШУВАЧ", section_title_style),
            Paragraph("ПРЕСМЕТКОВЕН ПЕРИОД", section_title_style),
        ],
        [
            Paragraph(f"<b>{consumer_name}</b><br/>{consumer_address}<br/>Број на бројило: {meter_number}", body_style),
            Paragraph(f"Почеток: {period_start}<br/>Денови: {days_in_period}", body_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[9 * cm, 9 * cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _EVN_BLUE),
        ("BACKGROUND", (0, 1), (-1, 1), _LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 1), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4 * cm))

    # -----------------------------------------------------------------------
    # Bill detail table
    # -----------------------------------------------------------------------
    vt_block1_rate = cfg.get(CONF_VT_BLOCK1_RATE, DEFAULT_VT_BLOCK1_RATE)
    vt_block2_rate = cfg.get(CONF_VT_BLOCK2_RATE, DEFAULT_VT_BLOCK2_RATE)
    vt_block3_rate = cfg.get(CONF_VT_BLOCK3_RATE, DEFAULT_VT_BLOCK3_RATE)
    vt_block4_rate = cfg.get(CONF_VT_BLOCK4_RATE, DEFAULT_VT_BLOCK4_RATE)
    nt_rate = cfg.get(CONF_NT_RATE, DEFAULT_NT_RATE)
    td_rate = cfg.get(CONF_TD_RATE, DEFAULT_TD_RATE)
    vat_pct = cfg.get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT)
    network_access = cfg.get(CONF_NETWORK_ACCESS, DEFAULT_NETWORK_ACCESS)
    municipal_tax = cfg.get(CONF_MUNICIPAL_TAX, DEFAULT_MUNICIPAL_TAX)

    def row(label, kwh, rate, mkd, bold=False, bg=None):
        s = bold_style if bold else body_style
        return [
            Paragraph(label, s),
            Paragraph(kwh, s),
            Paragraph(rate, s),
            Paragraph(mkd, s),
        ]

    col_w = [8.5 * cm, 2.5 * cm, 3 * cm, 3.5 * cm]

    bill_header = [
        Paragraph("Опис", section_title_style),
        Paragraph("kWh", section_title_style),
        Paragraph("MKD/kWh", section_title_style),
        Paragraph("MKD", section_title_style),
    ]

    b1_kwh = data.get(DATA_VT_BLOCK1_KWH, 0.0)
    b2_kwh = data.get(DATA_VT_BLOCK2_KWH, 0.0)
    b3_kwh = data.get(DATA_VT_BLOCK3_KWH, 0.0)
    b4_kwh = data.get(DATA_VT_BLOCK4_KWH, 0.0)
    nt_kwh = data.get(DATA_NT_CONSUMPTION, 0.0)
    total_kwh = data.get(DATA_TOTAL_CONSUMPTION, 0.0)

    bill_rows = [
        bill_header,
        row("ВТ 1 до 210", _kwh(b1_kwh), f"× {_rate(vt_block1_rate)} =", _mkd(data.get(DATA_VT_BLOCK1_COST, 0))),
        row("ВТ 211 до 630", _kwh(b2_kwh), f"× {_rate(vt_block2_rate)} =", _mkd(data.get(DATA_VT_BLOCK2_COST, 0))),
        row("ВТ 631 до 1050", _kwh(b3_kwh), f"× {_rate(vt_block3_rate)} =", _mkd(data.get(DATA_VT_BLOCK3_COST, 0))),
        row("ВТ повеќе од 1050", _kwh(b4_kwh), f"× {_rate(vt_block4_rate)} =", _mkd(data.get(DATA_VT_BLOCK4_COST, 0))),
        row("ВТ вкупно", _kwh(data.get(DATA_VT_CONSUMPTION, 0)), "", _mkd(data.get(DATA_VT_COST, 0)), bold=True),
        row("НТ", _kwh(nt_kwh), f"× {_rate(nt_rate)} =", _mkd(data.get(DATA_NT_COST, 0))),
        row("ВТ + НТ вкупно", _kwh(total_kwh), "", _mkd(data.get(DATA_ENERGY_COST, 0)), bold=True),
        row("Пристап до мрежа", "1", f"× {_mkd(network_access)} =", _mkd(network_access)),
        row("Пренос + Дистрибуција", _kwh(total_kwh), f"× {_rate(td_rate)} =", _mkd(data.get(DATA_TD_COST, 0))),
        row("Надоместок за пренос и дистрибуција вкупно", "", "", _mkd(data.get(DATA_TD_COST, 0) + network_access)),
        row(f"Ел. енергија + пренос + дистрибуција (без ДДВ)", "", "", _mkd(data.get(DATA_SUBTOTAL, 0)), bold=True),
        row(f"ДДВ ({data.get(DATA_SUBTOTAL, 0):.0f} × {vat_pct:.0f}%)", "", "", _mkd(data.get(DATA_VAT_AMOUNT, 0))),
        row("Вкупно со ДДВ", "", "", _mkd(data.get(DATA_TOTAL_WITH_VAT, 0)), bold=True),
        row("Комунална такса", "", "", _mkd(data.get(DATA_MUNICIPAL_TAX, municipal_tax))),
    ]

    # Total row (highlighted)
    total_row = [
        Paragraph("ВКУПНО СО КОМУНАЛНА ТАКСА", bold_style),
        Paragraph(_kwh(total_kwh), bold_style),
        Paragraph("", bold_style),
        Paragraph(_mkd(data.get(DATA_TOTAL_COST, 0)), bold_style),
    ]

    bill_table_data = bill_rows + [total_row]
    bill_table = Table(bill_table_data, colWidths=col_w)

    ts = TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), _EVN_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Align numbers right
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        # Alternating row backgrounds
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, _LIGHT_GRAY]),
        # Total row
        ("BACKGROUND", (0, -1), (-1, -1), _EVN_YELLOW),
        ("TEXTCOLOR", (0, -1), (-1, -1), _DARK_GRAY),
        # Subtotal rows (VT vkupno, VT+NT, subtotal, total+VAT)
        ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
        ("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"),
        ("FONTNAME", (0, 11), (-1, 11), "Helvetica-Bold"),
        ("FONTNAME", (0, 12), (-1, 12), "Helvetica-Bold"),  # VAT line
        ("FONTNAME", (0, 13), (-1, 13), "Helvetica-Bold"),  # total+VAT
        # Grid
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
    bill_table.setStyle(ts)
    story.append(bill_table)
    story.append(Spacer(1, 0.5 * cm))

    # -----------------------------------------------------------------------
    # Footer note
    # -----------------------------------------------------------------------
    story.append(Paragraph(
        f"* Сметката е генерирана автоматски од Home Assistant - Energy Invoice MK  |  "
        f"Период: {period_start}  |  Генерирана: {date.today().isoformat()}",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=7, textColor=colors.grey),
    ))

    doc.build(story)
