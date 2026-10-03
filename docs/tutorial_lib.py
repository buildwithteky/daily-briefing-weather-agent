"""Tiny slide toolkit on top of reportlab (16:9, top-left coordinates)."""
import os
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

W, H = 1280, 720
ORANGE, DARK, BG = HexColor("#EC7211"), HexColor("#232F3E"), HexColor("#F2F3F3")  # AWS orange / squid ink / light grey
GREY, LINE, SOFT = HexColor("#545B64"), HexColor("#D5DBDB"), HexColor("#EAEDED")
AWS_TEAL = HexColor("#00A4A6")  # official "Region" group colour
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aws-icons")
GREEN, AMBER, RED, BLUE = HexColor("#15803D"), HexColor("#B45309"), HexColor("#C62828"), HexColor("#1D4ED8")
CODE_BG, CODE_TXT, CODE_DIM = HexColor("#161E2D"), HexColor("#F2F3F3"), HexColor("#8D99A8")
MONO_W = 0.6  # Courier glyph width / font size


class Deck:
    def __init__(self, path, total, footer):
        self.c = canvas.Canvas(path, pagesize=(W, H))
        self.total, self.footer, self.n = total, footer, 0

    def Y(self, y):
        return H - y

    # ---------------------------------------------------------------- pages
    def slide(self, title, kicker=""):
        c = self.c
        if self.n:
            c.showPage()
        self.n += 1
        c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(ORANGE); c.rect(0, H - 8, W, 8, fill=1, stroke=0)
        if kicker:
            c.setFillColor(ORANGE); c.setFont("Courier-Bold", 13)
            c.drawString(56, self.Y(46), kicker.upper())
        c.setFillColor(DARK); c.setFont("Helvetica-Bold", 31)
        c.drawString(56, self.Y(84), title)
        # footer + progress
        c.setFillColor(LINE); c.rect(0, 0, W, 5, fill=1, stroke=0)
        c.setFillColor(ORANGE); c.rect(0, 0, W * self.n / self.total, 5, fill=1, stroke=0)
        c.setFillColor(GREY); c.setFont("Helvetica", 11)
        c.drawString(56, 22, self.footer)
        c.drawRightString(W - 56, 22, "%d / %d" % (self.n, self.total))

    def title_slide(self, title, sub, tags):
        c = self.c
        self.n += 1
        c.setFillColor(DARK); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(ORANGE); c.rect(0, 0, 18, H, fill=1, stroke=0)
        c.setFillColor(ORANGE); c.setFont("Courier-Bold", 16)
        c.drawString(90, self.Y(150), "HANDS-ON AWS TUTORIAL")
        y = 230
        c.setFillColor(white); c.setFont("Helvetica-Bold", 54)
        for line in title:
            c.drawString(90, self.Y(y), line); y += 66
        c.setFillColor(HexColor("#D9D5D0")); c.setFont("Helvetica", 22)
        for line in sub:
            c.drawString(90, self.Y(y + 10), line); y += 32
        x = 90
        c.setFont("Courier-Bold", 14)
        for t in tags:
            w = c.stringWidth(t, "Courier-Bold", 14) + 28
            c.setStrokeColor(ORANGE); c.setFillColor(HexColor("#333131"))
            c.roundRect(x, self.Y(640), w, 34, 4, fill=1, stroke=1)
            c.setFillColor(white); c.drawString(x + 14, self.Y(629), t); x += w + 12

    # ---------------------------------------------------------------- text
    def para(self, x, y, w, text, size=16, color=DARK, bold=False, leading=None, align=TA_LEFT, font=None):
        st = ParagraphStyle("p", fontName=font or ("Helvetica-Bold" if bold else "Helvetica"), fontSize=size,
                            leading=leading or size * 1.32, textColor=color, alignment=align)
        p = Paragraph(text, st)
        _, h = p.wrap(w, 10000)
        p.drawOn(self.c, x, self.Y(y) - h)
        return h

    def bullets(self, x, y, w, items, size=16, gap=9, color=DARK, bullet="•"):
        for it in items:
            st = ParagraphStyle("b", fontName="Helvetica", fontSize=size, leading=size * 1.32, textColor=color,
                                leftIndent=18, bulletIndent=2, bulletFontName="Helvetica-Bold", bulletColor=ORANGE)
            p = Paragraph(it, st, bulletText=bullet)
            _, h = p.wrap(w, 10000)
            p.drawOn(self.c, x, self.Y(y) - h)
            y += h + gap
        return y

    def label(self, x, y, text, color=ORANGE, size=12):
        self.c.setFillColor(color); self.c.setFont("Courier-Bold", size)
        self.c.drawString(x, self.Y(y), text.upper())

    # ---------------------------------------------------------------- code
    def code(self, x, y, w, lines, size=12, title=None, boost=1.15):
        longest = max((len(l[2:]) + (2 if l.startswith("$ ") else 0)) if l[:2] in ("$ ", "= ") else len(l) for l in lines)
        fit = (w - 28) / (longest * MONO_W)
        size = min(size * boost, fit)
        lh = size * 1.32
        top = 30 if title else 0
        h = len(lines) * lh + 26 + top
        cw = size * MONO_W
        c = self.c
        c.setFillColor(CODE_BG); c.roundRect(x, self.Y(y + h), w, h, 4, fill=1, stroke=0)
        if title:
            c.setFillColor(ORANGE); c.setFont("Courier-Bold", 11)
            c.drawString(x + 14, self.Y(y + 20), title.upper())
        yy = y + 20 + top + size * 0.35
        for raw in lines:
            kind, txt = "plain", raw
            if raw.startswith("$ "): kind, txt = "cmd", raw[2:]
            elif raw.startswith("# "): kind, txt = "com", raw
            elif raw.startswith("= "): kind, txt = "out", raw[2:]
            xx = x + 14
            if kind == "cmd":
                c.setFillColor(ORANGE); c.setFont("Courier-Bold", size); c.drawString(xx, self.Y(yy), "$"); xx += 2 * cw
            c.setFont("Courier", size)
            c.setFillColor({"plain": CODE_TXT, "cmd": CODE_TXT, "com": CODE_DIM, "out": HexColor("#86EFAC")}[kind])
            c.drawString(xx, self.Y(yy), txt)
            yy += lh
        return y + h

    # ---------------------------------------------------------- components
    def callout(self, x, y, w, label, text, color=ORANGE, size=14):
        st = ParagraphStyle("c", fontName="Helvetica", fontSize=size, leading=size * 1.32, textColor=DARK)
        p = Paragraph(text, st)
        _, h = p.wrap(w - 34, 10000)
        bh = h + 40
        c = self.c
        c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(x, self.Y(y + bh), w, bh, 4, fill=1, stroke=1)
        c.setFillColor(color); c.rect(x, self.Y(y + bh), 5, bh, fill=1, stroke=0)
        c.setFont("Courier-Bold", 11); c.drawString(x + 18, self.Y(y + 19), label.upper())
        p.drawOn(c, x + 18, self.Y(y + 28) - h)
        return y + bh

    def table(self, x, y, widths, rows, size=13, header=True, mono_cols=()):
        data = []
        for ri, r in enumerate(rows):
            row = []
            for ci, cell in enumerate(r):
                head = header and ri == 0
                st = ParagraphStyle("t", fontName="Helvetica-Bold" if head else ("Courier" if ci in mono_cols else "Helvetica"),
                                    fontSize=size - (1 if ci in mono_cols and not head else 0), leading=size * 1.3,
                                    textColor=white if head else DARK)
                row.append(Paragraph(cell, st))
            data.append(row)
        t = Table(data, colWidths=widths)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                 ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                 ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, -1), white)]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), DARK)]
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0: style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#F7F5F2")))
        t.setStyle(TableStyle(style))
        w, h = t.wrap(sum(widths), 10000)
        t.drawOn(self.c, x, self.Y(y) - h)
        return y + h

    def node(self, x, y, w, h, title, sub="", fill=white, stroke=DARK, bar=ORANGE, tsize=15):
        c = self.c
        c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(1.2)
        c.roundRect(x, self.Y(y + h), w, h, 4, fill=1, stroke=1)
        if bar:
            c.setFillColor(bar); c.rect(x, self.Y(y + 6), w, 6, fill=1, stroke=0)
        c.setFillColor(DARK if fill in (white, SOFT) else white); c.setFont("Helvetica-Bold", tsize)
        c.drawCentredString(x + w / 2, self.Y(y + h / 2 + (2 if sub else 6)), title)
        if sub:
            c.setFont("Helvetica", tsize - 3); c.setFillColor(GREY if fill in (white, SOFT) else HexColor("#D9D5D0"))
            c.drawCentredString(x + w / 2, self.Y(y + h / 2 + 16), sub)

    def arrow(self, x1, y1, x2, y2, label="", color=DARK, both=False, dash=False, lsize=11, loff=(0, -7)):
        import math
        c = self.c
        c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(1.8)
        if dash: c.setDash(5, 4)
        c.line(x1, self.Y(y1), x2, self.Y(y2)); c.setDash()

        def head(xa, ya, xb, yb):  # arrow head at (xb, yb) pointing away from (xa, ya)
            ang = math.atan2(self.Y(yb) - self.Y(ya), xb - xa)
            p = c.beginPath(); p.moveTo(xb, self.Y(yb))
            for d in (0.42, -0.42):
                p.lineTo(xb - 11 * math.cos(ang - d), self.Y(yb) - 11 * math.sin(ang - d))
            p.close(); c.drawPath(p, fill=1, stroke=0)
        head(x1, y1, x2, y2)
        if both: head(x2, y2, x1, y1)
        if label:
            c.setFont("Helvetica-Bold", lsize); c.setFillColor(color)
            c.drawCentredString((x1 + x2) / 2 + loff[0], self.Y((y1 + y2) / 2 + loff[1]), label)

    def placeholder(self, x, y, w, h, text):
        c = self.c
        c.setFillColor(HexColor("#F4F2EF")); c.setStrokeColor(GREY); c.setDash(6, 4); c.setLineWidth(1.2)
        c.roundRect(x, self.Y(y + h), w, h, 4, fill=1, stroke=1); c.setDash()
        c.setFillColor(GREY); c.setFont("Courier-Bold", 12)
        c.drawCentredString(x + w / 2, self.Y(y + h / 2 - 4), "[ SCREENSHOT ]")
        self.para(x + 16, y + h / 2 + 8, w - 32, text, size=12, color=GREY, align=TA_CENTER)

    def badge(self, x, y, n, r=15):
        c = self.c
        c.setFillColor(ORANGE); c.circle(x, self.Y(y), r, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Helvetica-Bold", 15); c.drawCentredString(x, self.Y(y) - 5.5, str(n))

    def chip(self, x, y, text, fill=SOFT, color=DARK, size=12):
        c = self.c
        w = c.stringWidth(text, "Helvetica-Bold", size) + 20
        c.setFillColor(fill); c.roundRect(x, self.Y(y + 26), w, 26, 4, fill=1, stroke=0)
        c.setFillColor(color); c.setFont("Helvetica-Bold", size); c.drawString(x + 10, self.Y(y + 18), text)
        return x + w + 8

    # ------------------------------------------------- official AWS icons
    def icon(self, name, x, y, size=56):
        """Draw an official AWS Architecture Icon (top-left x, y)."""
        self.c.drawImage(ImageReader(os.path.join(ICON_DIR, name + ".png")), x, self.Y(y + size), size, size, mask="auto")

    def tile(self, cx, y, name, label, sub="", size=64):
        """AWS-diagram style service tile: icon with the service name underneath."""
        self.icon(name, cx - size / 2, y, size)
        c = self.c
        c.setFillColor(DARK); c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(cx, self.Y(y + size + 16), label)
        if sub:
            c.setFillColor(GREY); c.setFont("Helvetica", 11)
            c.drawCentredString(cx, self.Y(y + size + 31), sub)

    def group(self, x, y, w, h, label, kind="cloud"):
        """Official AWS group box: 'cloud' (solid squid ink) or 'region' (dashed teal)."""
        c = self.c
        col = DARK if kind == "cloud" else AWS_TEAL
        c.setStrokeColor(col); c.setLineWidth(1.6)
        if kind == "region": c.setDash(6, 4)
        c.rect(x, self.Y(y + h), w, h, fill=0, stroke=1); c.setDash()
        self.icon("group-aws-cloud" if kind == "cloud" else "group-region", x, y, 30)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 13)
        c.drawString(x + 38, self.Y(y + 20), label)

    def save(self):
        self.c.showPage(); self.c.save()
