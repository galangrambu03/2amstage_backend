import base64
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# --- Theme colors (Matches Tailwind & React UI) ---
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
C_EMERALD = (52, 211, 153)       # emerald-400
C_EMERALD_BG = (16, 52, 40)     # bg-emerald-400/10

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

_S = 2
W, H = 1200 * _S, 380 * _S
POSTER_W = 240 * _S
STUB_W = 280 * _S
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


def _format_datetime(dt):
    if not dt:
        return "-"
    return dt.strftime("%d %b %Y, %H:%M") + " WIB"


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
        src = src.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - POSTER_W) // 2
        top = (new_h - H) // 2
        panel = src.crop((left, top, left + POSTER_W, top + H))

        # Gradient dark scrim di sisi kanan poster untuk seamless blending
        scrim = Image.new("L", (POSTER_W, H), 0)
        sd = ImageDraw.Draw(scrim)
        for xx in range(POSTER_W):
            t = xx / max(POSTER_W - 1, 1)
            sd.line([(xx, 0), (xx, H)], fill=int(20 + 180 * t))
        black = Image.new("RGB", (POSTER_W, H), C_SURFACE)
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
    notch_r = 10 * _S
    gap = 24 * _S
    y = top
    while y < bottom:
        draw.ellipse((x - notch_r, y - notch_r, x + notch_r, y + notch_r), fill=bg_color)
        y += gap


