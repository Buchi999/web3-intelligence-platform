"""
PDF report rendering using ReportLab's platypus layer. ReportLab chosen
over WeasyPrint for Windows install reliability (no system GTK dependency).
"""
import io
import re
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports.builder import CollectionReportData, WalletReportData

MAX_TABLE_ROWS = 15

_styles = getSampleStyleSheet()
_title_style = ParagraphStyle("ReportTitle", parent=_styles["Title"], fontSize=20, spaceAfter=4)
_subtitle_style = ParagraphStyle("ReportSubtitle", parent=_styles["Normal"], fontSize=10, textColor=colors.grey)
_heading_style = ParagraphStyle("SectionHeading", parent=_styles["Heading2"], spaceBefore=16, spaceAfter=6)
_body_style = _styles["Normal"]
_note_style = ParagraphStyle("Note", parent=_styles["Normal"], fontSize=8, textColor=colors.grey, spaceBefore=4)
_table_header_bg = colors.HexColor("#1f2937")

_NARRATIVE_HEADERS = {
    "executive summary",
    "wallet behavior",
    "portfolio analysis",
    "nft analysis",
    "transaction behavior",
    "risk indicators",
    "notable patterns",
    "data limitations",
    "recommended further investigation",
}


def _render_ai_narrative(text: str) -> list:
    """Render LLM output as flowables. Text is escaped (never trusted as
    markup) since it's model-generated, not authored by this codebase.

    Models commonly wrap headers in markdown bold (**Executive Summary**)
    even when instructed to use plain headers — strip those markers before
    matching against known section names, and convert any remaining inline
    **bold** markdown to real bold rendering rather than leaving literal
    asterisks visible in the output.
    """
    flowables = []
    for raw_line in text.split("\n"):
        line = raw_line.strip().lstrip("#").strip()
        if not line:
            continue

        dewrapped = line.strip("*").strip().rstrip(":")
        if dewrapped.lower() in _NARRATIVE_HEADERS:
            flowables.append(Paragraph(f"<b>{escape(dewrapped)}</b>", _body_style))
            continue

        escaped = escape(line)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
        flowables.append(Paragraph(escaped, _body_style))
    return flowables


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M UTC") if dt else "Unknown"


def _fmt_num(value: float | None, decimals: int = 4) -> str:
    return f"{value:,.{decimals}f}" if value is not None else "Data unavailable"


def _fmt_pct(value: float | None) -> str:
    return f"{value:.2f}%" if value is not None else "Data unavailable"


def _standard_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), _table_header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _limitations_section(limitations: list[str]):
    story = [Paragraph("Data Limitations", _heading_style)]
    items = [ListItem(Paragraph(limit, _body_style)) for limit in limitations]
    story.append(ListFlowable(items, bulletType="bullet", start="•"))
    return story


def _methodology_section(data_sources: list[str]):
    story = [Paragraph("Methodology &amp; Data Sources", _heading_style)]
    story.append(
        Paragraph(
            "This report is generated from publicly available blockchain data. Heuristic "
            "classifications and derived metrics are pattern-based observations, not "
            "definitive claims, and are labeled with their confidence level throughout. "
            "No private keys, seed phrases, or non-public data were accessed to produce "
            "this report.",
            _body_style,
        )
    )
    story.append(Spacer(1, 4))
    items = [ListItem(Paragraph(src, _body_style)) for src in data_sources]
    story.append(ListFlowable(items, bulletType="bullet", start="•"))
    return story


