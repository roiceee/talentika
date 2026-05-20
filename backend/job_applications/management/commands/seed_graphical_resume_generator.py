"""
Heavily graphical résumé PDF builders for OCR robustness testing.

These styles deliberately stress OCR engines (Tesseract) with photo
placeholders, skill bars, colored banner blocks, sidebar columns, pie-chart
style skill breakdowns, and timeline infographics. All five styles render
the SAME factual résumé content. Only the visual treatment differs, so any
variation in extracted text can be attributed to the OCR layer rather than
to differences in content.
"""

from io import BytesIO

from reportlab.graphics.shapes import Circle, Drawing, Polygon, Rect, Wedge
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

# ─────────────────────────────────────────────────────────────────────────────
# Palette
# ─────────────────────────────────────────────────────────────────────────────

ORANGE     = colors.HexColor("#F39C12")
ORANGE_LT  = colors.HexColor("#FCD9A2")
TEAL       = colors.HexColor("#2C5F73")
TEAL_LT    = colors.HexColor("#A7C7D0")
NAVY       = colors.HexColor("#1A3C6E")
NAVY_DK    = colors.HexColor("#0D2545")
DARK       = colors.HexColor("#2C3E50")
RED        = colors.HexColor("#C0392B")
GOLD       = colors.HexColor("#D4A017")
GREEN      = colors.HexColor("#27AE60")
LIGHT_BG   = colors.HexColor("#F5F5F5")
GREY       = colors.HexColor("#777777")
LGREY      = colors.HexColor("#BDC3C7")
WHITE      = colors.white
BLACK      = colors.black


# ─────────────────────────────────────────────────────────────────────────────
# Reusable graphical primitives
# ─────────────────────────────────────────────────────────────────────────────

def _photo_placeholder(width=1.3 * inch, height=1.3 * inch, bg=TEAL_LT, fg=WHITE):
    """A stylized profile-photo placeholder drawn as vector shapes."""
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=bg, strokeColor=None))
    d.add(Circle(width / 2, height * 0.68, height * 0.18, fillColor=fg, strokeColor=None))
    d.add(Polygon(
        [width * 0.20, 0,
         width * 0.20, height * 0.30,
         width * 0.32, height * 0.48,
         width * 0.68, height * 0.48,
         width * 0.80, height * 0.30,
         width * 0.80, 0],
        fillColor=fg, strokeColor=None,
    ))
    return d


def _circular_photo_placeholder(diameter=1.6 * inch, bg=TEAL_LT, fg=WHITE,
                                ring=None):
    """A circular profile photo placeholder with a stylized silhouette."""
    d = Drawing(diameter, diameter)
    if ring is not None:
        d.add(Circle(diameter / 2, diameter / 2, diameter / 2,
                     fillColor=ring, strokeColor=None))
        d.add(Circle(diameter / 2, diameter / 2, diameter / 2 - 3,
                     fillColor=bg, strokeColor=None))
    else:
        d.add(Circle(diameter / 2, diameter / 2, diameter / 2,
                     fillColor=bg, strokeColor=None))
    d.add(Circle(diameter / 2, diameter * 0.62, diameter * 0.13,
                 fillColor=fg, strokeColor=None))
    d.add(Polygon(
        [diameter * 0.22, diameter * 0.05,
         diameter * 0.28, diameter * 0.46,
         diameter * 0.72, diameter * 0.46,
         diameter * 0.78, diameter * 0.05],
        fillColor=fg, strokeColor=None,
    ))
    return d


def _make_page_bg(page_color, *, sidebar_color=None, sidebar_x=0.3 * inch,
                  sidebar_width=2.6 * inch, margin=0.3 * inch):
    """Return an onPage callback that paints a full-bleed background and,
    optionally, a contrasting sidebar rectangle inside the margins."""
    page_w, page_h = letter

    def _draw(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(page_color)
        canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)
        if sidebar_color is not None:
            canvas.setFillColor(sidebar_color)
            canvas.rect(sidebar_x, margin, sidebar_width, page_h - 2 * margin,
                        stroke=0, fill=1)
        canvas.restoreState()

    return _draw


