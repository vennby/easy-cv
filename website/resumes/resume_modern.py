import os
import io
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader

# ── Palette ───────────────────────────────────────────────────────────────
_SIDEBAR_BG   = colors.HexColor("#1B2B44")   # dark navy
_ACCENT       = colors.HexColor("#3A7FBF")   # steel blue
_SIDEBAR_TEXT = colors.HexColor("#D8E6F5")   # light blue-white
_SIDEBAR_DIM  = colors.HexColor("#8EB0D4")   # muted blue
_SIDEBAR_HEAD = colors.HexColor("#FFFFFF")   # white headings
_MAIN_TEXT    = colors.HexColor("#111827")   # near-black
_MAIN_MUTED   = colors.HexColor("#4A5568")   # muted grey
_RULE         = colors.HexColor("#CBD5E0")   # light rule


def _register_fonts():
    fd = os.path.join(os.path.dirname(__file__), "..", "fonts")
    try:
        pdfmetrics.registerFont(TTFont("EBGaramond", os.path.join(fd, "EBGaramond-Regular.ttf")))
        return "EBGaramond"
    except Exception:
        return "Times-Roman"


def _circle_photo(path):
    try:
        from PIL import Image, ImageDraw
        img  = Image.open(path).convert("RGBA")
        s    = min(img.size)
        img  = img.crop(((img.width - s) // 2, (img.height - s) // 2,
                          (img.width + s) // 2, (img.height + s) // 2))
        img  = img.resize((220, 220), Image.LANCZOS)
        mask = Image.new("L", (220, 220), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
        img.putalpha(mask)
        out  = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        return out
    except Exception:
        return None


def _clean_bullets(text):
    """
    Split description text into bullet strings.
    Lines starting with -, bullet, or * begin a new bullet.
    Continuation lines (no leading marker) are joined to the previous bullet.
    """
    if not text or not text.strip():
        return []
    lines   = text.splitlines()
    bullets = []
    current = None
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if re.match(r'^[-\u2022\*]\s*', stripped):
            if current is not None:
                bullets.append(current)
            current = re.sub(r'^[-\u2022\*]\s*', '', stripped)
        else:
            if current is None:
                current = stripped
            else:
                current += " " + stripped
    if current is not None:
        bullets.append(current)
    return bullets or [text.strip()]


def _trim_url(url, max_chars=28):
    if not url:
        return url
    s = re.sub(r'^https?://(www\.)?', '', url).rstrip('/')
    return s if len(s) <= max_chars else s[:max_chars - 1] + "\u2026"


def _fmt_date(ds):
    if not ds:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(str(ds), fmt).strftime("%b %Y")
        except Exception:
            continue
    return str(ds)


# ─────────────────────────────────────────────────────────────────────────────
def generate_modern_resume(resume):
    BODY   = _register_fonts()
    BOLD   = "Times-Bold"
    ITALIC = "Times-Italic"
    BULL   = "\u2022"

    PAGE_W, PAGE_H = letter      # 612 x 792 pt

    # Layout constants
    SB_W  = 185   # sidebar width
    SB_L  = 13    # sidebar content left x
    SB_R  = SB_W - 11
    SB_TW = SB_R - SB_L   # usable sidebar text width

    MX = SB_W + 20   # main column left x
    MR = PAGE_W - 26  # main column right x
    MW = MR - MX      # main column text width

    LH = 13.5  # base leading

    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=letter)

    def sw(text, font, size):
        return stringWidth(text, font, size)

    # ── Sidebar background ────────────────────────────────────────────────
    def draw_sidebar_bg():
        c.setFillColor(_SIDEBAR_BG)
        c.rect(0, 0, SB_W, PAGE_H, fill=1, stroke=0)

    draw_sidebar_bg()

    sb_y = PAGE_H - 22

    # ── Sidebar text wrapper (word-wrap with optional indent) ─────────────
    def sb_wrap(text, font, size, color=None, x_indent=0):
        nonlocal sb_y
        x     = SB_L + x_indent
        avail = SB_TW - x_indent
        words = text.split()
        line  = ""
        c.setFont(font, size)
        c.setFillColor(color or _SIDEBAR_TEXT)
        while words:
            trial = (line + " " + words[0]).strip()
            if sw(trial, font, size) <= avail:
                line  = trial
                words.pop(0)
            else:
                if line:
                    c.drawString(x, sb_y, line)
                    sb_y -= LH * 0.88
                    c.setFont(font, size)
                line  = words.pop(0)
                avail = SB_TW
                x     = SB_L
        if line:
            c.drawString(x, sb_y, line)
            sb_y -= LH * 0.88

    # ── Sidebar section header ────────────────────────────────────────────
    def sb_section(title):
        nonlocal sb_y
        sb_y -= 9
        c.setFillColor(_ACCENT)
        c.rect(SB_L, sb_y + LH * 0.7, SB_TW, 1.0, fill=1, stroke=0)
        sb_y -= 2.5
        c.setFont(BOLD, 8)
        c.setFillColor(_SIDEBAR_HEAD)
        c.drawString(SB_L, sb_y, title.upper())
        sb_y -= LH * 0.85

    # ── Contact row: small icon glyph + wrapped text on same line ─────────
    def sb_contact_row(icon, display, url=None):
        nonlocal sb_y
        if not display:
            return
        ICON_SIZE = 7.5
        TEXT_SIZE = 8.5
        ICON_SLOT = 14   # horizontal px reserved for icon

        c.setFont(BOLD, ICON_SIZE)
        c.setFillColor(_ACCENT)
        c.drawString(SB_L, sb_y, icon)

        avail  = SB_TW - ICON_SLOT
        words  = display.split()
        line   = ""
        first  = True
        line_y = sb_y

        c.setFont(BODY, TEXT_SIZE)
        c.setFillColor(_SIDEBAR_TEXT)
        while words:
            trial = (line + " " + words[0]).strip()
            slot  = avail if first else SB_TW
            if sw(trial, BODY, TEXT_SIZE) <= slot:
                line  = trial
                words.pop(0)
            else:
                if line:
                    x = SB_L + (ICON_SLOT if first else 0)
                    c.drawString(x, line_y, line)
                    if url and first:
                        tw = sw(line, BODY, TEXT_SIZE)
                        c.linkURL(url, (x, line_y - 2, x + tw, line_y + TEXT_SIZE), relative=0)
                    line_y -= LH * 0.92
                    c.setFont(BODY, TEXT_SIZE)
                first, line = False, words.pop(0)
        if line:
            x = SB_L + (ICON_SLOT if first else 0)
            c.drawString(x, line_y, line)
            if url and first:
                tw = sw(line, BODY, TEXT_SIZE)
                c.linkURL(url, (x, line_y - 2, x + tw, line_y + TEXT_SIZE), relative=0)
            line_y -= LH * 0.92
        sb_y = line_y - 1

    # ── Personal info ─────────────────────────────────────────────────────
    pi        = getattr(getattr(resume, "user", None), "personal_info", None)
    full_name = (getattr(pi, "full_name", None) or getattr(resume, "name", ""))

    # ── Circular photo ────────────────────────────────────────────────────
    PHOTO_R  = 44
    PHOTO_CX = SB_W / 2

    if pi and getattr(pi, "image_path", None):
        img_path   = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", pi.image_path)
        circle_buf = _circle_photo(img_path)
        if circle_buf:
            PHOTO_CY = sb_y - PHOTO_R
            c.saveState()
            path = c.beginPath()
            path.circle(PHOTO_CX, PHOTO_CY, PHOTO_R)
            c.clipPath(path, stroke=0, fill=0)
            c.drawImage(ImageReader(circle_buf),
                        PHOTO_CX - PHOTO_R, PHOTO_CY - PHOTO_R,
                        width=PHOTO_R * 2, height=PHOTO_R * 2, mask="auto")
            c.restoreState()
            c.setStrokeColor(colors.white)
            c.setLineWidth(2)
            c.circle(PHOTO_CX, PHOTO_CY, PHOTO_R + 1, fill=0, stroke=1)
            sb_y = PHOTO_CY - PHOTO_R - 8
        else:
            sb_y -= 10
    else:
        sb_y -= 10

    # ── Sidebar name ──────────────────────────────────────────────────────
    name_parts = full_name.strip().split()
    first_line = " ".join(name_parts[:-1]) if len(name_parts) > 1 else full_name
    last_line  = name_parts[-1]             if len(name_parts) > 1 else ""

    c.setFont(BOLD, 12)
    c.setFillColor(colors.white)
    if first_line:
        c.drawCentredString(SB_W / 2, sb_y, first_line)
        sb_y -= LH
    if last_line:
        c.drawCentredString(SB_W / 2, sb_y, last_line)
        sb_y -= LH
    sb_y -= 4

    # ── Contact ───────────────────────────────────────────────────────────
    if pi:
        sb_section("Contact")
        if getattr(pi, "phone",    None):
            sb_contact_row("T",  pi.phone,            f"tel:{pi.phone}")
        if getattr(pi, "email",    None):
            sb_contact_row("@",  pi.email,            f"mailto:{pi.email}")
        if getattr(pi, "linkedin", None):
            sb_contact_row("in", _trim_url(pi.linkedin), pi.linkedin)
        if getattr(pi, "github",   None):
            sb_contact_row("gh", _trim_url(pi.github),   pi.github)
        if getattr(pi, "website",  None):
            sb_contact_row("W",  _trim_url(pi.website),  pi.website)
        if getattr(pi, "address",  None):
            parts      = [p.strip() for p in re.split(r'[,;]', pi.address) if p.strip()]
            short_addr = ", ".join(parts[-2:]) if len(parts) >= 2 else pi.address
            sb_contact_row("\u2605", short_addr)

    # ── Skills ────────────────────────────────────────────────────────────
    if resume.skills:
        sb_section("Skills")
        grouped = {}
        for skill in resume.skills:
            g = (skill.group or "Other").strip()
            grouped.setdefault(g, []).append(skill.data)

        for grp, items in grouped.items():
            c.setFont(BOLD, 8.5)
            c.setFillColor(_SIDEBAR_HEAD)
            c.drawString(SB_L, sb_y, grp)
            sb_y -= LH * 0.9
            for item in items:
                sb_wrap(f"{BULL}  {item}", BODY, 8.5, x_indent=2)
            sb_y -= 2

    # =========================================================================
    # MAIN COLUMN
    # =========================================================================
    my = PAGE_H - 32

    def ensure(needed):
        nonlocal my
        if my - needed < 52:
            c.showPage()
            draw_sidebar_bg()
            my = PAGE_H - 42

    def main_wrap(text, font, size, bullet=False, x_off=0):
        """Word-wrap text in the main column with optional hanging-indent bullet."""
        nonlocal my
        HANG     = 11
        prefix   = f"{BULL}  " if bullet else ""
        prefix_w = sw(prefix, font, size) if bullet else 0
        words    = text.split()
        line     = ""
        first    = True
        c.setFont(font, size)
        c.setFillColor(_MAIN_TEXT)
        while words:
            trial = (line + " " + words[0]).strip()
            avail = (MW - x_off - prefix_w) if first else (MW - x_off - HANG)
            if sw(trial, font, size) <= avail:
                line  = trial
                words.pop(0)
            else:
                ensure(LH)
                ox = MX + x_off + (0 if first else HANG)
                c.drawString(ox, my, (prefix if first else "") + line)
                my    -= LH
                c.setFont(font, size)
                c.setFillColor(_MAIN_TEXT)
                line, first = "", False
        if line:
            ensure(LH)
            ox = MX + x_off + (0 if first else HANG)
            c.drawString(ox, my, (prefix if first else "") + line)
            my -= LH

    def main_section(title):
        nonlocal my
        ensure(LH * 3)
        my -= 8
        c.setFillColor(_ACCENT)
        c.rect(MX - 9, my - 1, 3.5, LH + 2, fill=1, stroke=0)
        c.setFont(BOLD, 11.5)
        c.setFillColor(colors.HexColor("#1A2B44"))
        c.drawString(MX, my, title.upper())
        my -= 3
        c.setStrokeColor(_RULE)
        c.setLineWidth(0.5)
        c.line(MX, my, MR, my)
        my -= LH

    def two_col(l_text, l_font, l_size, r_text):
        nonlocal my
        ensure(LH)
        c.setFont(l_font, l_size)
        c.setFillColor(_MAIN_TEXT)
        c.drawString(MX, my, l_text)
        if r_text:
            c.setFont(BODY, 9.5)
            c.setFillColor(_MAIN_MUTED)
            c.drawRightString(MR, my, r_text)
        my -= LH

    # ── Name header ───────────────────────────────────────────────────────
    c.setFont(BOLD, 21)
    c.setFillColor(colors.HexColor("#1A2B44"))
    c.drawString(MX, my, full_name)
    my -= LH + 2
    c.setStrokeColor(_ACCENT)
    c.setLineWidth(1.5)
    c.line(MX, my, MR, my)
    my -= 10

    # ── Profile / Bio ─────────────────────────────────────────────────────
    if resume.bios:
        main_section("Profile")
        for bio in resume.bios:
            main_wrap(bio.bio, BODY, 10.5)
        my -= 4

    # ── Education ─────────────────────────────────────────────────────────
    if resume.educations:
        main_section("Education")
        for edu in resume.educations:
            ensure(LH * 3)
            parts    = [str(p) for p in [edu.start_year, edu.end_year] if p]
            date_str = " \u2013 ".join(parts)
            two_col(f"{edu.uni}, {edu.location}", BOLD, 10.5, date_str)
            if edu.degree:
                c.setFont(ITALIC, 10)
                c.setFillColor(_MAIN_MUTED)
                c.drawString(MX, my, edu.degree)
                my -= LH
            my -= 6

    # ── Experience ────────────────────────────────────────────────────────
    if resume.experiences:
        main_section("Experience")
        for exp in resume.experiences:
            ensure(LH * 4)
            end_s  = "Present" if (exp.ongoing or not exp.end_date) else _fmt_date(exp.end_date)
            date_s = f"{_fmt_date(exp.start_date)} \u2013 {end_s}" if exp.start_date else end_s
            two_col(exp.comp, BOLD, 10.5, date_s)
            c.setFont(ITALIC, 10)
            c.setFillColor(_MAIN_MUTED)
            c.drawString(MX, my, exp.role)
            my -= LH + 1
            for bt in _clean_bullets(exp.desc):
                main_wrap(bt, BODY, 10, bullet=True, x_off=4)
            my -= 6

    # ── Projects ──────────────────────────────────────────────────────────
    if resume.projects:
        main_section("Projects")
        for proj in resume.projects:
            ensure(LH * 3)
            c.setFont(BOLD, 10.5)
            c.setFillColor(_MAIN_TEXT)
            c.drawString(MX, my, proj.proj)
            if proj.tool:
                c.setFont(ITALIC, 9.5)
                c.setFillColor(_ACCENT)
                c.drawRightString(MR, my, proj.tool)
            my -= LH + 1
            for bt in _clean_bullets(proj.desc):
                main_wrap(bt, BODY, 10, bullet=True, x_off=4)
            my -= 6

    c.save()
    buf.seek(0)
    return buf