def render_wallet_report_pdf(data: WalletReportData) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    story = []

    story.append(Paragraph("Web3 Wallet Intelligence Report", _title_style))
    story.append(Paragraph(f"Wallet: {data.address}", _subtitle_style))
    story.append(Paragraph(f"Generated: {_fmt_dt(data.generated_at)}", _subtitle_style))
    story.append(Spacer(1, 12))

    tx = data.transactions
    if data.ai_narrative:
        story.append(Paragraph("Executive Summary &amp; Analysis (AI-Generated Narrative)", _heading_style))
        story.append(
            Paragraph(
                "Generated by an LLM from only the structured data in this report — see Methodology.",
                _note_style,
            )
        )
        story.extend(_render_ai_narrative(data.ai_narrative))
    else:
        summary_parts = [
            f"This wallet holds {_fmt_num(data.balance.native_balance_native_unit, 4)} ETH "
            f"(confidence: {data.balance.meta.confidence.value})."
        ]
        if tx.total_transactions:
            summary_parts.append(
                f"Across the most recent {tx.total_transactions} transactions retrieved, "
                f"it was active on {tx.active_days} distinct day(s), with "
                f"{tx.incoming_count} incoming and {tx.outgoing_count} outgoing transfers."
            )
        else:
            summary_parts.append("No transaction history was found for this address.")
        if data.tokens.holdings:
            summary_parts.append(
                f"The wallet holds {len(data.tokens.holdings)} distinct ERC-20 token(s); "
                f"portfolio concentration is computed by {data.tokens.concentration_method.value.replace('_', ' ')}."
            )
        if data.nfts.total_nft_count:
            summary_parts.append(
                f"It holds {data.nfts.total_nft_count} NFT(s) across "
                f"{data.nfts.distinct_collections_count} collection(s)."
            )
        story.append(Paragraph("Executive Summary (Automated Summary — not AI-generated)", _heading_style))
        story.append(Paragraph(" ".join(summary_parts), _body_style))

    story.append(Paragraph("Transaction Analysis", _heading_style))
    tx_rows = [
        ["Metric", "Value"],
        ["Total transactions (this page)", str(tx.total_transactions)],
        ["Incoming / Outgoing", f"{tx.incoming_count} / {tx.outgoing_count}"],
        ["Active days", str(tx.active_days)],
        ["Avg. transactions/day", _fmt_num(tx.average_transactions_per_day, 2)],
        ["Avg. transaction value (ETH)", _fmt_num(tx.average_transaction_value_native, 4)],
        [
            "Largest transaction",
            f"{_fmt_num(tx.largest_transaction.value_native, 4)} ETH ({tx.largest_transaction.hash[:12]}...)"
            if tx.largest_transaction
            else "N/A",
        ],
        ["Dormant periods (30+ days)", str(len(tx.dormant_periods))],
    ]
    story.append(Table(tx_rows, style=_standard_table_style(), hAlign="LEFT", colWidths=[220, 280]))
    if tx.data_note:
        story.append(Paragraph(tx.data_note, _note_style))

    story.append(Paragraph("Token Portfolio", _heading_style))
    if data.tokens.holdings:
        story.append(
            Paragraph(
                f"Concentration method: {data.tokens.concentration_method.value} — "
                f"top asset: {_fmt_pct(data.tokens.top_asset_pct)}"
                + (f" — total value: ${_fmt_num(data.tokens.total_value_usd, 2)}" if data.tokens.total_value_usd else ""),
                _body_style,
            )
        )
        rows = [["Symbol", "Balance", "USD Value", "% of Portfolio"]]
        for h in data.tokens.holdings[:MAX_TABLE_ROWS]:
            rows.append(
                [
                    h.symbol or "?",
                    _fmt_num(h.balance_normalized, 4),
                    f"${_fmt_num(h.usd_value, 2)}" if h.usd_value is not None else "N/A",
                    _fmt_pct(h.pct_of_portfolio),
                ]
            )
        story.append(Table(rows, style=_standard_table_style(), hAlign="LEFT", colWidths=[100, 130, 130, 140]))
        if len(data.tokens.holdings) > MAX_TABLE_ROWS:
            story.append(Paragraph(f"...and {len(data.tokens.holdings) - MAX_TABLE_ROWS} more token(s).", _note_style))
    else:
        story.append(Paragraph("No ERC-20 token holdings found for this address.", _body_style))
    if data.tokens.data_note:
        story.append(Paragraph(data.tokens.data_note, _note_style))

    story.append(Paragraph("NFT Holdings", _heading_style))
    if data.nfts.collections:
        story.append(
            Paragraph(
                f"{data.nfts.total_nft_count} NFT(s) across {data.nfts.distinct_collections_count} "
                f"collection(s). Top collection concentration: {_fmt_pct(data.nfts.top_collection_pct)}.",
                _body_style,
            )
        )
        rows = [["Collection Address", "Count", "% of NFTs Held"]]
        for c in data.nfts.collections[:MAX_TABLE_ROWS]:
            rows.append([c.collection_address, str(c.count), _fmt_pct(c.pct_of_portfolio)])
        story.append(Table(rows, style=_standard_table_style(), hAlign="LEFT", colWidths=[280, 80, 140]))
        if len(data.nfts.collections) > MAX_TABLE_ROWS:
            story.append(
                Paragraph(f"...and {len(data.nfts.collections) - MAX_TABLE_ROWS} more collection(s).", _note_style)
            )
    else:
        story.append(Paragraph("No NFT holdings found for this address.", _body_style))

    if data.nfts.data_note:
        story.append(Paragraph(data.nfts.data_note, _note_style))

    if data.classifications:
        story.append(Paragraph("Behavior Classification", _heading_style))
        story.append(
            Paragraph(
                "Heuristic patterns only — not definitive claims. A wallet may match "
                "several classifications at once.",
                _note_style,
            )
        )
        for c in data.classifications:
            story.append(Paragraph(f"<b>{c.label}</b> — confidence: {c.confidence:.0f}%", _body_style))
            items = [ListItem(Paragraph(f, _body_style)) for f in c.factors]
            story.append(ListFlowable(items, bulletType="bullet", start="•"))
            story.append(Spacer(1, 4))

    if data.risk:
        story.append(Paragraph("Risk Indicators", _heading_style))
        story.append(Paragraph(f"<b>Risk Score: {data.risk.score}/100</b>", _body_style))
        if data.risk.factors:
            items = [ListItem(Paragraph(f"{f.description} (+{f.points})", _body_style)) for f in data.risk.factors]
            story.append(ListFlowable(items, bulletType="bullet", start="•"))
        else:
            story.append(Paragraph("No risk factors were identified.", _body_style))
        story.append(Paragraph(data.risk.disclaimer, _note_style))

    story.extend(_limitations_section(data.limitations))
    story.extend(_methodology_section(data.data_sources))

    doc.build(story)
    return buffer.getvalue()


