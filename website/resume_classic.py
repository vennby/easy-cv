import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth

# ─────────────────────────────────────────────────────────────────────────────
# Font registration
# EBGaramond for body; Times-Bold / Times-Italic as built-in serif companions
# ─────────────────────────────────────────────────────────────────────────────
def _register_fonts():
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    try:
        pdfmetrics.registerFont(TTFont("EBGaramond", os.path.join(font_dir, "EBGaramond-Regular.ttf")))
        return "EBGaramond"
    except Exception:
        return "Times-Roman"

def generate_classic_resume(resume):
    # ── constants ────────────────────────────────────────────────────────
    BODY   = _register_fonts()   # EBGaramond (serif, same as current)
    BOLD   = "Times-Bold"        # built-in serif bold — blends with EB Garamond
    ITALIC = "Times-Italic"      # built-in serif italic

    PAGE_W, PAGE_H = letter
    L      = 43                  # left  margin  (points)
    R      = PAGE_W - 43         # right margin
    TW     = R - L               # usable text width
    LH     = 13.5                # base leading
    BULLET = "\u2022"

    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=letter)
    y   = PAGE_H - 42

    # ── helpers ──────────────────────────────────────────────────────────
    def sw(text, font, size):
        return stringWidth(text, font, size)

    def ensure(needed):
        nonlocal y
        if y - needed < 52:
            c.showPage()
            y = PAGE_H - 50

    def clean_bullet(text):
        """Strip leading markdown-style list markers (-, *, –) users type."""
        import re
        return re.sub(r'^[-\*\u2013\u2022]\s*', '', text.strip())

    def draw_wrapped(text, x, avail_w, font, size, bullet=None, hang=8):
        """Wrap and draw text. bullet=BULLET to prefix first line."""
        nonlocal y
        text     = clean_bullet(text) if bullet else text
        prefix   = f"{bullet}  " if bullet else ""
        prefix_w = sw(prefix, font, size) if bullet else 0
        words    = text.split()
        line     = ""
        first    = True

        c.setFont(font, size)
        while words:
            trial = (line + " " + words[0]).strip()
            slot  = avail_w - (prefix_w if first else hang)
            if sw(trial, font, size) <= slot:
                line = trial
                words.pop(0)
            else:
                ensure(LH)
                ox = x + (0 if first else hang)
                c.drawString(ox, y, (prefix if first else "") + line)
                y -= LH
                c.setFont(font, size)
                line, first = "", False
        if line:
            ensure(LH)
            ox = x + (0 if first else hang)
            c.drawString(ox, y, (prefix if first else "") + line)
            y -= LH

    def section_header(title):
        nonlocal y
        ensure(LH * 3)
        y -= 8                           # gap above section
        c.setFont(BOLD, 11.5)
        c.setFillColor(colors.black)
        c.drawString(L, y, title.upper())
        # Full-width rule sits 1.5 pt below baseline
        rule_y = y - 1.5
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.6)
        c.line(L, rule_y, R, rule_y)
        y -= LH + 3                      # gap below header before content

    def two_col(l_text, l_font, l_size, r_text, r_font, r_size):
        nonlocal y
        ensure(LH)
        c.setFillColor(colors.black)
        c.setFont(l_font, l_size)
        c.drawString(L, y, l_text)
        if r_text:
            c.setFont(r_font, r_size)
            c.drawRightString(R, y, r_text)
        y -= LH

    def fmt_date(date_str):
        if not date_str:
            return ""
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return datetime.strptime(str(date_str), fmt).strftime("%b %Y")
            except Exception:
                continue
        return str(date_str)

    # ════════════════════════════════════════════════════════════════════
    # NAME
    # ════════════════════════════════════════════════════════════════════
    pi        = getattr(getattr(resume, "user", None), "personal_info", None)
    full_name = (getattr(pi, "full_name", None) or getattr(resume, "name", ""))

    c.setFont(BOLD, 22)
    c.setFillColor(colors.black)
    c.drawCentredString(PAGE_W / 2, y, full_name)
    y -= LH + 4

    # ════════════════════════════════════════════════════════════════════
    # CONTACT LINE  — centered, pipe-separated, hyperlinked
    # ════════════════════════════════════════════════════════════════════
    if pi:
        SEP  = "  |  "
        CS   = 9.5
        parts, types = [], []
        if getattr(pi, "phone",    None): parts.append(pi.phone);    types.append("phone")
        if getattr(pi, "email",    None): parts.append(pi.email);    types.append("email")
        if getattr(pi, "linkedin", None): parts.append("LinkedIn");  types.append("linkedin")
        if getattr(pi, "github",   None): parts.append("GitHub");    types.append("github")
        if getattr(pi, "website",  None): parts.append(pi.website);  types.append("website")

        if parts:
            sep_w   = sw(SEP, BODY, CS)
            total_w = sum(sw(p, BODY, CS) for p in parts) + sep_w * (len(parts) - 1)
            cx      = (PAGE_W - total_w) / 2

            c.setFont(BODY, CS)
            c.setFillColor(colors.HexColor("#222222"))
            for idx, part in enumerate(parts):
                pw = sw(part, BODY, CS)
                c.drawString(cx, y, part)
                url_map = {
                    "linkedin": pi.linkedin,
                    "github":   pi.github,
                    "website":  pi.website,
                    "email":    f"mailto:{pi.email}",
                    "phone":    f"tel:{pi.phone}",
                }
                c.linkURL(url_map[types[idx]], (cx, y - 2, cx + pw, y + CS), relative=0)
                cx += pw
                if idx < len(parts) - 1:
                    c.setFillColor(colors.HexColor("#888888"))
                    c.drawString(cx, y, SEP)
                    c.setFillColor(colors.HexColor("#222222"))
                    cx += sep_w

        y -= LH + 2

    # ════════════════════════════════════════════════════════════════════
    # SUMMARY / BIO
    # ════════════════════════════════════════════════════════════════════
    if resume.bios:
        section_header("Summary")
        c.setFillColor(colors.black)
        for bio in resume.bios:
            draw_wrapped(bio.bio, L, TW, BODY, 10.5)
        y -= 2

    # ════════════════════════════════════════════════════════════════════
    # EDUCATION
    # ════════════════════════════════════════════════════════════════════
    if resume.educations:
        section_header("Education")
        for edu in resume.educations:
            ensure(LH * 2.5)
            date_parts = []
            if edu.start_year: date_parts.append(str(edu.start_year))
            if edu.end_year:   date_parts.append(str(edu.end_year))
            date_str = " \u2013 ".join(date_parts)

            # Row 1: Bold institution + location  |  date
            two_col(f"{edu.uni}, {edu.location}", BOLD, 11,
                    date_str,                     BODY, 10.5)
            # Row 2: Italic degree
            if edu.degree:
                c.setFont(ITALIC, 10.5)
                c.setFillColor(colors.black)
                c.drawString(L, y, edu.degree)
                y -= LH
            y -= 4                       # gap between education entries

    # ════════════════════════════════════════════════════════════════════
    # EXPERIENCE
    # ════════════════════════════════════════════════════════════════════
    if resume.experiences:
        section_header("Experience")
        for exp in resume.experiences:
            ensure(LH * 4)

            start_fmt = fmt_date(exp.start_date)
            end_fmt   = "Present" if (exp.ongoing or not exp.end_date) else fmt_date(exp.end_date)
            date_str  = f"{start_fmt} \u2013 {end_fmt}" if start_fmt else end_fmt

            # Row 1: Bold company  |  dates
            two_col(exp.comp, BOLD, 11, date_str, BODY, 10.5)
            # Row 2: Italic role
            c.setFont(ITALIC, 10.5)
            c.setFillColor(colors.black)
            c.drawString(L, y, exp.role)
            y -= LH
            # Bullets
            if exp.desc:
                bullets = [b.strip() for b in exp.desc.splitlines() if b.strip()] or [exp.desc.strip()]
                c.setFillColor(colors.black)
                for bt in bullets:
                    draw_wrapped(bt, L + 10, TW - 14, BODY, 10.5, bullet=BULLET, hang=10)
            y -= 4                       # gap between experience entries

    # ════════════════════════════════════════════════════════════════════
    # PROJECTS
    # ════════════════════════════════════════════════════════════════════
    if resume.projects:
        section_header("Projects")
        for proj in resume.projects:
            ensure(LH * 3)
            # Row 1: Bold project name  |  italic tools (right)
            c.setFont(BOLD, 11)
            c.setFillColor(colors.black)
            c.drawString(L, y, proj.proj)
            if proj.tool:
                c.setFont(ITALIC, 10.5)
                c.drawRightString(R, y, proj.tool)
            y -= LH
            # Bullets
            if proj.desc:
                bullets = [b.strip() for b in proj.desc.splitlines() if b.strip()] or [proj.desc.strip()]
                c.setFillColor(colors.black)
                for bt in bullets:
                    draw_wrapped(bt, L + 10, TW - 14, BODY, 10.5, bullet=BULLET, hang=10)
            y -= 4                       # gap between project entries

    # ════════════════════════════════════════════════════════════════════
    # TECHNICAL SKILLS
    # ════════════════════════════════════════════════════════════════════
    if resume.skills:
        section_header("Technical Skills")
        grouped = {}
        for skill in resume.skills:
            g = (skill.group or "Other").strip()
            grouped.setdefault(g, []).append(skill.data)

        for group_name, skill_list in grouped.items():
            ensure(LH)
            label    = f"{group_name}: "
            label_w  = sw(label, BOLD, 10.5)
            items    = ", ".join(skill_list)
            words    = items.split()
            line     = ""
            first    = True

            c.setFont(BOLD, 10.5)
            c.setFillColor(colors.black)
            c.drawString(L, y, label)
            c.setFont(BODY, 10.5)

            for word in words:
                trial    = (line + " " + word).strip()
                avail    = (TW - label_w) if first else TW
                if sw(trial, BODY, 10.5) <= avail:
                    line = trial
                else:
                    ensure(LH)
                    c.drawString((L + label_w) if first else L, y, line)
                    y -= LH
                    c.setFont(BODY, 10.5)
                    first, line = False, word
            if line:
                ensure(LH)
                c.drawString((L + label_w) if first else L, y, line)
                y -= LH

    c.save()
    buf.seek(0)
    return buf