class SkillBar(Flowable):
    """Horizontal skill bar: label on left, filled progress bar, percent on right."""

    def __init__(self, label, percent, *, width=220, height=10,
                 bar_color=ORANGE, bg_color=ORANGE_LT, text_color=DARK,
                 label_width=70):
        super().__init__()
        self.label = label
        self.percent = max(0, min(100, percent))
        self.width = width
        self.height = height
        self.bar_color = bar_color
        self.bg_color = bg_color
        self.text_color = text_color
        self.label_width = label_width

    def wrap(self, *_):
        return self.width, self.height + 6

    def draw(self):
        c = self.canv
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(0, self.height / 2 - 1, self.label.upper())
        bar_x = self.label_width
        bar_w = self.width - bar_x - 30
        c.setFillColor(self.bg_color)
        c.rect(bar_x, 0, bar_w, self.height, stroke=0, fill=1)
        c.setFillColor(self.bar_color)
        c.rect(bar_x, 0, bar_w * (self.percent / 100), self.height, stroke=0, fill=1)
        c.setFillColor(self.text_color)
        c.setFont("Helvetica", 7)
        c.drawString(bar_x + bar_w + 4, self.height / 2 - 1, f"{self.percent}%")


class SkillDots(Flowable):
    """Skill rendered as 5 filled/empty circles (●●●●○)."""

    def __init__(self, label, level, *, width=220, dot_radius=4, gap=4,
                 fill_color=ORANGE, empty_color=LGREY, text_color=DARK,
                 label_width=110):
        super().__init__()
        self.label = label
        self.level = max(0, min(5, level))
        self.width = width
        self.r = dot_radius
        self.gap = gap
        self.fill_color = fill_color
        self.empty_color = empty_color
        self.text_color = text_color
        self.label_width = label_width

    def wrap(self, *_):
        return self.width, self.r * 2 + 4

    def draw(self):
        c = self.canv
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(0, self.r - 2, self.label)
        x = self.label_width
        y = self.r
        for i in range(5):
            c.setFillColor(self.fill_color if i < self.level else self.empty_color)
            c.circle(x + i * (self.r * 2 + self.gap), y, self.r, stroke=0, fill=1)


class DonutChart(Flowable):
    """Donut chart visualising a skill mix. Caller supplies (label, percent, color) tuples."""

    def __init__(self, segments, *, size=1.4 * inch, hole_ratio=0.55):
        super().__init__()
        self.segments = segments
        self.size = size
        self.hole_ratio = hole_ratio

    def wrap(self, *_):
        return self.size, self.size

    def draw(self):
        c = self.canv
        cx = cy = self.size / 2
        r_outer = self.size / 2
        r_inner = r_outer * self.hole_ratio
        total = sum(p for _, p, _ in self.segments) or 1
        start = 90
        for _, pct, col in self.segments:
            sweep = (pct / total) * 360
            c.setFillColor(col)
            c.wedge(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                    start, -sweep, stroke=0, fill=1)
            start -= sweep
        c.setFillColor(WHITE)
        c.circle(cx, cy, r_inner, stroke=0, fill=1)


class Timeline(Flowable):
    """Vertical timeline column: a colored line with year-dot markers."""

    def __init__(self, years, *, width=0.6 * inch, height=4 * inch,
                 line_color=ORANGE, dot_color=NAVY, text_color=DARK):
        super().__init__()
        self.years = years
        self.width = width
        self.height = height
        self.line_color = line_color
        self.dot_color = dot_color
        self.text_color = text_color

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        line_x = self.width * 0.75
        c.setStrokeColor(self.line_color)
        c.setLineWidth(2)
        c.line(line_x, 4, line_x, self.height - 4)
        n = max(1, len(self.years))
        for i, year in enumerate(self.years):
            y = self.height - 10 - (i * (self.height - 20) / max(1, n - 1)) if n > 1 else self.height / 2
            c.setFillColor(self.dot_color)
            c.circle(line_x, y, 4, stroke=0, fill=1)
            c.setFillColor(self.text_color)
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(line_x - 8, y - 3, str(year))


def _hr(color=LGREY, thickness=0.5, space_after=4):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=space_after)