def render_collection_report_pdf(data: CollectionReportData) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    story = []

    story.append(Paragraph("NFT Collection Holder Intelligence Report", _title_style))
    story.append(Paragraph(f"Contract: {data.address}", _subtitle_style))
    if data.metadata.name:
        story.append(Paragraph(f"Name: {data.metadata.name}", _subtitle_style))
    story.append(Paragraph(f"Generated: {_fmt_dt(data.generated_at)}", _subtitle_style))
    story.append(Spacer(1, 12))

    h = data.holders
    summary = (
        f"This collection has {h.total_holders} holder(s) across {h.total_supply_held} token(s) held. "
        f"The top 10 holders control {_fmt_pct(h.top_10_concentration_pct)} of supply, and the top 50 "
        f"control {_fmt_pct(h.top_50_concentration_pct)}. Average holding is "
        f"{_fmt_num(h.average_holdings, 2)} token(s) per holder (median: {_fmt_num(h.median_holdings, 1)})."
        if h.total_holders
        else "No holder data was found for this collection."
    )
    story.append(Paragraph("Executive Summary (Automated Summary — not AI-generated)", _heading_style))
    story.append(Paragraph(summary, _body_style))

    if h.total_holders:
        story.append(Paragraph("Holder Distribution", _heading_style))
        rows = [["Holdings", "Number of Holders"]] + [[d.label, str(d.holder_count)] for d in h.distribution]
        story.append(Table(rows, style=_standard_table_style(), hAlign="LEFT", colWidths=[250, 250]))

        story.append(Paragraph("Top Holders", _heading_style))
        rows = [["Address", "Quantity", "% of Supply"]]
        for t in h.top_holders:
            rows.append([t.address, str(t.quantity), _fmt_pct(t.pct_of_supply)])
        story.append(Table(rows, style=_standard_table_style(), hAlign="LEFT", colWidths=[260, 100, 140]))

    if h.data_note:
        story.append(Paragraph(h.data_note, _note_style))

    story.extend(_limitations_section(data.limitations))
    story.extend(_methodology_section(data.data_sources))

    doc.build(story)
    return buffer.getvalue()