def render_ticket_png(ticket, event, category, order, poster_img=None):
    """Draws one ticket card as a PNG, mirroring the React QRTicket component strictly."""
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card = Image.new("RGB", (W, H), C_SURFACE)
    draw = ImageDraw.Draw(card)

    # 1. Poster Frame
    panel = _poster_panel(poster_img, event.artis or event.nama)
    card.paste(panel, (0, 0))

    # Perforated Divider (Antara Main & Stub)
    stub_x = W - STUB_W
    _perforation(draw, stub_x, -10 * _S, H + 10 * _S, C_VOID)

    # Fonts
    f_cat = _font("bold", 14)
    f_title = _font("bold", 36)
    f_sub = _font("regular", 20)
    f_meta = _font("regular", 18)
    f_badge = _font("bold", 15)
    f_code = _font("regular", 14)

    x = POSTER_W + 40 * _S

    # 2. Category Label (UPPERCASE Amber)
    cat_name = getattr(category, 'nama_kategori', str(category)) if category else "TIKET"
    draw.text((x, 32 * _S), cat_name.upper(), font=f_cat, fill=C_AMBER)

    # 3. Artis / Title
    title_text = event.artis or event.nama or "Konser"
    draw.text((x, 56 * _S), title_text, font=f_title, fill=C_HI)

    # 4. Subtitle (Event Name if Artis exists)
    curr_y = 112 * _S
    if event.artis and event.nama:
        draw.text((x, curr_y), event.nama, font=f_sub, fill=C_MID)
        curr_y += 32 * _S

    # 5. Metadata Grid (Tanggal, Waktu, Lokasi)
    tanggal = _format_tanggal(event.tanggal) if hasattr(event, 'tanggal') else "-"
    waktu = (event.waktu.strftime("%H:%M") + " WIB") if getattr(event, 'waktu', None) else "-"
    lokasi = getattr(event, 'lokasi', "-")

    meta_y = curr_y + 12 * _S
    draw.text((x, meta_y), f"📅  {tanggal}", font=f_meta, fill=C_MID)
    draw.text((x, meta_y + 32 * _S), f"⏰  {waktu}", font=f_meta, fill=C_MID)
    draw.text((x, meta_y + 64 * _S), f"📍  {lokasi}", font=f_meta, fill=C_MID)

    # 6. Check-in Timestamp (If Used)
    if ticket.status == "used" and getattr(ticket, 'used_at', None):
        draw.text(
            (x, meta_y + 104 * _S),
            f"Check-in pada {_format_datetime(ticket.used_at)}",
            font=f_code,
            fill=C_DIM
        )

    # 7. Status Badge (Dynamic STATUS_MAP like React)
    is_active = ticket.status == "unused"
    if is_active:
        status_label = "Aktif"
        badge_fg = C_EMERALD
        badge_bg = C_EMERALD_BG
    elif ticket.status == "used":
        status_label = "Sudah Check-in"
        badge_fg = C_MID
        badge_bg = C_SURFACE2
    else:
        status_label = "Tidak Berlaku"
        badge_fg = C_STAGE
        badge_bg = (60, 20, 30)

    # Render Badge
    bbox = draw.textbbox((0, 0), status_label, font=f_badge)
    bw = bbox[2] - bbox[0] + 48 * _S
    bh = 32 * _S
    badge_x = stub_x - bw - 30 * _S
    badge_y = 32 * _S

    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + bw, badge_y + bh),
        radius=bh // 2,
        fill=badge_bg,
        outline=badge_fg,
        width=1 * _S
    )

    # Status Icon inside Badge
    ic_x, ic_y = badge_x + 16 * _S, badge_y + bh // 2
    r = 6 * _S
    draw.ellipse((ic_x - r, ic_y - r, ic_x + r, ic_y + r), outline=badge_fg, width=int(1.5 * _S))
    if is_active:
        draw.line([(ic_x - 3*_S, ic_y), (ic_x - 1*_S, ic_y + 2*_S), (ic_x + 3*_S, ic_y - 3*_S)], fill=badge_fg, width=2*_S)
    else:
        draw.line((ic_x - 3*_S, ic_y - 3*_S, ic_x + 3*_S, ic_y + 3*_S), fill=badge_fg, width=2*_S)
        draw.line((ic_x - 3*_S, ic_y + 3*_S, ic_x + 3*_S, ic_y - 3*_S), fill=badge_fg, width=2*_S)

    draw.text((badge_x + 30 * _S, badge_y + 6 * _S), status_label, font=f_badge, fill=badge_fg)

    # 8. Stub Right Side (QR Code & Ticket Code)
    qr_size = 180 * _S
    qr_x = stub_x + (STUB_W - qr_size) // 2
    qr_y = (H - qr_size) // 2 - 15 * _S

    # Shadow for QR
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = 12 * _S
    sd.rounded_rectangle(
        (qr_x - pad, qr_y - pad, qr_x + qr_size + pad, qr_y + qr_size + pad),
        radius=16 * _S, fill=(0, 0, 0, 140)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10 * _S))
    card = Image.alpha_composite(card.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(card)

    # QR Background Box
    draw.rounded_rectangle(
        (qr_x - pad, qr_y - pad, qr_x + qr_size + pad, qr_y + qr_size + pad),
        radius=16 * _S, fill=C_HI
    )

    if ticket.qr_code_base64:
        qr_img = Image.open(io.BytesIO(base64.b64decode(ticket.qr_code_base64))).convert("RGB")
        qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
        card.paste(qr_img, (qr_x, qr_y))

    # Ticket Code under QR
    code_bbox = draw.textbbox((0, 0), ticket.ticket_code, font=f_code)
    code_w = code_bbox[2] - code_bbox[0]
    draw.text(
        (qr_x + (qr_size // 2) - (code_w // 2), qr_y + qr_size + pad + 12 * _S),
        ticket.ticket_code, font=f_code, fill=C_DIM
    )

    # Accent Top Line Gradient
    accent = _diagonal_gradient((W, 6 * _S), C_STAGE, C_VIOLET)
    card.paste(accent, (0, 0))

    # Apply Card Mask
    mask = _rounded_mask((W, H), RADIUS)
    base.paste(card, (0, 0), mask)

    # 9. If Status != unused (Used/Void), Apply Grayscale & Opacity Effect (Mirrors React `opacity-60 grayscale`)
    if ticket.status != "unused":
        # Convert to Grayscale & back to RGB
        gray_card = ImageOps.grayscale(base.convert("RGB")).convert("RGB")
        # Blend original color with grayscale (60% opacity look)
        base = Image.blend(gray_card, base.convert("RGB"), alpha=0.35).convert("RGBA")

    # Downsample for Anti-Aliasing Crisp Output
    return base.convert("RGB").resize((W // _S, H // _S), Image.LANCZOS)