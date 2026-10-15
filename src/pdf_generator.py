"""PDF invoice generation using ReportLab (fully offline)."""
from __future__ import annotations

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import utils

ACCENT = colors.HexColor("#1f6feb")
DARK = colors.HexColor("#1f2430")
MUTED = colors.HexColor("#6b7280")
LIGHT = colors.HexColor("#f3f4f6")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Issuer", parent=ss["Normal"], fontSize=9, textColor=MUTED, leading=12, alignment=TA_RIGHT))
    ss.add(ParagraphStyle("IssuerName", parent=ss["Normal"], fontSize=13, textColor=DARK, leading=16,
                          alignment=TA_RIGHT, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("DocTitle", parent=ss["Normal"], fontSize=22, textColor=DARK, leading=26,
                          fontName="Helvetica-Bold", spaceAfter=2))
    ss.add(ParagraphStyle("DocSub", parent=ss["Normal"], fontSize=10, textColor=MUTED, leading=13))
    ss.add(ParagraphStyle("Block", parent=ss["Normal"], fontSize=9.5, textColor=DARK, leading=13))
    ss.add(ParagraphStyle("BlockBold", parent=ss["Normal"], fontSize=10, textColor=DARK, leading=14,
                          fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("Label", parent=ss["Normal"], fontSize=8, textColor=MUTED, leading=11))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=8, textColor=MUTED, leading=11))
    ss.add(ParagraphStyle("CellRight", parent=ss["Normal"], fontSize=9.5, textColor=DARK, leading=12,
                          alignment=TA_RIGHT))
    ss.add(ParagraphStyle("CellRightBold", parent=ss["Normal"], fontSize=10, textColor=DARK, leading=13,
                          alignment=TA_RIGHT, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("CellHead", parent=ss["Normal"], fontSize=8.5, textColor=colors.white, leading=11,
                          fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("CellHeadR", parent=ss["Normal"], fontSize=8.5, textColor=colors.white, leading=11,
                          fontName="Helvetica-Bold", alignment=TA_RIGHT))
    ss.add(ParagraphStyle("TotalLabel", parent=ss["Normal"], fontSize=10, textColor=DARK, leading=14,
                          alignment=TA_RIGHT))
    ss.add(ParagraphStyle("GrandLabel", parent=ss["Normal"], fontSize=12, textColor=DARK, leading=16,
                          alignment=TA_RIGHT, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("GrandValue", parent=ss["Normal"], fontSize=12, textColor=ACCENT, leading=16,
                          alignment=TA_RIGHT, fontName="Helvetica-Bold"))
    return ss


def _address_lines(entity: dict) -> list[str]:
    lines = []
    name = (entity.get("company") or "").strip() if entity.get("type") == "business" else ""
    display = name or (entity.get("name") or entity.get("company") or "").strip()
    if display:
        lines.append(display)
    if entity.get("type") == "business" and (entity.get("contact") or "").strip():
        lines.append(entity["contact"].strip())
    street = (entity.get("street") or "").strip()
    if street:
        lines.append(street)
    line3 = " ".join(p for p in [(entity.get("postal") or "").strip(), (entity.get("city") or "").strip()] if p)
    if line3:
        lines.append(line3)
    country = (entity.get("country") or "").strip()
    if country and country.lower() not in ("deutschland", "germany", "de"):
        lines.append(country)
    if (entity.get("vat") or "").strip():
        lines.append(f"{entity['vat']}")
    return lines


def generate_invoice_pdf(invoice: dict, config, tr, output_path: str) -> str:
    """Create the PDF for *invoice* and return the file path."""
    ss = _styles()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    issuer = config.get("issuer", default={}) or {}
    bank = config.get("bank", default={}) or {}
    tax = config.get("tax", default={}) or {}
    currency = config.get("currency", default="€")
    client = invoice.get("client") or {}
    totals = invoice.get("totals") or {"net": 0, "vat": 0, "gross": 0, "vat_rate": 0}
    vat_rate = totals.get("vat_rate", 0)
    lang = tr.lang

    def money(v):
        return utils.format_amount(v, currency)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{tr.t('pdf.title')} {invoice.get('number','')}",
        author=issuer.get("name", ""),
    )
    story: list = []

    # ---------------------------------------------------------- header
    logo_path = (issuer.get("logo") or "").strip()
    logo_flow = None
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path)
            ratio = img.imageHeight / float(img.imageWidth or 1)
            img.drawWidth = 45 * mm
            img.drawHeight = max(10 * mm, 45 * mm * ratio)
            logo_flow = img
        except Exception:
            logo_flow = None

    issuer_lines = [
        (issuer.get("name") or "").strip(),
        (issuer.get("street") or "").strip(),
        " ".join(p for p in [(issuer.get("postal") or "").strip(), (issuer.get("city") or "").strip()] if p),
        (issuer.get("email") or "").strip(),
        (issuer.get("phone") or "").strip(),
    ]
    issuer_lines = [ln for ln in issuer_lines if ln]
    issuer_par = [Paragraph(issuer_lines[0], ss["IssuerName"])] if issuer_lines else []
    issuer_par += [Paragraph(ln, ss["Issuer"]) for ln in issuer_lines[1:]]

    left_cell = logo_flow if logo_flow else Paragraph("", ss["DocSub"])
    header = Table([[left_cell, issuer_par]], colWidths=[80 * mm, 90 * mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceAfter=8))
    story.append(Spacer(1, 6))

    # ---------------------------------------------------------- title + recipient
    story.append(Paragraph(tr.t("pdf.title"), ss["DocTitle"]))
    story.append(Paragraph(f"{tr.t('pdf.invoice_no')} {invoice.get('number','')}", ss["DocSub"]))
    story.append(Spacer(1, 12))

    recipient_lines = _address_lines(client)
    if not recipient_lines:
        recipient_lines = ["—"]
    recip_flow = [Paragraph(tr.t("pdf.bill_to"), ss["Label"])]
    recip_flow += [Paragraph(ln, ss["Block"]) for ln in recipient_lines]

    meta_rows = [
        [Paragraph(tr.t("pdf.date"), ss["Label"]), Paragraph(utils.format_date(invoice.get("issue_date"), lang), ss["Block"])],
        [Paragraph(tr.t("pdf.service_date"), ss["Label"]), Paragraph(utils.format_date(invoice.get("service_date"), lang), ss["Block"])],
        [Paragraph(tr.t("pdf.due_date"), ss["Label"]), Paragraph(utils.format_date(invoice.get("due_date"), lang), ss["Block"])],
    ]
    meta_table = Table(meta_rows, colWidths=[30 * mm, 40 * mm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    two_col = Table([[recip_flow, meta_table]], colWidths=[95 * mm, 75 * mm])
    two_col.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(two_col)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------- items table
    head = [
        Paragraph(tr.t("pdf.col.pos"), ss["CellHead"]),
        Paragraph(tr.t("pdf.col.description"), ss["CellHead"]),
        Paragraph(tr.t("pdf.col.qty"), ss["CellHeadR"]),
        Paragraph(tr.t("pdf.col.unit"), ss["CellHead"]),
        Paragraph(tr.t("pdf.col.unit_price"), ss["CellHeadR"]),
        Paragraph(tr.t("pdf.col.total"), ss["CellHeadR"]),
    ]
    data = [head]
    for idx, item in enumerate(invoice.get("items", []), start=1):
        qty = float(item.get("quantity") or 0)
        price = float(item.get("unit_price") or 0)
        line = qty * price
        data.append([
            Paragraph(str(idx), ss["Block"]),
            Paragraph((item.get("description") or "").replace("\n", "<br/>"), ss["Block"]),
            Paragraph(utils.format_qty(qty), ss["CellRight"]),
            Paragraph(item.get("unit") or "", ss["Block"]),
            Paragraph(money(price), ss["CellRight"]),
            Paragraph(money(line), ss["CellRight"]),
        ])

    col_widths = [12 * mm, 78 * mm, 16 * mm, 18 * mm, 24 * mm, 22 * mm]
    items_table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
    ]
    for r in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    items_table.setStyle(TableStyle(style))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------- totals
    totals_rows = [
        [Paragraph(tr.t("pdf.subtotal"), ss["TotalLabel"]), Paragraph(money(totals["net"]), ss["CellRight"])],
    ]
    if abs(float(vat_rate)) > 1e-9:
        totals_rows.append([
            Paragraph(tr.t("pdf.vat", rate=utils.format_qty(vat_rate)), ss["TotalLabel"]),
            Paragraph(money(totals["vat"]), ss["CellRight"]),
        ])
    totals_rows.append([
        Paragraph(tr.t("pdf.grand_total"), ss["GrandLabel"]),
        Paragraph(money(totals["gross"]), ss["GrandValue"]),
    ])
    totals_table = Table(totals_rows, colWidths=[120 * mm, 50 * mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -2), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 3),
        ("TOPPADDING", (0, -1), (-1, -1), 7),
        ("LINEABOVE", (0, -1), (-1, -1), 1, DARK),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 8))

    if config.is_kleinunternehmer():
        story.append(Paragraph(tr.t("pdf.kleinunternehmer"), ss["Small"]))
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------- payment info
    pay_lines = []
    if (bank.get("iban") or "").strip():
        pay_lines.append(f"{tr.t('pdf.pay_until', date=utils.format_date(invoice.get('due_date'), lang))}")
        parts = []
        if (bank.get("bank_name") or "").strip():
            parts.append(f"{tr.t('pdf.bank')}: {bank['bank_name']}")
        parts.append(f"{tr.t('pdf.iban')}: {bank['iban']}")
        if (bank.get("bic") or "").strip():
            parts.append(f"{tr.t('pdf.bic')}: {bank['bic']}")
        pay_lines.append(" · ".join(parts))
    if pay_lines:
        story.append(Paragraph(tr.t("pdf.payment_info"), ss["BlockBold"]))
        for ln in pay_lines:
            story.append(Paragraph(ln, ss["Block"]))
        story.append(Spacer(1, 8))

    if (invoice.get("notes") or "").strip():
        story.append(Paragraph((invoice["notes"]).replace("\n", "<br/>"), ss["Block"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph(tr.t("pdf.thank_you"), ss["Block"]))

    # ---------------------------------------------------------- footer
    footer_bits = []
    if (issuer.get("name") or "").strip():
        footer_bits.append(issuer["name"].strip())
    if (tax.get("tax_number") or "").strip():
        footer_bits.append(f"{tr.t('pdf.tax_number')}: {tax['tax_number']}")
    if (tax.get("vat_id") or "").strip():
        footer_bits.append(f"{tr.t('pdf.vat_id')}: {tax['vat_id']}")

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d1d5db"))
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 11 * mm, " · ".join(footer_bits))
        canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"{tr.t('pdf.title')} {invoice.get('number','')}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output_path
