import base64
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- Theme colors (matches tailwind.config.js) ---
C_VOID = (11, 10, 16)
C_SURFACE = (22, 20, 30)
C_SURFACE2 = (32, 29, 43)
C_SURFACE3 = (42, 38, 55)
C_STAGE = (255, 46, 99)
C_AMBER = (255, 201, 60)
C_VIOLET = (140, 111, 255)
C_HI = (247, 245, 251)
C_MID = (180, 175, 199)
C_DIM = (113, 108, 135)
C_GREEN = (52, 199, 132)

_FONT_PATHS = {
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}

# Rendered at 2x for crisp attachments, then downsampled at the end.
_S = 2
W, H = 1200 * _S, 380 * _S
POSTER_W = 240 * _S
RADIUS = 28 * _S


def _font(weight, size):
    for path in _FONT_PATHS.get(weight, []):
        try:
            return ImageFont.truetype(path, size * _S)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _format_tanggal(tanggal):
    if not tanggal:
        return "-"
    return f"{tanggal.strftime('%A')}, {tanggal.day} {tanggal.strftime('%b')} {tanggal.year}"


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _diagonal_gradient(size, c1, c2):
    w, h = size
    grad = Image.new("RGB", size)
    px = grad.load()
    for y in range(h):
        t_row = y / max(h - 1, 1)
        for x in range(0, w, 4):
            t = (t_row + (x / max(w - 1, 1))) / 2
            col = _lerp_color(c1, c2, min(t, 1))
            for dx in range(4):
                if x + dx < w:
                    px[x + dx, y] = col
    return grad


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _poster_panel(poster_img, event_label):
    """Real poster (cover-fit + dark scrim for legibility) if provided,
    otherwise a stylized gradient placeholder with a spotlight glow."""
    if poster_img:
        src = poster_img.convert("RGB")
        src_ratio = src.width / src.height
        dst_ratio = POSTER_W / H
        if src_ratio > dst_ratio:
            new_h = H
            new_w = int(H * src_ratio)
        else:
            new_w = POSTER_W
            new_h = int(POSTER_W / src_ratio)
        src = src.resize((new_w, new_h))
        left = (new_w - POSTER_W) // 2
        top = (new_h - H) // 2
        panel = src.crop((left, top, left + POSTER_W, top + H))

        scrim = Image.new("L", (POSTER_W, H), 0)
        sd = ImageDraw.Draw(scrim)
        for xx in range(POSTER_W):
            t = xx / max(POSTER_W - 1, 1)
            sd.line([(xx, 0), (xx, H)], fill=int(60 + 140 * t))
        black = Image.new("RGB", (POSTER_W, H), C_VOID)
        panel = Image.composite(black, panel, scrim)
        return panel

    panel = _diagonal_gradient((POSTER_W, H), C_SURFACE3, (26, 22, 36))
    glow = Image.new("RGBA", (POSTER_W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = POSTER_W // 2, int(H * 0.32)
    gd.ellipse((cx - 160 * _S, cy - 160 * _S, cx + 160 * _S, cy + 160 * _S), fill=(*C_STAGE, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(60 * _S))
    panel = Image.alpha_composite(panel.convert("RGBA"), glow).convert("RGB")

    d = ImageDraw.Draw(panel)
    f_mono = _font("bold", 15)
    label = (event_label or "2AMSTAGE")[:22].upper()
    d.text((28 * _S, H - 46 * _S), label, font=f_mono, fill=C_MID)
    return panel


def _perforation(draw, x, top, bottom, bg_color):
    """Scalloped edge: a column of small circles cut into the card border,
    mimicking a torn ticket stub."""
    notch_r = 9 * _S
    gap = 22 * _S
    y = top
    while y < bottom:
        draw.ellipse((x - notch_r, y - notch_r, x + notch_r, y + notch_r), fill=bg_color)
        y += gap


def render_ticket_png(ticket, event, category, order, poster_img=None):
    """Draws one ticket card as a PNG, styled like the web ticket stub."""
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    card = Image.new("RGB", (W, H), C_SURFACE)
    draw = ImageDraw.Draw(card)

    panel = _poster_panel(poster_img, event.artis or event.nama)
    card.paste(panel, (0, 0))

    _perforation(draw, POSTER_W, -10 * _S, H + 10 * _S, C_SURFACE)

    f_label = _font("bold", 20)
    f_title = _font("bold", 42)
    f_sub = _font("regular", 22)
    f_meta_label = _font("bold", 15)
    f_meta_val = _font("regular", 20)
    f_badge = _font("bold", 17)
    f_code = _font("regular", 16)
    f_brand = _font("bold", 18)

    x = POSTER_W + 50 * _S
    draw.text((x, 30 * _S), "T I K E T", font=f_label, fill=C_AMBER)
    draw.text((x, 60 * _S), event.artis or event.nama, font=f_title, fill=C_HI)
    draw.text((x, 116 * _S), event.nama, font=f_sub, fill=C_MID)

    tanggal = _format_tanggal(event.tanggal)
    waktu = (event.waktu.strftime("%H:%M") + " WIB") if event.waktu else "-"
    meta_y = 168 * _S
    meta_gap = 30 * _S
    for i, (label, val) in enumerate([("TANGGAL", tanggal), ("WAKTU", waktu), ("LOKASI", event.lokasi)]):
        ly = meta_y + i * meta_gap
        draw.text((x, ly), label, font=f_meta_label, fill=C_DIM)
        draw.text((x + 110 * _S, ly - 2 * _S), val, font=f_meta_val, fill=C_HI)

    pill_y = meta_y + 3 * meta_gap + 8 * _S
    cat_text = category.nama_kategori
    cbbox = draw.textbbox((0, 0), cat_text, font=f_meta_label)
    cw, ch = cbbox[2] - cbbox[0] + 28 * _S, cbbox[3] - cbbox[1] + 16 * _S
    draw.rounded_rectangle((x, pill_y, x + cw, pill_y + ch), radius=ch // 2, outline=C_STAGE, width=2 * _S)
    draw.text((x + 14 * _S, pill_y + 8 * _S), cat_text, font=f_meta_label, fill=C_STAGE)

    badge_active = ticket.status == "unused"
    badge_text = "AKTIF" if badge_active else ("SUDAH DIPAKAI" if ticket.status == "used" else "TIDAK BERLAKU")
    badge_color = C_GREEN if badge_active else C_DIM
    bbox = draw.textbbox((0, 0), badge_text, font=f_badge)
    bw, bh = bbox[2] - bbox[0] + 52 * _S, bbox[3] - bbox[1] + 18 * _S
    badge_x = W - 280 * _S - bw
    draw.rounded_rectangle((badge_x, 28 * _S, badge_x + bw, 28 * _S + bh), radius=bh // 2, outline=badge_color, width=int(1.5 * _S))
    icon_cx, icon_cy = badge_x + 20 * _S, 28 * _S + bh // 2
    icon_r = 9 * _S
    draw.ellipse((icon_cx - icon_r, icon_cy - icon_r, icon_cx + icon_r, icon_cy + icon_r), outline=badge_color, width=int(1.5 * _S))
    if badge_active:
        draw.line(
            [(icon_cx - 4 * _S, icon_cy), (icon_cx - 1 * _S, icon_cy + 3 * _S), (icon_cx + 4 * _S, icon_cy - 4 * _S)],
            fill=badge_color, width=int(1.5 * _S), joint="curve"
        )
    else:
        draw.line((icon_cx - 4 * _S, icon_cy - 4 * _S, icon_cx + 4 * _S, icon_cy + 4 * _S), fill=badge_color, width=int(1.5 * _S))
        draw.line((icon_cx - 4 * _S, icon_cy + 4 * _S, icon_cx + 4 * _S, icon_cy - 4 * _S), fill=badge_color, width=int(1.5 * _S))
    draw.text((badge_x + 36 * _S, 28 * _S + 9 * _S), badge_text, font=f_badge, fill=badge_color)

    qr_size = 190 * _S
    qr_x = W - qr_size - 55 * _S
    qr_y = (H - qr_size) // 2

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = 14 * _S
    sd.rounded_rectangle(
        (qr_x - pad, qr_y - pad + 10 * _S, qr_x + qr_size + pad, qr_y + qr_size + pad + 10 * _S),
        radius=16 * _S, fill=(0, 0, 0, 120)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14 * _S))
    card = Image.alpha_composite(card.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(card)

    draw.rounded_rectangle(
        (qr_x - pad, qr_y - pad, qr_x + qr_size + pad, qr_y + qr_size + pad), radius=16 * _S, fill=C_HI
    )
    if ticket.qr_code_base64:
        qr_img = Image.open(io.BytesIO(base64.b64decode(ticket.qr_code_base64))).convert("RGB")
        qr_img = qr_img.resize((qr_size, qr_size))
        card.paste(qr_img, (qr_x, qr_y))

    code_bbox = draw.textbbox((0, 0), ticket.ticket_code, font=f_code)
    code_w = code_bbox[2] - code_bbox[0]
    draw.text(
        (qr_x + qr_size / 2 - code_w / 2, qr_y + qr_size + pad + 14 * _S),
        ticket.ticket_code, font=f_code, fill=C_DIM
    )

    draw.line((POSTER_W, H - 2 * _S, W, H - 2 * _S), fill=C_SURFACE2, width=2 * _S)
    draw.text((x, H - 40 * _S), "2AM", font=f_brand, fill=C_HI)
    bx = x + draw.textbbox((0, 0), "2AM", font=f_brand)[2]
    draw.text((bx, H - 40 * _S), "STAGE", font=f_brand, fill=C_STAGE)

    accent_h = 8 * _S
    accent = _diagonal_gradient((W, accent_h), C_STAGE, C_VIOLET)
    card.paste(accent, (0, 0))

    mask = _rounded_mask((W, H), RADIUS)
    base.paste(card, (0, 0), mask)

    return base.convert("RGB").resize((W // _S, H // _S), Image.LANCZOS)


def render_tickets_pngs(tickets, event, category_map, order, poster_img=None):
    """Returns list of (filename, png_bytes) for each ticket."""
    results = []
    for t in tickets:
        category = category_map[t.order_detail_id]
        img = render_ticket_png(t, event, category, order, poster_img=poster_img)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        results.append((f"{t.ticket_code}.png", buf.getvalue()))
    return results


def render_tickets_pdf(tickets, event, category_map, order, poster_img=None):
    """Returns a single multi-page PDF (bytes) containing all tickets, one per page."""
    images = [
        render_ticket_png(t, event, category_map[t.order_detail_id], order, poster_img=poster_img).convert("RGB")
        for t in tickets
    ]
    if not images:
        return None
    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()
