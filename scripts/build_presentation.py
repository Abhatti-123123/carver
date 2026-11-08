"""Build the 45-minute presentation.

Usage: python scripts/build_presentation.py carver_presentation.pptx
Numbers come from scripts/run_results.py (futures), scripts/crypto_run.py and scripts/dltm_app1.py.
"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
INK = RGBColor(0x1A, 0x1A, 0x19)
GRAY = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x8A, 0x89, 0x84)
RULE = RGBColor(0xDD, 0xDC, 0xD6)
PANEL = RGBColor(0xF3, 0xF4, 0xF6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLUE = RGBColor(0x2A, 0x78, 0xD6)     # categorical slot 1
ORANGE = RGBColor(0xEB, 0x68, 0x34)   # categorical slot 2
FONT = "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W = 13.333
slide_no = 0


def text(slide, x, y, w, h, s, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP):
    tf = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0)
    for i, line in enumerate(s.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, FONT
    return tf


def bullets(slide, x, y, w, h, items, size=16, gap=8):
    """items: str or (str, level). Level-1 items render smaller and indented."""
    tf = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0)
    for i, it in enumerate(items):
        s, lvl = (it, 0) if isinstance(it, str) else it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        # real bullet with hanging indent so wrapped lines align with the text
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(Inches(0.28 + 0.3 * lvl)))
        pPr.set("indent", str(-Inches(0.28)))
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•" if lvl == 0 else "–"})
        pPr.append(bu)
        r = p.add_run()
        r.text = s
        r.font.name = FONT
        r.font.size = Pt(size if lvl == 0 else size - 2)
        r.font.color.rgb = INK if lvl == 0 else GRAY
    return tf


def rect(slide, x, y, w, h, fill, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def footer(slide):
    global slide_no
    slide_no += 1
    text(slide, 0.6, 7.05, 8, 0.3, "Risk-aware systematic portfolio  ·  Angad Bhatti", 10, MUTED)
    text(slide, W - 1.6, 7.05, 1.0, 0.3, str(slide_no), 10, MUTED, align=PP_ALIGN.RIGHT)


def content_slide(title, kicker=None):
    s = prs.slides.add_slide(BLANK)
    if kicker:
        text(s, 0.6, 0.35, 12, 0.35, kicker.upper(), 12, BLUE, bold=True)
    text(s, 0.6, 0.65, 12.1, 0.8, title, 30, NAVY, bold=True)
    rect(s, 0.6, 1.45, 12.13, 0.02, RULE)
    footer(s)
    return s


def section_slide(num, title, sub):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, 7.5, NAVY)
    text(s, 0.9, 2.4, 11, 0.6, num, 20, RGBColor(0x8F, 0xB8, 0xEC), bold=True)
    text(s, 0.9, 2.95, 11.5, 1.2, title, 44, WHITE, bold=True)
    text(s, 0.9, 4.15, 11.5, 1.0, sub, 20, RGBColor(0xC9, 0xD3, 0xE2))
    global slide_no
    slide_no += 1
    return s


def table(slide, x, y, w, rows, col_w=None, size=14, row_h=0.42, first_col_bold=True,
          highlight_col=None):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y),
                                 Inches(w), Inches(row_h * len(rows)))
    tbl = shp.table
    tbl.first_row = True
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(cw)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(row_h)
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = NAVY
            elif highlight_col is not None and c == highlight_col:
                cell.fill.fore_color.rgb = RGBColor(0xE6, 0xEF, 0xFA)
            else:
                cell.fill.fore_color.rgb = WHITE if r % 2 else PANEL
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = Inches(0.1)
            tf = cell.text_frame
            tf.word_wrap = True
            tf.paragraphs[0].text = ""
            run = tf.paragraphs[0].add_run()
            run.text = val
            run.font.name, run.font.size = FONT, Pt(size)
            run.font.bold = r == 0 or (c == 0 and first_col_bold)
            run.font.color.rgb = WHITE if r == 0 else INK
            tf.paragraphs[0].alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
    return tbl


def stat_tile(slide, x, y, w, h, value, label, sub=None):
    rect(slide, x, y, w, h, PANEL)
    rect(slide, x, y, 0.06, h, BLUE)
    text(slide, x + 0.3, y + 0.2, w - 0.4, 0.75, value, 36, NAVY, bold=True)
    text(slide, x + 0.3, y + 0.95, w - 0.4, 0.4, label, 14, GRAY, bold=True)
    if sub:
        text(slide, x + 0.3, y + 1.3, w - 0.4, 0.4, sub, 11, MUTED)


def style_chart(chart, legend=True):
    chart.font.name, chart.font.size = FONT, Pt(12)
    chart.font.color.rgb = GRAY
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(12)
    va = chart.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RULE
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(11)
    ca = chart.category_axis
    ca.format.line.color.rgb = RULE
    ca.tick_labels.font.size = Pt(12)

LIGHT = RGBColor(0xC9, 0xD3, 0xE2)
TINT = RGBColor(0xE6, 0xEF, 0xFA)


def bar_chart(s, x, y, w, h, cats, vals, title, fmt_axis='0.0;-0.0;0', fmt_lbl='+0.00;-0.00;;', horizontal=True,
              gap=60, label_size=11):
    """Gains blue, losses orange: two series with overlap 100 so each bar keeps one fill."""
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("Gain", [v if v >= 0 else None for v in vals])
    cd.add_series("Loss", [v if v < 0 else None for v in vals])
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    ch = s.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    style_chart(ch, legend=False)
    if title:
        ch.has_title = True
        ch.chart_title.text_frame.text = title
        run = ch.chart_title.text_frame.paragraphs[0].runs[0]
        run.font.size, run.font.bold, run.font.color.rgb = Pt(13), True, NAVY
    if horizontal:
        ch.category_axis.reverse_order = True
    ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    ch.value_axis.tick_labels.number_format = fmt_axis
    ch.value_axis.tick_labels.number_format_is_linked = False
    plot = ch.plots[0]
    plot.gap_width, plot.overlap = gap, 100
    if fmt_lbl:
        plot.has_data_labels = True
        plot.data_labels.number_format, plot.data_labels.number_format_is_linked = fmt_lbl, False
        plot.data_labels.font.size, plot.data_labels.font.color.rgb = Pt(label_size), INK
        plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    for ser, col in zip(plot.series, (BLUE, ORANGE)):
        ser.invert_if_negative = False
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = col
    return ch


# =========================================================================
# 1. Title
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, 7.5, NAVY)
rect(s, 0.9, 2.2, 0.08, 2.3, BLUE)
text(s, 1.2, 1.95, 11.5, 1.7, "Building a Risk-Aware Systematic Portfolio:\nFrom Market Signals to Regime Intelligence",
     38, WHITE, bold=True)
text(s, 1.2, 3.85, 11.5, 0.9, "A Carver-style futures portfolio across 31 markets, 2005–2025, with a long-memory "
     "regime layer", 20, LIGHT)
text(s, 1.2, 5.6, 11, 0.4, "Angad Bhatti", 18, WHITE, bold=True)
slide_no += 1
notes(s, "[0:30] Introduce yourself and the project: a replication and extension of Robert Carver's "
         "Advanced Futures Trading Strategies, built on public Yahoo Finance data, extended with a regime layer from my "
         "long-memory research. The question running through the talk: how do you build a portfolio that controls "
         "its risk first, and then lets market regimes decide how much risk to take?")

# 2. Thesis + agenda
s = content_slide("The thesis: risk first, then regimes decide how much", "Why we are here")
bullets(s, 0.6, 1.8, 6.4, 4.8, [
    "Any single market or signal has long losing stretches: diversify and size by risk first",
    "Combining lowly-correlated markets raises Sharpe without raising risk",
    "Regime signals then set how much risk to take: trend state per market, market memory for the whole book",
    "Every layer is judged by what it adds over the simpler version, not by its own backtest",
], 18, 12)
rect(s, 7.6, 1.8, 5.13, 4.7, PANEL)
text(s, 7.9, 2.0, 4.6, 0.4, "AGENDA", 13, BLUE, bold=True)
for i, a in enumerate(["Universe & system", "Results", "How the portfolio is built", "Regime intelligence & robustness",
                       "Limitations & recommendations", "Personal analysis"]):
    yy = 2.55 + i * 0.62
    text(s, 7.9, yy, 0.5, 0.5, str(i + 1), 20, BLUE, bold=True)
    text(s, 8.4, yy + 0.03, 4.1, 0.5, a, 18, INK)
notes(s, "[1:30] Set up the argument. The goal was never to maximise backtest return; it was to build a portfolio "
         "that is risk-aware by construction. First the risk machinery: volatility scaling, diversification, "
         "covariance-aware sizing. Then regime intelligence: trend state decides how much risk each market gets, "
         "and market-wide memory flags when the whole book faces a fat left tail. Walk through the agenda: "
         "approach, results, then limitations.")

# 3. Universe
s = content_slide("The universe: 31 liquid futures across 6 asset classes", "1 · Universe")
classes = [
    ("Equity indices", "Growth & risk appetite; the strongest long-run drift in the book", "ES · NQ · YM · Nikkei"),
    ("Rates / bonds", "Usually rally in risk-off; four curve points give different duration", "ZT · ZF · ZN · ZB"),
    ("Energy", "Supply shocks and inflation, unrelated to equity earnings", "CL · RBOB · NG · HO"),
    ("Metals", "Gold as a crisis hedge, copper as an industrial-growth proxy", "GC · SI · HG · PA"),
    ("Grains & softs", "Weather and harvest driven: the most idiosyncratic block", "ZC · ZW · ZS · ZM · KC · CC · OJ"),
    ("Livestock", "Own supply cycle; almost uncorrelated with financial markets", "LE · GF · HE"),
]
gx = 0.12
cw = (12.13 - gx * (len(classes) - 1)) / len(classes)
for i, (name, why, ex) in enumerate(classes):
    x = 0.6 + i * (cw + gx)
    rect(s, x, 1.8, cw, 3.55, PANEL)
    rect(s, x, 1.8, cw, 0.07, BLUE)
    text(s, x + 0.2, 2.05, cw - 0.4, 0.5, name, 18, NAVY, bold=True)
    text(s, x + 0.2, 2.6, cw - 0.4, 1.7, why, 14, GRAY)
    text(s, x + 0.2, 4.3, cw - 0.4, 0.3, "EXAMPLES", 10, MUTED, bold=True)
    text(s, x + 0.2, 4.6, cw - 0.4, 0.6, ex, 13, INK, bold=True)
rect(s, 0.6, 5.7, 12.13, 0.95, TINT)
text(s, 0.85, 5.7, 11.7, 0.95,
     "Selection rule: deep liquidity, history back to 2005, and drivers that differ across classes — "
     "so correlations stay low when it matters most.", 15, NAVY, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[2:30] The foundation of diversification. Explain each class's economic driver and why it behaves "
         "differently: we pick markets for different reasons to move. Data: daily front-month futures from Yahoo "
         "Finance; the return on each contract-roll day is neutralised using an exchange roll calendar so roll "
         "gaps are not booked as P&L.")

# 4. System overview
s = content_slide("The system in one picture: five steps, one risk budget", "1 · Universe & system")
steps = [("S1", "Buy & hold", "Baseline: one fixed position per market"),
         ("S2", "Constant vol target", "Size each market to a fixed risk"),
         ("S3", "Variable vol target", "Blend fast & slow vol to adapt"),
         ("S4", "Portfolio risk parity", "Correlation-aware: diversification core"),
         ("S6/7", "Trend strength", "Size longs by trend strength; no shorts")]
gap = 0.146
bw = (12.13 - gap * (len(steps) - 1)) / len(steps)
for i, (tag, name, desc) in enumerate(steps):
    x = 0.6 + i * (bw + gap)
    core = tag == "S4"
    rect(s, x, 1.75, bw, 2.75, NAVY if core else PANEL)
    text(s, x + 0.18, 1.9, bw - 0.3, 0.5, tag, 24, WHITE if core else BLUE, bold=True)
    text(s, x + 0.18, 2.5, bw - 0.3, 0.9, name, 16, WHITE if core else NAVY, bold=True)
    text(s, x + 0.18, 3.35, bw - 0.3, 1.1, desc, 13, LIGHT if core else GRAY)
rect(s, 0.6, 4.7, 12.13, 0.04, BLUE)
text(s, 0.6, 4.82, 4, 0.4, "Single-market risk control", 13, GRAY, bold=True)
text(s, 4.7, 4.82, 4, 0.4, "Portfolio diversification", 13, BLUE, bold=True, align=PP_ALIGN.CENTER)
text(s, 8.73, 4.82, 4, 0.4, "Signal-aware sizing", 13, GRAY, bold=True, align=PP_ALIGN.RIGHT)
rect(s, 0.6, 5.45, 12.13, 1.3, PANEL)
for i, (k, d) in enumerate([
        ("Sharpe ratio", "Return per unit of risk, no risk-free deduction: futures returns are already excess returns."),
        ("Vol target", "The risk dial: scales every position up or down. Changes return and drawdown, not Sharpe."),
        ("Final system", "S6/7 on top of S4, 31 markets; settings chosen on 2005–16 data only.")]):
    x = 0.85 + i * 4.0
    text(s, x, 5.58, 3.7, 0.35, k.upper(), 11, BLUE, bold=True)
    text(s, x, 5.9, 3.7, 0.8, d, 12, INK)
notes(s, "[2:30] Give the audience the vocabulary before the numbers. S1–S3 control risk one market at a time. "
         "S4 is where diversification becomes explicit through the covariance matrix. S6/7 decides how much "
         "of that diversified risk budget to deploy, based on trend strength. Every layer is a buy-and-hold variant: the "
         "book stays invested and layers only change how much is held. Carry strategies (S8+) were left out for "
         "lack of data.")

# =========================================================================
section_slide("02", "Results", "31-market futures, 2005–2025, roll-adjusted, after 5 bp costs")

# 5. Results at a glance
s = content_slide("Results at a glance", "2 · Results")
for i, (v, l, sub) in enumerate([("1.04", "Sharpe, 20 years", "2005 – mid-2025, +881%"),
                                  ("1.48", "Sharpe since 2020", "CAGR 19.8%, max DD –13%"),
                                  ("–26.9%", "Max drawdown", "20 years, at 11% volatility"),
                                  ("1.04", "Crypto Sharpe", "Risk-scaled portfolio, untuned")]):
    stat_tile(s, 0.6 + i * 3.08, 1.75, 2.9, 1.75, v, l, sub)
table(s, 0.6, 3.85, 12.13, [
    ("", "Full 2005–25", "In-sample 05–16", "Out-of-sample 17–25", "Since 2020", "Crypto 2023–25"),
    ("Total return", "+881%", "+195%", "+232%", "+169%", "+161%"),
    ("CAGR", "11.8%", "9.4%", "15.2%", "19.8%", "25.6%"),
    ("Volatility", "11.3%", "10.7%", "12.1%", "12.7%", "25.1%"),
    ("Sharpe", "1.04", "0.89", "1.23", "1.48", "1.04"),
    ("Max drawdown", "–26.9%", "–20.3%", "–26.9%", "–13.0%", "–21.4%"),
], col_w=[1.83, 2.06, 2.06, 2.06, 2.06, 2.06], size=13, row_h=0.42, highlight_col=1)
text(s, 0.6, 6.55, 12.1, 0.35, "Sharpe uses a 0% risk-free rate: futures prices already embed the financing cost, so "
     "futures P&L is an excess return; the cash posted as margin earns the risk-free rate on top.", 11, MUTED)
notes(s, "[2:30] Lead with the headline: 31 futures, 2005 to mid-2025, roll days neutralised, 5 bp per trade. "
         "Sharpe 1.04 over twenty years and 1.48 since 2020. Settings were chosen on 2005–2016 only, and the "
         "untouched 2017–2025 window did better (1.23), so this is not a fitted number. Crypto column: the risk-scaled "
         "portfolio (S4) on 12 liquid coins, 2023–2025, with the futures parameters unchanged. Footnote: no risk-free deduction "
         "because the futures price already embeds financing (F ≈ S × (1 + r − yield)).")

# 6. Strategy ladder
s = content_slide("Each layer changes something different", "2 · Results")
table(s, 0.6, 1.75, 12.13, [
    ("Strategy", "Measured as", "Sharpe", "Since 2020", "CAGR", "Volatility", "Max drawdown"),
    ("S1  Buy & hold", "average single market", "0.30", "—", "3.6%", "24.1%", "–62%"),
    ("S2  Constant vol target", "average single market", "0.29", "—", "4.4%", "21.4%", "–63%"),
    ("S3  Variable vol target", "average single market", "0.23", "—", "2.7%", "25.9%", "–68%"),
    ("S4  Portfolio risk parity", "portfolio", "0.73", "1.06", "13.3%", "20.0%", "–49.5%"),
    ("S6/7  S4 + trend-strength sizing", "portfolio (final)", "1.04", "1.48", "11.8%", "11.3%", "–26.9%"),
], col_w=[3.03, 2.3, 1.2, 1.4, 1.3, 1.4, 1.5], size=13, row_h=0.47, highlight_col=2)
bullets(s, 0.6, 5.2, 12.1, 1.7, [
    "A single market earns Sharpe ≈ 0.3 however it is sized — the portfolio step more than doubles it",
    "Trend-strength sizing on the risk-scaled portfolio lifts Sharpe to 1.04 and halves the drawdown",
], 15, 8)
notes(s, "[2:30] The ladder. S1–S3 are single-market strategies, so we show the average market: about 0.3 "
         "whichever way it is sized. S4 combines the same markets with correlation-aware sizing and more than "
         "doubles Sharpe — that is diversification. Trend-strength sizing on top of it is the "
         "step that lifts the book to 1.04 while cutting the drawdown from about -50% to -27%: it holds most risk "
         "in markets that are trending and very little in those that are not.")

# 7. Out-of-sample
s = content_slide("Out of sample: chosen on 2005–16, stronger after", "2 · Results")
stat_tile(s, 0.6, 1.8, 3.0, 1.75, "+232%", "Total return", "Jan 2017 – Jun 2025")
stat_tile(s, 3.8, 1.8, 3.0, 1.75, "15.2%", "CAGR", "at 12.1% volatility")
stat_tile(s, 0.6, 3.75, 3.0, 1.75, "1.23", "Sharpe ratio", "0.05% cost per trade")
stat_tile(s, 3.8, 3.75, 3.0, 1.75, "–26.9%", "Max drawdown", "Jan 2018 – Mar 2020")
bullets(s, 7.3, 1.85, 5.4, 4.6, [
    "Covariance windows, leverage smoothing, trend overlay and forecast scaling were compared on 2005–16 only",
    "The winner was then run once on 2017–25 and not changed afterwards",
    "Since 2020: Sharpe 1.48, CAGR 19.8%, through COVID and the 2022 rate shock",
], 16, 12)
notes(s, "[1:30] The honesty slide. Settings were selected on the first twelve years. The out-of-sample window "
         "has a higher Sharpe (1.23 vs 0.89), helped by strong trends in commodities and equities after 2020.")

# 8. Vol target dial
s = content_slide("Vol target is a leverage dial, not an alpha source", "2 · Results")
cd = CategoryChartData()
cd.categories = ["CAGR", "Volatility", "Max drawdown (abs.)"]
for lab, vals in (("20% target", (11.8, 11.3, 26.9)), ("40% target", (23.3, 22.6, 48.0)),
                  ("60% target", (34.2, 34.0, 64.0))):
    cd.add_series(lab, vals)
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.2), Inches(5.1), cd).chart
style_chart(ch)
ch.value_axis.maximum_scale = 70
ch.value_axis.tick_labels.number_format = '0"%"'
ch.value_axis.tick_labels.number_format_is_linked = False
plot = ch.plots[0]
plot.gap_width, plot.overlap = 70, -8
plot.has_data_labels = True
plot.data_labels.number_format, plot.data_labels.number_format_is_linked = '0"%"', False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
plot.data_labels.font.size, plot.data_labels.font.color.rgb = Pt(11), INK
for ser, col in zip(plot.series, (BLUE, ORANGE, NAVY)):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = col
table(s, 8.2, 1.85, 4.53, [("Target", "20%", "40%", "60%"), ("Sharpe", "1.04", "1.04", "1.04"),
                           ("Turnover", "213", "426", "638")], col_w=[1.33, 1.07, 1.07, 1.06], size=13, row_h=0.42)
bullets(s, 8.2, 3.4, 4.53, 3.3, [
    "Sharpe identical at every target: the engine is the same",
    "Doubling the target doubles CAGR (12% → 23%) and drawdown (–27% → –48%)",
    "Realised vol sits near half the target: trend sizing holds less than full risk most of the time",
], 14, 8)
notes(s, "[1:30] Same system, only the vol target changes. Sharpe stays 1.04. Return and drawdown scale together. "
         "This is why we optimise Sharpe first and choose the dial second. Turnover is total position change in "
         "units of capital over twenty years.")

# 9. Distribution & tails
s = content_slide("Return distribution: fat tails, negative skew", "2 · Results")
table(s, 0.6, 1.8, 5.9, [
    ("Distribution", "Value"), ("Mean / median daily return", "0.047% / 0.049%"), ("Daily volatility", "0.71%"),
    ("Skewness", "–0.70"), ("Excess kurtosis", "6.02"), ("Worst / best day", "–7.7% / +4.1%"),
    ("VaR95 / VaR99", "–1.08% / –2.14%"), ("CVaR95 / CVaR99", "–1.74% / –2.87%"),
], col_w=[3.5, 2.4], size=13, row_h=0.45)
table(s, 6.83, 1.8, 5.9, [
    ("Risk & payoff", "Value"), ("Annualised Sortino", "1.30"), ("Tail ratio (95th / 5th pct.)", "1.11"),
    ("Hit rate", "55.1%"), ("Avg up / down day", "+0.49% / –0.50%"), ("Profit factor", "1.21"),
    ("Jarque-Bera", "p ≈ 0 (non-normal)"), ("ACF(1)", "0.069 (weak)"),
], col_w=[3.5, 2.4], size=13, row_h=0.45)
text(s, 0.6, 5.65, 12.1, 1.1,
     "Slow trend sizing steps aside in grinding bear markets but cannot react to overnight gaps, so the worst days "
     "are sudden shocks — hence negative skew. Sortino (1.30) above Sharpe (1.04) shows downside volatility is "
     "contained; fat tails mean risk is judged with VaR/CVaR, not variance alone.", 15, INK)
notes(s, "[1:30] Daily returns of the final system. Skew -0.7 and kurtosis 6: the left tail comes from gap events "
         "like March 2020, before a slow trend signal can respond. Hit rate 55% with symmetric up and down days — "
         "a small daily edge, compounded across 31 markets. Transition: can we see the bad tail coming?")

# 10a. Market memory predicts the left tail
s = content_slide("Market memory predicts when our left tail is fat", "2 · Results")
table(s, 0.6, 1.8, 6.3, [
    ("Market memory state", "Months", "Skew", "Worst month", "Sharpe"),
    ("Low", "55", "–0.43", "–4.4%", "1.82"),
    ("Mid", "53", "–0.73", "–6.9%", "0.67"),
    ("High", "41", "–1.42", "–11.2%", "0.77"),
], col_w=[2.1, 1.0, 1.0, 1.2, 1.0], size=13, row_h=0.5)
text(s, 0.6, 3.85, 6.3, 0.4, "Next month of the final system, 2013–25, by market memory at month-end.", 11, MUTED)
bullets(s, 0.6, 4.35, 6.3, 2.5, [
    "State = average dLTM (d*) across ~460 S&P 500 stocks, vs its own 1-year average; thresholds use only past data",
    "High memory has the most negative skew under all three definitions, and without the COVID months",
    "It predicts tail risk, not returns: Sharpe is not monotonic across states",
], 13, 7)
cd = CategoryChartData()
cd.categories = ["Low memory", "Mid", "High memory"]
for lab, vals in (("Detrended (headline)", (-0.43, -0.73, -1.42)), ("Expanding terciles", (-0.22, -0.68, -1.07)),
                  ("Rolling 3-year terciles", (-0.43, -0.68, -1.51))):
    cd.add_series(lab, vals)
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.2), Inches(1.65), Inches(5.53), Inches(5.1), cd).chart
style_chart(ch)
ch.has_title = True
ch.chart_title.text_frame.text = "Next-month skew of the final system"
run = ch.chart_title.text_frame.paragraphs[0].runs[0]
run.font.size, run.font.bold, run.font.color.rgb = Pt(13), True, NAVY
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.value_axis.minimum_scale, ch.value_axis.maximum_scale = -1.6, 0
ch.value_axis.tick_labels.number_format = '0.0;-0.0;0'
ch.value_axis.tick_labels.number_format_is_linked = False
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.HIGH
plot = ch.plots[0]
plot.gap_width, plot.overlap = 70, -8
plot.has_data_labels = True
plot.data_labels.number_format, plot.data_labels.number_format_is_linked = '+0.00;-0.00;0', False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
plot.data_labels.font.size, plot.data_labels.font.color.rgb = Pt(10), INK
for ser, col in zip(plot.series, (BLUE, ORANGE, NAVY)):
    ser.invert_if_negative = False
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = col
notes(s, "[2:30] The previous slide showed our weakness: negative skew from sudden crashes. Can we see the bad tail "
         "coming? This is where my dLTM research comes in. dLTM estimates long memory in a price series from the tail "
         "of its autocorrelation function; my research found that high-memory regimes are followed by more negative "
         "skew. Here I average each S&P 500 stock's walk-forward d* into one market memory state, measure it against "
         "its own one-year average so a slow drift cannot drive the result, and bucket it into thirds using only "
         "past data. In high-memory months, the next month of our futures book has skew of -1.42 versus -0.43 when "
         "memory is low, and the worst month is -11% versus -4%. The ranking holds under all three definitions and "
         "with the COVID months removed. The honest framing: it tells you when the left tail is fat, not where "
         "returns go — and tail risk is exactly what a risk-scaled system needs to know.")

# 10. Regimes
s = content_slide("By regime: steps aside in slow bears, caught by sudden crashes", "2 · Results")
yr = [14.5, 14.2, 24.1, 3.6, 3.9, 24.0, 0.8, -4.7, 29.5, 22.2, -6.5, -4.1, 36.8, -9.9, 0.4, 11.6, 40.0, 18.5, 7.1, 30.4, 3.9]
ch = bar_chart(s, 0.6, 1.65, 7.4, 5.0, [f"{y % 100:02d}" if y < 2025 else "25*" for y in range(2005, 2026)], yr,
               "Calendar-year return (%)", fmt_axis="0", fmt_lbl=None, horizontal=False, gap=40)
text(s, 0.6, 6.62, 7.4, 0.3, "* 2025 = January to June.", 11, MUTED)
table(s, 8.3, 1.75, 4.43, [
    ("Episode", "Return"), ("GFC (2008 – Mar 09)", "+2.4%"), ("Euro crisis (H2 2011)", "–5.2%"),
    ("Commodity bust (Jul 14 – Feb 16)", "–8.5%"), ("COVID crash (Feb – Apr 20)", "–9.5%"),
    ("Reflation (2021)", "+40.0%"), ("Rate hikes (2022)", "+18.5%"),
], col_w=[3.03, 1.4], size=12, row_h=0.42)
bullets(s, 8.3, 4.95, 4.43, 1.9, [
    "2008: +3.6% while the S&P 500 fell 37% — trend sizing had already cut risk",
    "Worst drawdown: Jan 2018 – Mar 2020, choppy markets then COVID",
    "3-year rolling Sharpe: –0.29 (Nov 2020) to 2.07 (Jul 2023)",
], 13, 6)
notes(s, "[2:00] Slow bear markets (2008, the 2014–16 commodity bust) are where trend sizing earns its keep: "
         "positions shrink as trends roll over. Sudden crashes like COVID hit before the signal reacts. Inflation "
         "and reflation pay: 2021 +40%, 2022 +18.5% when a 60/40 portfolio lost. Judge it over full cycles.")

# 11. Overlay alpha tests
s = content_slide("Does trend sizing add value? Regress, don't eyeball", "2 · Results")
table(s, 0.6, 1.85, 12.13, [
    ("Test (monthly returns, 2005–25)", "Alpha / month", "t-stat", "p-value", "Beta", "R²", "Read-out"),
    ("Trend strength (S6/7) vs risk-scaled portfolio (S4)", "0.44%", "3.13", "0.002", "0.45", "0.58",
     "Significant alpha"),
    ("Same test, since 2020", "0.57%", "3.00", "0.003", "0.55", "0.71", "Holds out of sample"),
], col_w=[3.6, 1.6, 1.1, 1.1, 1.0, 1.0, 2.73], size=14, row_h=0.6)
bullets(s, 0.6, 4.0, 12.1, 2.8, [
    "About 5% a year of alpha on top of the risk-scaled portfolio, at less than half its market exposure (beta 0.45)",
    "Risk scaling is the frame; the trend signal is the alpha placed inside it",
    "Allowing shorts on the same signals cut Sharpe in every test (1.02 → 0.63): size longs, don't short",
    "Method matters: a backtest win is not evidence until it is regressed against the simpler alternative",
], 16, 10)
notes(s, "[2:00] Regress monthly returns of the final system on the risk-scaled portfolio it is built on. Alpha "
         "0.44% a month (about 5% a year), t = 3.13 with HAC standard errors, beta only 0.45: trend-strength sizing is a "
         "genuine alpha layered on top of the risk machinery, and it holds since 2020 (t = 3.00). Lesson: judge each layer by "
         "incremental alpha against the simpler version, not by its standalone backtest.")

# =========================================================================
section_slide("03", "How the portfolio is built",
              "Each layer in detail: from one market to a risk-balanced, trend-aware portfolio")

# 13. S1-S3
s = content_slide("S1–S3: control risk one market at a time", "3 · How")
for i, (tag, h, items) in enumerate([
        ("S1", "Buy & hold", ["Fixed long position per market", "Benchmark: high vol, low Sharpe, deep drawdowns",
                              "Shows why risk-adjusting is essential"]),
        ("S2", "Constant vol target", ["Position = 20% target ÷ 20-day realised vol", "Capped at 5× notional",
                                       "Stable risk profile across regimes"]),
        ("S3", "Variable vol target", ["Target = 0.7 × fast vol + 0.3 × slow vol (EWMA)",
                                       "More risk in calm, less in turbulence", "Avoids overreacting to spikes"])]):
    x = 0.6 + i * 4.11
    rect(s, x, 1.8, 3.9, 3.7, PANEL)
    text(s, x + 0.3, 2.0, 3.3, 0.5, tag, 22, BLUE, bold=True)
    text(s, x + 0.3, 2.55, 3.3, 0.5, h, 19, NAVY, bold=True)
    bullets(s, x + 0.3, 3.25, 3.35, 2.2, items, 15, 12)
text(s, 0.6, 5.8, 12.1, 0.9, "Making each market's risk comparable is the prerequisite for combining them — "
     "otherwise the most volatile market dominates the book.", 16, INK)
notes(s, "[1:30] Quick pass. These make each market's risk comparable — a prerequisite for combining them. Without "
         "it, natural gas would dominate the book. On its own, none of them beats Sharpe 0.3 per market.")

# 14. S4
s = content_slide("S4: portfolio risk parity — the diversification core", "3 · How")
for i, (n, d) in enumerate([
        ("1", "Weight each market by inverse blended volatility (70% fast / 30% slow EWMA), capped at 7"),
        ("2", "Estimate covariance from a 50/50 blend of 60-day and 120-day windows"),
        ("3", "Rescale the whole book to the vol target: √(wᵀΣw) → 20%"),
        ("4", "Smooth that scale factor (20-day half-life) so leverage is not slashed at the bottom of a shock")]):
    yy = 1.85 + i * 1.12
    rect(s, 0.6, yy, 0.75, 0.85, BLUE)
    text(s, 0.6, yy, 0.75, 0.85, n, 24, WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.6, yy + 0.05, 5.4, 0.85, d, 16, INK, anchor=MSO_ANCHOR.MIDDLE)
rect(s, 7.5, 1.85, 5.23, 4.35, PANEL)
text(s, 7.8, 2.05, 4.7, 0.4, "WHY IT WORKS", 12, BLUE, bold=True)
bullets(s, 7.8, 2.5, 4.7, 3.6, [
    "Correlated markets share one risk budget instead of doubling it",
    "Uncorrelated markets let total size grow at the same portfolio risk",
    "Lifts Sharpe from ≈ 0.3 per market to 0.73 for the portfolio",
    "Daily re-levering cut leverage hardest right before rebounds; smoothing recovered part of that",
], 15, 10)
notes(s, "[2:00] The core slide for the how. Walk the four steps. Step 4 came from a diagnostic: with daily "
         "re-levering, leverage was lowest right after crashes (e.g. December 2008), exactly when the following "
         "months paid best. Smoothing the scale factor and using longer covariance windows improved in-sample "
         "Sharpe.")

# 15. Concept: more assets
s = content_slide("Past ~30 markets, more assets add no profit", "3 · How")
table(s, 0.6, 1.75, 7.3, [
    ("Final system, 2005–25", "21", "31 (base)", "35 + bonds", "35 no bonds"),
    ("What was added", "—", "+10 drift sectors", "+5 rates, +3 FX", "+8 commodities"),
    ("Avg correlation", "0.08", "0.07", "0.06", "0.08"),
    ("Effective bets", "18.1", "27.7", "29.7", "33.1"),
    ("Avg market Sharpe", "0.35", "0.36", "0.34", "0.35"),
    ("Diversification gain", "×2.50", "×2.92", "×2.99", "×3.04"),
    ("Portfolio Sharpe", "0.88", "1.04", "1.01", "1.05"),
    ("Max drawdown", "–24.1%", "–26.9%", "–28.7%", "–24.6%"),
], col_w=[2.0, 1.05, 1.45, 1.4, 1.4], size=12, row_h=0.47, highlight_col=2)
rect(s, 0.6, 5.7, 7.3, 1.05, TINT)
text(s, 0.85, 5.7, 6.9, 1.05, "Portfolio Sharpe ≈ average market Sharpe × diversification gain,\n"
     "gain ≈ √( N ÷ (1 + (N – 1) ρ ) ) — it flattens once ρ is already low.", 14, NAVY, anchor=MSO_ANCHOR.MIDDLE)
bar_chart(s, 8.2, 1.65, 4.53, 5.1, ["Metals", "Equity", "Livestock", "Ags & softs", "Dairy", "Energy", "Rates", "FX"],
          [0.61, 0.44, 0.31, 0.31, 0.23, 0.05, 0.04, -0.05], "Sharpe by asset class")
notes(s, "[2:30] The key concept slide. Same final system, four universes. 21 to 31 markets adds +0.16 Sharpe: the "
         "ten new markets are drift sectors with their own edge. Going to 35 adds nothing. Adding bonds and "
         "currencies gives the lowest correlation of all, but they carry no edge for a long-biased trend book, so "
         "Sharpe slips to 1.01. Adding eight more commodities raises effective bets to 33, but several are near-"
         "copies (mini crude, mini gas) or thin (butter, milk), so Sharpe only matches the base. With average "
         "correlation already near 0.07, the formula says the gain from markets 31 to 35 is about 4% at most. "
         "Diversification multiplies an edge; it cannot create one. If asked whether the universe was picked after "
         "seeing results: the 35-market test is what revealed the principle, but the principle is economic — a "
         "long-biased book only earns where markets drift — which is why the deck shows all three universes, not "
         "just the winner.")

# 16. S6/7
s = content_slide("S6/7: deploy the risk budget where trends are", "3 · How")
rect(s, 0.6, 1.8, 12.13, 3.7, PANEL)
text(s, 0.9, 2.0, 5.3, 0.5, "S6/7", 22, BLUE, bold=True)
text(s, 0.9, 2.55, 11.5, 0.5, "Trend-strength sizing on the risk-scaled portfolio", 19, NAVY, bold=True)
bullets(s, 0.9, 3.2, 11.5, 2.3, [
    "Forecast = slow EWMAC(64,256) ÷ price volatility, scaled ×1.9, capped at ±20",
    "Position = S4 risk-scaled position × forecast ÷ 10: more risk where trends are strong",
    "Long-only: the position grows with trend strength and fades to ~0 as the trend dies — no shorts",
    "Re-sized only when the forecast moves > 5%, so turnover stays low",
], 16, 10)
text(s, 0.6, 5.8, 12.1, 0.9, "Size by volatility first, then by trend strength: 0.44% a month of alpha over the "
     "risk-scaled portfolio (t = 3.13).", 16, INK)
notes(s, "[2:00] Trend sizing decides how much of the diversified risk budget each market gets. Strength sizing scales each long by how strong and persistent its trend is; when the trend turns "
         "negative the position has already faded to almost nothing, so the book effectively steps aside without "
         "ever shorting. Allowing shorts on the same signal cut Sharpe in every test (1.02 to 0.63).")

# =========================================================================
section_slide("04", "Regime intelligence & robustness", "Does the machinery transfer, and how should regime signals be used?")

# 18. Crypto
s = content_slide("Robustness: same parameters, new universe", "4 · Robustness")
rect(s, 0.6, 1.75, 12.13, 0.75, TINT)
text(s, 0.85, 1.75, 11.7, 0.75, "The risk-scaled portfolio (S4) with its futures parameters, applied to 12 liquid crypto coins — "
     "no re-fitting.", 17, NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
table(s, 0.6, 2.8, 6.6, [
    ("S4 risk-scaled portfolio", "Futures (2005–25)", "Crypto (2023–25)"),
    ("Total return", "+1,204%", "+161%"), ("CAGR", "13.3%", "25.6%"), ("Volatility", "20.0%", "25.1%"),
    ("Sharpe", "0.73", "1.04"), ("Sortino", "1.03", "1.47"), ("Max drawdown", "–49.5%", "–21.4%"),
    ("Tail ratio", "1.01", "1.08"),
], col_w=[2.2, 2.2, 2.2], size=13, row_h=0.42, highlight_col=2)
text(s, 0.6, 6.25, 6.6, 0.4, "Crypto: 12 spot coins (BTC, ETH, SOL…), Jan 2023 – Nov 2025.", 11, MUTED)
bullets(s, 7.6, 2.85, 5.13, 3.9, [
    "Crypto Sharpe 1.04 with the identical risk machinery, never fitted to crypto",
    "Very different volatility and correlation structure — the risk machinery still held",
    "Short sample (under 3 years): evidence of portability, not a track record",
    "Takeaway: the edge lives in the risk machinery, not in fitted parameters",
], 15, 12)
notes(s, "[2:00] Robustness evidence. The risk-scaled portfolio (S4) with exactly the futures parameters — "
         "60/120-day covariance, smoothed leverage, 20% target — on 12 spot coins, Jan 2023 to Nov 2025. Crypto has "
         "a very different vol and correlation structure and nothing was retuned, yet Sharpe is 1.04. Be upfront "
         "that 2.9 years is short; the slow trend-strength layer needs more history than that to warm up, which "
         "is why crypto is shown with the risk machinery alone.")

# 19. Using dLTM
s = content_slide("Using it: de-risk the futures book, tilt the stock book", "4 · Regime intelligence")
text(s, 0.6, 1.75, 5.9, 0.5, "Futures: halve the book when memory is high", 18, NAVY, bold=True)
table(s, 0.6, 2.35, 5.9, [
    ("Final system, 2013–25", "As is", "De-risked"),
    ("Sharpe", "1.14", "1.19"), ("Skew", "–0.85", "–0.56"), ("Max drawdown", "–26.9%", "–16.9%"),
    ("CAGR", "13.2%", "11.9%"), ("Volatility", "11.5%", "9.9%"),
], col_w=[2.5, 1.7, 1.7], size=13, row_h=0.45, highlight_col=2)
text(s, 0.6, 5.1, 5.9, 0.9, "All three state definitions: drawdown –27% → –14% to –17%, Sharpe +0.03 to +0.12. "
     "Lower CAGR only because the book runs less risk on average.", 12, MUTED)
text(s, 6.83, 1.75, 5.9, 0.5, "Stocks: tilt toward high-memory names", 18, NAVY, bold=True)
table(s, 6.83, 2.35, 5.9, [
    ("30 S&P 500 stocks, 2011–25", "Sharpe", "Volatility"),
    ("Final system (base)", "0.783", "13.2%"),
    ("×1.5 / ×0.5 by memory (levered)", "0.794", "17.1%"),
    ("Same, leverage-neutral tilt", "0.809", "13.7%"),
], col_w=[3.3, 1.3, 1.3], size=13, row_h=0.45, highlight_col=1)
bullets(s, 6.83, 4.3, 5.9, 2.5, [
    "Leverage-neutral: multipliers rescaled to average 1 each day — same risk, higher Sharpe (DM +2.13, p = 0.03)",
    "The signal works without adding leverage",
    "Base is 0.78, not 1.04: 30 US stocks diversify far less than 31 futures",
], 13, 7)
notes(s, "[2:00] Two ways to use the memory signal. In the futures book, as a risk switch: halve exposure the day after "
         "market memory enters its top third. Sharpe is kept or slightly better, skew improves from -0.85 to -0.56 and "
         "the maximum drawdown falls from -27% to -17%; the lower CAGR is just less risk on average. In a stock book, "
         "where each name has its own d*, as a tilt: more risk in high-memory names, less in low-memory names, "
         "rescaled every day so total risk is unchanged. Sharpe rises from 0.783 to 0.809 at the same volatility, "
         "DM p = 0.03, so the gain is the signal, not leverage. The 30-stock universe is the final system on 3 names "
         "per sector, rebuilt by a fixed rule because the original list was not kept; its base Sharpe is lower "
         "than the futures because single stocks all load on the S&P.")

# =========================================================================
section_slide("05", "Limitations & recommendations", "What the backtest cannot tell us, and how to run it live")

# 21. Limitations
two_col_title = "Limitations: what could make these numbers wrong"
s = content_slide(two_col_title, "5 · Limitations")
text(s, 0.6, 1.75, 5.85, 0.5, "Data and costs", 19, NAVY, bold=True)
rect(s, 0.6, 2.25, 0.9, 0.05, BLUE)
bullets(s, 0.6, 2.45, 5.85, 4.5, [
    "Public data by design (Yahoo front-month series); roll gaps neutralised from an exchange roll calendar "
    "rather than full contract-level back-adjustment",
    "Flat 5 bp cost on every market: too harsh for Treasuries, too light for thin softs and dairy",
    "Only markets Yahoo still lists back to 2005 — survivorship, and no non-US equity indices",
    "Crypto sample is under three years",
], 14, 7)
text(s, 6.88, 1.75, 5.85, 0.5, "Method and model", 19, NAVY, bold=True)
rect(s, 6.88, 2.25, 0.9, 0.05, BLUE)
bullets(s, 6.88, 2.45, 5.85, 4.5, [
    "Settings are fixed once on 2005–16 rather than re-estimated as new data arrive",
    "Long-biased: sudden gap-down crashes hit before slow trends react (COVID –9.5%, skew –0.7)",
    "dLTM evidence: 13 years; high-memory months mostly in 2014–20",
    "No carry strategies; no slippage or capacity model",
], 14, 7)
notes(s, "[2:30] Volunteer the weaknesses before the panel finds them. The biggest two: data quality (Yahoo, "
         "approximate roll handling), chosen because the work must use public data, and costs (a flat 5 bp with no "
         "per-market spreads or contract rounding). Expect the question of why 1.04 beats real trend-following funds. "
         "The SG Trend Index has a long-run Sharpe of about 0.42-0.47 since 2000, net of fees (ReSolve Asset "
         "Management; Price Action Lab, data to 2023); a fee-free replication of the same index reaches about 0.72 "
         "(ReSolve). This backtest is gross of fees and leaves out per-market costs and capacity, so the gap is mostly "
         "fees, costs and scale, not a better signal.")

# 22. Recommendations
s = content_slide("Recommendations", "5 · Recommendations")
recs = [("Size longs by trend strength", "it earns the alpha over the risk-scaled portfolio (t = 3.13); shorting the same signal cut Sharpe"),
        ("Add markets that bring their own edge", "21 → 31 lifted Sharpe 0.88 → 1.04; going to 35 added nothing"),
        ("Pick the vol target after Sharpe", "Sharpe is 1.04 at every target; 40% nearly doubles drawdown"),
        ("Smooth leverage, blend covariance", "avoids cutting risk at the bottom and oversizing in calm"),
        ("Cut risk when market memory is high", "drawdown –27% → –17% with Sharpe kept"),
        ("Warm up before trading", "hold initial weights until the 120-day lookbacks are populated")]
for i, (h, d) in enumerate(recs):
    yy = 1.8 + i * 0.84
    rect(s, 0.6, yy, 0.07, 0.75, BLUE)
    text(s, 0.95, yy, 4.6, 0.75, h, 18, NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 5.6, yy, 7.1, 0.75, d, 16, GRAY, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "[1:00] Practical takeaways for running the system live.")

# =========================================================================
section_slide("06", "Personal analysis", "My research notes and experiment observations from building the system")


def two_col(title, lh, litems, rh, ritems, note, size=14):
    s = content_slide(title, "6 · Personal analysis")
    text(s, 0.6, 1.75, 5.85, 0.5, lh, 19, NAVY, bold=True)
    rect(s, 0.6, 2.25, 0.9, 0.05, BLUE)
    bullets(s, 0.6, 2.45, 5.85, 4.5, litems, size, 7)
    text(s, 6.88, 1.75, 5.85, 0.5, rh, 19, NAVY, bold=True)
    rect(s, 6.88, 2.25, 0.9, 0.05, BLUE)
    bullets(s, 6.88, 2.45, 5.85, 4.5, ritems, size, 7)
    notes(s, note)


two_col("Measuring risk honestly",
        "Data and volatility", [
            "Roll gaps are not P&L: neutralise them before measuring returns",
            "Back-filling mini prices before 2019 is safe when testing micro contracts",
            "Equal-weight std: a large return leaving the window fakes a vol jump → use EWMA (λ ≈ 0.6, Carver p.99)",
            "Vol clusters short-run, mean-reverts long-run → blend horizons so crisis weights stay sane",
            "Annualising assumes independent days; autocorrelation makes it spurious, but usable here",
        ],
        "Evaluation metrics", [
            "Futures prices embed financing, so futures P&L is already an excess return — no rf deduction in Sharpe",
            "Sharpe penalises upside volatility too",
            "Sortino isolates the downside and flags negative skew — report both",
            "Prefer average drawdown to a single worst max drawdown",
            "Returns are fat-tailed: model them that way; use percentile ratios for tails",
        ],
        "[1:15] From my notes file. These choices are why the risk numbers in the results section can be trusted.")

two_col("Sizing, leverage and signals",
        "Leverage and risk budget", [
            "Leverage ratio = total risk appetite ÷ risk of one contract = portfolio loss % ÷ 1-contract loss %",
            "Contract leverage = notional per contract ÷ capital; leverage = capital wiped ÷ move in contract",
            "Riskier contracts carry higher initial and variation margin — more cash to enter and to hold",
            "Kelly-optimal risk ≈ Sharpe; target about half of it",
            "Mean-variance optimisation only matters without leverage to tune risk",
        ],
        "Signals and sizing", [
            "Size by volatility, not by confidence score — better Sharpe throughout",
            "MACD-type trends work on the long side: close longs, don't short",
            "Cap extreme indicator values (reversal risk); min–max scale when extremes are not absurd",
            "Indicators must be risk- and price-adjusted to compare across history",
            "Hold initial weights or don't trade until lookbacks are populated",
        ],
        "[1:15] From my notes file: the mechanics behind the sizing layers in S2–S7.", size=13)

two_col("Market behaviour, skew and strategy selection",
        "Market behaviour and skew", [
            "Equities and commodities bounce sharply after strong negative trends; not vice versa",
            "VIX falls sharply after strong positive trends; not vice versa",
            "Negative skew = frequent small gains, rare large losses — it should demand higher return",
            "Goal: identify negative skew in advance (→ led to the dLTM work)",
            "Major risk: the largest positions build in the quiet before a crisis",
        ],
        "Choosing strategies honestly", [
            "Picking the backtest winner is fitting the sample — a regime may have favoured it",
            "Start blended; slowly cut weight on inefficient components",
            "If it can't be explained logically and financially, treat it as data mining",
            "Measure real value by regressing against the simpler baseline for alpha",
            "Higher Sharpe beats higher return: it can be levered safely",
        ],
        "[1:00] The skew point connects directly to the dLTM extension shown earlier.")

two_col("Experiment log: what the backtests showed",
        "Observations from the code", [
            "Portfolio risk scaling was the first step to lift Sharpe well above single markets",
            "Raising the vol target lifted returns and CAGR sharply; Sharpe barely moved",
            "Normalising weights so |w| sums to 1 during warm-up was crucial",
            "Daily re-levering hurt; smoothing the scale factor helped",
            "Long-only trend-strength sizing beat a binary trend filter and every variant that shorted",
        ],
        "Implementation assumptions", [
            "Capital = price × multiplier",
            "Every layer is a buy-and-hold variant: a zero signal means hold, not exit",
            "Rolls neutralised from an exchange roll calendar",
            "Carry strategies excluded because of data limitations",
        ],
        "[1:00] From my code comments and experiments. Shows how the design evolved.")

# Q&A
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, W, 7.5, NAVY)
text(s, 0.9, 2.6, 11.5, 1.0, "Questions", 48, WHITE, bold=True)
text(s, 0.9, 3.7, 11.5, 1.2, "Risk-aware by construction: diversify and size by risk, let trend and market-memory\n"
     "regimes set how much risk to take, and judge every layer by what it adds.", 20, LIGHT)
text(s, 0.9, 5.6, 11.5, 0.4, "github.com/Abhatti-123123/carver", 16, RGBColor(0x8F, 0xB8, 0xEC))
notes(s, "Close by restating the thesis in one sentence, then open for questions.")

prs.save(sys.argv[1])
print("slides:", len(prs.slides))