def _band(text, *, bg, fg=WHITE, font="Helvetica-Bold", fs=11, pad=6):
    """Solid colored bar containing a heading."""
    style = ParagraphStyle("_band", fontName=font, fontSize=fs, textColor=fg)
    tbl = Table([[Paragraph(text, style)]], colWidths=["100%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad - 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 2),
    ]))
    return tbl


def _doc(buffer, *, lm=0.5, rm=0.5, tm=0.5, bm=0.5):
    return SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=lm * inch, rightMargin=rm * inch,
        topMargin=tm * inch, bottomMargin=bm * inch,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Style A — Photo banner + two columns + skill bars (matches reference image)
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_a_photo_banner(first_name, last_name, email, phone, template) -> bytes:
    buf = BytesIO()
    doc = _doc(buf)
    base = getSampleStyleSheet()

    name_s = ParagraphStyle("a_name", fontName="Helvetica-Bold", fontSize=18,
                            textColor=WHITE, alignment=TA_LEFT)
    sub_s = ParagraphStyle("a_sub", fontName="Helvetica", fontSize=10,
                           textColor=WHITE, alignment=TA_CENTER)
    section_s = ParagraphStyle("a_sect", fontName="Helvetica-Bold", fontSize=11,
                               textColor=TEAL, spaceAfter=4, spaceBefore=8)
    body_s = ParagraphStyle("a_body", fontName="Helvetica", fontSize=8.5,
                            textColor=DARK, spaceAfter=3, leading=11)
    jh_s = ParagraphStyle("a_jh", fontName="Helvetica-Bold", fontSize=9,
                          textColor=DARK, spaceAfter=1)

    # ── Top banner: orange name box + photo + grey "Barista" strip ──
    orange_box = Table([[Paragraph(f"{first_name}<br/>{last_name}", name_s)]],
                       colWidths=[2.6 * inch], rowHeights=[1.4 * inch])
    orange_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    photo = _photo_placeholder(width=4.8 * inch, height=1.4 * inch, bg=TEAL_LT)
    header = Table([[orange_box, photo]], colWidths=[2.6 * inch, 4.8 * inch])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    title_strip = Table([[Paragraph("Barista", sub_s)]],
                        colWidths=["100%"], rowHeights=[0.25 * inch])
    title_strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    # ── Left column ──
    left = []
    left.append(Paragraph("BIOGRAPHY", section_s))
    left.append(_hr(TEAL, 1, 4))
    left.append(Paragraph(template["summary"], body_s))

    left.append(Paragraph("CONTACT", section_s))
    left.append(_hr(TEAL, 1, 4))
    left.append(Paragraph(f"&#9679;  {email}", body_s))
    left.append(Paragraph(f"&#9679;  {phone}", body_s))
    left.append(Paragraph("&#9679;  Davao City, Philippines", body_s))

    left.append(Paragraph("SKILLS", section_s))
    left.append(_hr(TEAL, 1, 4))
    for skill, pct in _skill_levels(template["skills"]):
        left.append(SkillBar(skill, pct, width=2.6 * inch))
        left.append(Spacer(1, 2))

    # ── Right column ──
    right = []
    right.append(Paragraph("EDUCATION", section_s))
    right.append(_hr(TEAL, 1, 4))
    for edu in template["education"]:
        right.append(Paragraph(f"<b>{edu['year']}</b> &#8212; {edu['degree']}", body_s))
        right.append(Paragraph(edu["school"], body_s))
        right.append(Spacer(1, 3))

    right.append(Paragraph("WORK EXPERIENCE", section_s))
    right.append(_hr(TEAL, 1, 4))
    for exp in template["experience"]:
        right.append(Paragraph(f"<b>{exp['period']}</b>", body_s))
        right.append(Paragraph(f"<b>{exp['title']}</b>, {exp['company']}", jh_s))
        for duty in exp["duties"]:
            right.append(Paragraph(f"&#9679; {duty}", body_s))
        right.append(Spacer(1, 4))

    if template.get("certifications"):
        right.append(Paragraph("CERTIFICATIONS", section_s))
        right.append(_hr(TEAL, 1, 4))
        for cert in template["certifications"]:
            right.append(Paragraph(f"&#9679; {cert}", body_s))

    body = Table([[left, right]], colWidths=[3.1 * inch, 4.3 * inch])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 10),
    ]))

    doc.build([header, title_strip, Spacer(1, 6), body])
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style B — Dark sidebar (photo, contact, skill dots) + light main column
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_b_dark_sidebar(first_name, last_name, email, phone, template) -> bytes:
    buf = BytesIO()
    doc = _doc(buf, lm=0, rm=0, tm=0, bm=0)
    base = getSampleStyleSheet()

    side_name = ParagraphStyle("b_sname", fontName="Helvetica-Bold", fontSize=16,
                               textColor=WHITE, spaceAfter=2, alignment=TA_CENTER)
    side_role = ParagraphStyle("b_srole", fontName="Helvetica", fontSize=9,
                               textColor=ORANGE, alignment=TA_CENTER, spaceAfter=10)
    side_label = ParagraphStyle("b_slabel", fontName="Helvetica-Bold", fontSize=10,
                                textColor=WHITE, spaceBefore=10, spaceAfter=4)
    side_body = ParagraphStyle("b_sbody", fontName="Helvetica", fontSize=8,
                               textColor=colors.HexColor("#D6DBDF"), spaceAfter=2,
                               leading=11)

    main_name = ParagraphStyle("b_mname", fontName="Helvetica", fontSize=10, textColor=DARK)
    main_sect = ParagraphStyle("b_msect", fontName="Helvetica-Bold", fontSize=12,
                               textColor=NAVY, spaceBefore=10, spaceAfter=4)
    main_body = ParagraphStyle("b_mbody", fontName="Helvetica", fontSize=9,
                               textColor=DARK, spaceAfter=3, leading=12)
    jh_s = ParagraphStyle("b_jh", fontName="Helvetica-Bold", fontSize=9.5,
                          textColor=DARK, spaceAfter=1)

    # ── Sidebar content ──
    sidebar = [Spacer(1, 14)]
    sidebar.append(_photo_placeholder(width=1.6 * inch, height=1.6 * inch, bg=ORANGE))
    sidebar.append(Spacer(1, 8))
    sidebar.append(Paragraph(f"{first_name}<br/>{last_name}", side_name))
    sidebar.append(Paragraph("Senior Barista", side_role))

    sidebar.append(Paragraph("CONTACT", side_label))
    sidebar.append(_hr(ORANGE, 1, 4))
    sidebar.append(Paragraph(f"&#9993; {email}", side_body))
    sidebar.append(Paragraph(f"&#9742; {phone}", side_body))
    sidebar.append(Paragraph("&#9962; Davao City, PH", side_body))

    sidebar.append(Paragraph("SKILLS", side_label))
    sidebar.append(_hr(ORANGE, 1, 4))
    for skill, level in _skill_dot_levels(template["skills"]):
        sidebar.append(SkillDots(skill, level, width=2.0 * inch,
                                 fill_color=ORANGE, empty_color=GREY,
                                 text_color=WHITE, label_width=120))
        sidebar.append(Spacer(1, 1))

    if template.get("certifications"):
        sidebar.append(Paragraph("LICENSES", side_label))
        sidebar.append(_hr(ORANGE, 1, 4))
        for cert in template["certifications"]:
            sidebar.append(Paragraph(f"&#9679; {cert}", side_body))

    # ── Main content ──
    main = [Spacer(1, 14)]
    main.append(Paragraph("ABOUT ME", main_sect))
    main.append(_hr(NAVY, 1.2, 4))
    main.append(Paragraph(template["summary"], main_body))

    main.append(Paragraph("WORK EXPERIENCE", main_sect))
    main.append(_hr(NAVY, 1.2, 4))
    for exp in template["experience"]:
        main.append(Paragraph(f"<b>{exp['title']}</b>  &#8212;  <font color='#777777'>{exp['company']}</font>", jh_s))
        main.append(Paragraph(f"<i>{exp['period']}</i>", main_body))
        for duty in exp["duties"]:
            main.append(Paragraph(f"&#9656; {duty}", main_body))
        main.append(Spacer(1, 4))

    main.append(Paragraph("EDUCATION", main_sect))
    main.append(_hr(NAVY, 1.2, 4))
    for edu in template["education"]:
        main.append(Paragraph(f"<b>{edu['degree']}</b>", main_body))
        main.append(Paragraph(f"{edu['school']}  &#8226;  {edu['year']}", main_body))
        main.append(Spacer(1, 3))

    full = Table([[sidebar, main]], colWidths=[2.6 * inch, 5.9 * inch])
    full.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), NAVY_DK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 16),
        ("RIGHTPADDING", (0, 0), (0, -1), 16),
        ("LEFTPADDING", (1, 0), (1, -1), 18),
        ("RIGHTPADDING", (1, 0), (1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
    ]))

    doc.build([full])
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style C — Bold color-block sections (each section header is a wide colored bar)
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_c_color_blocks(first_name, last_name, email, phone, template) -> bytes:
    buf = BytesIO()
    doc = _doc(buf)
    base = getSampleStyleSheet()

    hero_name = ParagraphStyle("c_name", fontName="Helvetica-Bold", fontSize=32,
                               textColor=WHITE, leading=34)
    hero_role = ParagraphStyle("c_role", fontName="Helvetica", fontSize=13,
                               textColor=WHITE, spaceBefore=6)
    contact_s = ParagraphStyle("c_contact", fontName="Helvetica", fontSize=9,
                               textColor=WHITE, alignment=TA_RIGHT, leading=14)
    body_s = ParagraphStyle("c_body", fontName="Helvetica", fontSize=10,
                            textColor=DARK, leading=13, spaceAfter=4)
    jh_s = ParagraphStyle("c_jh", fontName="Helvetica-Bold", fontSize=10.5,
                          textColor=NAVY, spaceAfter=2)

    # ── Hero block ──
    hero_left = [
        Paragraph(f"{first_name}<br/>{last_name}", hero_name),
        Paragraph("BARISTA", hero_role),
    ]
    hero_right = [
        Paragraph(f"{email}", contact_s),
        Paragraph(f"{phone}", contact_s),
        Paragraph("Davao City, Philippines", contact_s),
    ]
    hero = Table([[hero_left, hero_right]], colWidths=[4.5 * inch, 2.9 * inch])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), RED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
    ]))

    story = [hero, Spacer(1, 10)]

    story.append(_band("PROFILE", bg=NAVY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(template["summary"], body_s))

    story.append(_band("EXPERIENCE", bg=NAVY))
    story.append(Spacer(1, 4))
    for exp in template["experience"]:
        story.append(Paragraph(f"{exp['title']} <font color='#C0392B'>|</font> {exp['company']}", jh_s))
        story.append(Paragraph(f"<i>{exp['period']}</i>", body_s))
        for duty in exp["duties"]:
            story.append(Paragraph(f"&#9642; {duty}", body_s))
        story.append(Spacer(1, 4))

    # Education + Skills side-by-side
    edu_block = [Paragraph("EDUCATION", ParagraphStyle("_x", fontName="Helvetica-Bold",
                                                       fontSize=11, textColor=RED, spaceAfter=4))]
    edu_block.append(_hr(RED, 1, 4))
    for edu in template["education"]:
        edu_block.append(Paragraph(f"<b>{edu['degree']}</b>", body_s))
        edu_block.append(Paragraph(f"{edu['school']} ({edu['year']})", body_s))
        edu_block.append(Spacer(1, 3))

    skill_block = [Paragraph("SKILL LEVELS", ParagraphStyle("_y", fontName="Helvetica-Bold",
                                                            fontSize=11, textColor=RED, spaceAfter=4))]
    skill_block.append(_hr(RED, 1, 4))
    for skill, lvl in _skill_dot_levels(template["skills"]):
        skill_block.append(SkillDots(skill, lvl, fill_color=RED, empty_color=LGREY,
                                     text_color=DARK, label_width=140, width=3.4 * inch))
        skill_block.append(Spacer(1, 1))

    split = Table([[edu_block, skill_block]], colWidths=[3.6 * inch, 3.8 * inch])
    split.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(Spacer(1, 6))
    story.append(split)

    if template.get("certifications"):
        story.append(Spacer(1, 6))
        story.append(_band("CERTIFICATIONS & LICENSES", bg=NAVY))
        story.append(Spacer(1, 4))
        for cert in template["certifications"]:
            story.append(Paragraph(f"&#10004; {cert}", body_s))

    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style D — Timeline infographic with donut-chart skill mix
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_d_timeline_infographic(first_name, last_name, email, phone, template) -> bytes:
    buf = BytesIO()
    doc = _doc(buf, lm=0.4, rm=0.4)
    base = getSampleStyleSheet()
    page_bg = _make_page_bg(colors.HexColor("#FDF1E5"))  # soft peach

    name_s = ParagraphStyle("d_name", fontName="Helvetica-Bold", fontSize=26,
                            textColor=NAVY)
    role_s = ParagraphStyle("d_role", fontName="Helvetica", fontSize=11,
                            textColor=GOLD, spaceAfter=4)
    contact_s = ParagraphStyle("d_contact", fontName="Helvetica", fontSize=8.5,
                               textColor=GREY, alignment=TA_RIGHT)
    section_s = ParagraphStyle("d_sect", fontName="Helvetica-Bold", fontSize=12,
                               textColor=NAVY, spaceBefore=10, spaceAfter=4)
    body_s = ParagraphStyle("d_body", fontName="Helvetica", fontSize=9,
                            textColor=DARK, leading=12, spaceAfter=3)
    jh_s = ParagraphStyle("d_jh", fontName="Helvetica-Bold", fontSize=10,
                          textColor=NAVY)

    header_left = [Paragraph(f"{first_name} {last_name}", name_s),
                   Paragraph("BARISTA  &#8226;  SPECIALTY COFFEE", role_s)]
    header_right = [Paragraph(email, contact_s),
                    Paragraph(phone, contact_s),
                    Paragraph("Davao City, PH", contact_s)]
    header = Table([[header_left, header_right]], colWidths=[5.0 * inch, 2.5 * inch])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LINEBELOW", (0, 0), (-1, -1), 2, GOLD),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story = [header, Spacer(1, 10)]

    # ── Donut + Summary side-by-side ──
    donut_segments = [
        ("Coffee Craft", 40, GOLD),
        ("Customer Service", 25, NAVY),
        ("Training & Supervision", 20, ORANGE),
        ("Operations & Inventory", 15, TEAL),
    ]
    donut = DonutChart(donut_segments, size=1.5 * inch)
    legend_s = ParagraphStyle("d_legend", fontName="Helvetica", fontSize=8,
                              textColor=DARK, leading=11)
    legend = [Paragraph("SKILL MIX", ParagraphStyle("d_lh", fontName="Helvetica-Bold",
                                                    fontSize=10, textColor=NAVY, spaceAfter=4))]
    for label, pct, col in donut_segments:
        legend.append(Paragraph(
            f'<font color="{col.hexval()}">&#9632;</font>  {label} &#8212; {pct}%', legend_s))

    summary_block = [Paragraph("PROFILE", section_s),
                     _hr(GOLD, 1, 4),
                     Paragraph(template["summary"], body_s)]

    top_grid = Table(
        [[donut, legend, summary_block]],
        colWidths=[1.7 * inch, 1.8 * inch, 4.0 * inch],
    )
    top_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(top_grid)

    # ── Timeline + Experience ──
    years = [int(_extract_year(exp["period"])) for exp in template["experience"]]
    timeline = Timeline(years, width=0.7 * inch, height=2.4 * inch,
                        line_color=GOLD, dot_color=NAVY)
    exp_block = [Paragraph("EXPERIENCE TIMELINE", section_s), _hr(GOLD, 1, 4)]
    for exp in template["experience"]:
        exp_block.append(Paragraph(f"{exp['title']} &#8212; {exp['company']}", jh_s))
        exp_block.append(Paragraph(f"<i>{exp['period']}</i>", body_s))
        for duty in exp["duties"]:
            exp_block.append(Paragraph(f"&#9656; {duty}", body_s))
        exp_block.append(Spacer(1, 4))

    tl_grid = Table([[timeline, exp_block]], colWidths=[0.8 * inch, 6.7 * inch])
    tl_grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(tl_grid)

    # ── Education + Certs ──
    story.append(Paragraph("EDUCATION & CERTIFICATIONS", section_s))
    story.append(_hr(GOLD, 1, 4))
    for edu in template["education"]:
        story.append(Paragraph(f"<b>{edu['degree']}</b>  &#8212;  {edu['school']}, {edu['year']}", body_s))
    for cert in template.get("certifications", []):
        story.append(Paragraph(f"&#9733; {cert}", body_s))

    doc.build(story, onFirstPage=page_bg, onLaterPages=page_bg)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Style E — Full yellow-page background with off-white sidebar, circular photo,
# and pink cursive-style name. Mirrors a heavily styled flat-design résumé.
# ─────────────────────────────────────────────────────────────────────────────

def _build_style_e_yellow_sidebar(first_name, last_name, email, phone, template) -> bytes:
    buf = BytesIO()

    PAGE_YELLOW = colors.HexColor("#F4D261")
    SIDEBAR_BG  = colors.HexColor("#FBF8EF")
    PINK        = colors.HexColor("#E85A7E")
    PURPLE      = colors.HexColor("#5E2A6F")
    BODY_DK     = colors.HexColor("#3D2E5E")

    page_w, _ = letter
    margin = 0.3 * inch
    sidebar_w = 2.6 * inch

    doc = _doc(buf, lm=0.3, rm=0.3, tm=0.3, bm=0.3)
    page_bg = _make_page_bg(PAGE_YELLOW, sidebar_color=SIDEBAR_BG,
                            sidebar_x=margin, sidebar_width=sidebar_w,
                            margin=margin)

    name_s = ParagraphStyle("e_name", fontName="Helvetica-BoldOblique",
                            fontSize=26, textColor=PINK, leading=28)
    role_s = ParagraphStyle("e_role", fontName="Helvetica-Bold", fontSize=12,
                            textColor=BODY_DK, spaceAfter=6)
    bio_s = ParagraphStyle("e_bio", fontName="Helvetica", fontSize=9.5,
                           textColor=BODY_DK, leading=13, spaceAfter=4)
    main_sect = ParagraphStyle("e_msect", fontName="Helvetica-Bold", fontSize=11,
                               textColor=PURPLE, spaceBefore=10, spaceAfter=4)
    main_body = ParagraphStyle("e_mbody", fontName="Helvetica", fontSize=9,
                               textColor=BODY_DK, leading=12, spaceAfter=4)
    year_s = ParagraphStyle("e_year", fontName="Helvetica", fontSize=9,
                            textColor=BODY_DK, spaceAfter=1)
    jh_s = ParagraphStyle("e_jh", fontName="Helvetica-Bold", fontSize=10,
                          textColor=BODY_DK, spaceAfter=1)
    sidesect_s = ParagraphStyle("e_sidesect", fontName="Helvetica-Bold",
                                fontSize=10, textColor=PURPLE, spaceBefore=12,
                                spaceAfter=4)
    sidebody_s = ParagraphStyle("e_sidebody", fontName="Helvetica", fontSize=8.5,
                                textColor=BODY_DK, leading=12, spaceAfter=2)

    # ── Sidebar (drawn on top of the off-white sidebar rectangle) ──
    sidebar = [Spacer(1, 6)]
    sidebar.append(_circular_photo_placeholder(diameter=1.8 * inch,
                                               bg=PINK, fg=PAGE_YELLOW,
                                               ring=SIDEBAR_BG))
    sidebar.append(Spacer(1, 12))

    sidebar.append(Paragraph("CONTACT", sidesect_s))
    sidebar.append(_hr(PURPLE, 0.6, 4))
    sidebar.append(Paragraph(f"&#9742;  {phone}", sidebody_s))
    sidebar.append(Paragraph(f"&#9993;  {email}", sidebody_s))
    sidebar.append(Paragraph("&#9962;  Davao City, Philippines", sidebody_s))

    sidebar.append(Paragraph("SKILLS", sidesect_s))
    sidebar.append(_hr(PURPLE, 0.6, 4))
    for skill in template["skills"][:8]:
        sidebar.append(Paragraph(f"&#9679; {skill}", sidebody_s))

    sidebar.append(Paragraph("LANGUAGES", sidesect_s))
    sidebar.append(_hr(PURPLE, 0.6, 4))
    for lang in ("English", "Filipino", "Cebuano"):
        sidebar.append(Paragraph(f"&#9679; {lang}", sidebody_s))

    # ── Main content (on yellow) ──
    main = [Spacer(1, 6),
            Paragraph(f"{first_name} {last_name}", name_s),
            Paragraph("Specialty Coffee Barista", role_s),
            Paragraph(template["summary"], bio_s)]

    main.append(Paragraph("EDUCATION", main_sect))
    main.append(_hr(PURPLE, 0.6, 4))
    for edu in template["education"]:
        main.append(Paragraph(f"({edu['year']})", year_s))
        main.append(Paragraph(f"<b>{edu['school'].upper()}</b>", jh_s))
        main.append(Paragraph(edu["degree"], main_body))

    main.append(Paragraph("EXPERIENCE", main_sect))
    main.append(_hr(PURPLE, 0.6, 4))
    for exp in template["experience"]:
        main.append(Paragraph(f"({exp['period']})", year_s))
        main.append(Paragraph(f"<b>{exp['title'].upper()}</b>", jh_s))
        main.append(Paragraph(exp["company"], main_body))
        for duty in exp["duties"]:
            main.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&#9656; {duty}", main_body))
        main.append(Spacer(1, 4))

    if template.get("certifications"):
        main.append(Paragraph("CERTIFICATIONS", main_sect))
        main.append(_hr(PURPLE, 0.6, 4))
        for cert in template["certifications"]:
            main.append(Paragraph(f"&#9733; {cert}", main_body))

    inner_w = page_w - 2 * margin
    body = Table([[sidebar, main]],
                 colWidths=[sidebar_w, inner_w - sidebar_w])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 18),
        ("RIGHTPADDING", (0, 0), (0, -1), 18),
        ("LEFTPADDING", (1, 0), (1, -1), 22),
        ("RIGHTPADDING", (1, 0), (1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    doc.build([body], onFirstPage=page_bg, onLaterPages=page_bg)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _skill_levels(skills):
    """Map a list of skills to (label, percent) pairs using a stable pattern."""
    base = [95, 88, 82, 76, 70, 65]
    pairs = []
    for i, s in enumerate(skills):
        label = s if len(s) <= 18 else s[:16] + ".."
        pct = base[i] if i < len(base) else 60
        pairs.append((label, pct))
    return pairs


def _skill_dot_levels(skills):
    """Map a list of skills to (label, dots-out-of-5) pairs."""
    base = [5, 5, 4, 4, 4, 3]
    pairs = []
    for i, s in enumerate(skills):
        label = s if len(s) <= 28 else s[:26] + ".."
        level = base[i] if i < len(base) else 3
        pairs.append((label, level))
    return pairs


def _extract_year(period):
    """Pull the first 4-digit year out of a period string for the timeline."""
    for token in period.split():
        digits = "".join(ch for ch in token if ch.isdigit())
        if len(digits) >= 4:
            return digits[:4]
    return "----"


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

GRAPHICAL_BUILDERS = [
    _build_style_a_photo_banner,
    _build_style_b_dark_sidebar,
    _build_style_c_color_blocks,
    _build_style_d_timeline_infographic,
    _build_style_e_yellow_sidebar,
]

GRAPHICAL_STYLE_NAMES = [
    "photo_banner",
    "dark_sidebar",
    "color_blocks",
    "timeline_peach_bg",
    "yellow_sidebar_bg",
]


def build_graphical_resume(first_name, last_name, email, phone, template, style_idx) -> bytes:
    builder = GRAPHICAL_BUILDERS[style_idx % len(GRAPHICAL_BUILDERS)]
    return builder(first_name, last_name, email, phone, template)
