import base64
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops

# --- Colors matching the screenshot design ---
C_BG = (14, 14, 18)            # Deep dark background
C_CARD = (22, 22, 26)          # Card surface color
C_CATEGORY = (255, 75, 85)     # Coral / Pinkish Red ("TIKET")
C_WHITE = (255, 255, 255)      # Primary Title & Details
C_MUTED = (156, 163, 175)      # Subtitle / Muted text
C_DIM = (100, 110, 125)        # Code / Dim text
C_YELLOW = (234, 200, 20)      # Bright Yellow for "Simpan" action link
C_ICON = (214, 217, 224)       # Soft neutral for calendar/clock/pin icons — blends with text, not loud

# Status colors
C_GREEN_TEXT = (34, 197, 94)   # Bright green text & outline
C_GREEN_BG = (6, 40, 25)       # Dark green pill fill
C_DASH_LINE = (50, 52, 65)     # Dashed separator line

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

# High DPI scale factor (2x crisp resolution)
_S = 2
W_OUT, H_OUT = 1000, 340
W, H = W_OUT * _S, H_OUT * _S
POSTER_W = 230 * _S
STUB_W = 230 * _S
RADIUS = 24 * _S


def _font(weight, size):
    """Loads font with scaled pixel size for high DPI rendering."""
    for path in _FONT_PATHS.get(weight, []):
        try:
            return ImageFont.truetype(path, size * _S)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _format_tanggal(tanggal):
    if not tanggal:
        return "Senin, 10 Agu 2026"
    
    bulan_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
        7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
    }
    hari_map = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    
    try:
        nama_hari = hari_map.get(tanggal.strftime('%A'), tanggal.strftime('%A'))
        nama_bulan = bulan_map.get(tanggal.month, tanggal.strftime('%b'))
        return f"{nama_hari}, {tanggal.day} {nama_bulan} {tanggal.year}"
    except Exception:
        return str(tanggal)


def _format_waktu(waktu):
    if not waktu:
        return "19:00 WIB"
    try:
        return waktu.strftime("%H:%M") + " WIB"
    except Exception:
        return str(waktu)


# --- Vector Icon Drawing Functions ---

def _draw_calendar_icon(draw, x, y, size, color):
    w = max(2, size // 12)
    top = y + size * 0.2
    # Thin outline box only — no filled header bar, keeps it looking light
    draw.rounded_rectangle([x, top, x + size, y + size], radius=size * 0.14, outline=color, width=w)
    draw.line([(x + w, top + size * 0.24), (x + size - w, top + size * 0.24)], fill=color, width=w)
    # Small ring pegs at top
    draw.line([(x + size * 0.28, y), (x + size * 0.28, top + size * 0.12)], fill=color, width=w)
    draw.line([(x + size * 0.72, y), (x + size * 0.72, top + size * 0.12)], fill=color, width=w)


def _draw_clock_icon(draw, x, y, size, color):
    w = max(2, size // 10)
    draw.ellipse([x, y, x + size, y + size], outline=color, width=w)
    cx, cy = x + size / 2, y + size / 2
    draw.line([(cx, cy), (cx, y + size * 0.25)], fill=color, width=w)
    draw.line([(cx, cy), (cx + size * 0.25, cy)], fill=color, width=w)


def _draw_pin_icon(draw, x, y, size, color):
    w = max(2, size // 10)
    r = size * 0.35
    cx, cy = x + size / 2, y + r
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    ir = size * 0.12
    draw.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=color)
    draw.line([(cx - r * 0.7, cy + r * 0.6), (cx, y + size)], fill=color, width=w)
    draw.line([(cx + r * 0.7, cy + r * 0.6), (cx, y + size)], fill=color, width=w)


def _draw_download_icon(draw, x, y, size, color):
    w = max(2, size // 10)
    cx = x + size / 2
    draw.line([(cx, y), (cx, y + size * 0.6)], fill=color, width=w)
    draw.line([(cx - size * 0.25, y + size * 0.35), (cx, y + size * 0.6)], fill=color, width=w)
    draw.line([(cx + size * 0.25, y + size * 0.35), (cx, y + size * 0.6)], fill=color, width=w)
    draw.line([(x + size * 0.1, y + size * 0.85), (x + size * 0.9, y + size * 0.85)], fill=color, width=w)


def _draw_dashed_line(draw, x, y_start, y_end, color, dash_len=10, gap_len=8, width=3):
    for y in range(y_start, y_end, dash_len + gap_len):
        draw.line([(x, y), (x, min(y + dash_len, y_end))], fill=color, width=width)


def _poster_panel(poster_img, event_name):
    """Renders crisp poster image cleanly fitted to the left panel."""
    panel = Image.new("RGB", (POSTER_W, H), C_CARD)
    
    if poster_img:
        try:
            if isinstance(poster_img, bytes):
                src = Image.open(io.BytesIO(poster_img)).convert("RGB")
            elif isinstance(poster_img, str):
                src = Image.open(poster_img).convert("RGB")
            else:
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
            return panel
        except Exception:
            pass

    # Default fallback poster if image is missing
    d = ImageDraw.Draw(panel)
    d.rectangle([0, 0, POSTER_W, H], fill=(30, 28, 40))
    f_mono = _font("bold", 18)
    label = (event_name or "STAGE").upper()[:18]
    d.text((20 * _S, H // 2), label, font=f_mono, fill=C_MUTED)
    return panel


def render_ticket_png(ticket, event, category, order, poster_img=None):
    """Draws a clean, human-readable ticket card identical to the UI design."""
    
    # 1. Base Card Image
    card = Image.new("RGB", (W, H), C_CARD)
    draw = ImageDraw.Draw(card)

    # 2. Poster Panel (Left)
    artis_name = getattr(event, 'artis', None) or getattr(event, 'nama', 'Konser')
    panel = _poster_panel(poster_img, artis_name)
    card.paste(panel, (0, 0))

    # 3. Fonts Setup (Readable & Scaled)
    f_cat = _font("bold", 14)
    f_title = _font("bold", 30)
    f_sub = _font("regular", 18)
    f_meta = _font("regular", 17)
    f_badge = _font("bold", 14)
    f_code = _font("regular", 13)
    f_simpan = _font("bold", 15)

    # Main Area Coordinates
    x = POSTER_W + 35 * _S
    stub_x = W - STUB_W

    # 4. Header / Category ("TIKET")
    cat_text = getattr(category, 'nama_kategori', None) or "TIKET"
    draw.text((x, 32 * _S), cat_text.upper(), font=f_cat, fill=C_CATEGORY)

    # 5. Artist Title & Event Subtitle
    draw.text((x, 62 * _S), artis_name, font=f_title, fill=C_WHITE)
    
    curr_y = 118 * _S
    event_nama = getattr(event, 'nama', None)
    if event_nama and event_nama != artis_name:
        draw.text((x, curr_y), event_nama, font=f_sub, fill=C_MUTED)
        curr_y += 36 * _S
    else:
        curr_y += 8 * _S

    # 6. Details Row 1: Tanggal & Waktu (Side-by-Side)
    tgl_text = _format_tanggal(getattr(event, 'tanggal', None))
    wkt_text = _format_waktu(getattr(event, 'waktu', None))

    icon_s = 20 * _S
    _draw_calendar_icon(draw, x, curr_y + 2 * _S, icon_s, C_WHITE)
    draw.text((x + 28 * _S, curr_y), tgl_text, font=f_meta, fill=C_WHITE)

    # Calculate offset for Clock Icon
    tgl_bbox = draw.textbbox((0, 0), tgl_text, font=f_meta)
    clock_x = x + 28 * _S + (tgl_bbox[2] - tgl_bbox[0]) + 35 * _S

    _draw_clock_icon(draw, clock_x, curr_y + 2 * _S, icon_s, C_YELLOW)
    draw.text((clock_x + 28 * _S, curr_y), wkt_text, font=f_meta, fill=C_WHITE)

    # 7. Details Row 2: Lokasi
    curr_y += 42 * _S
    lokasi_text = getattr(event, 'lokasi', '-') or '-'
    _draw_pin_icon(draw, x, curr_y + 2 * _S, icon_s, C_WHITE)
    draw.text((x + 28 * _S, curr_y), lokasi_text, font=f_meta, fill=C_WHITE)

    # 8. Status Badge ("AKTIF") - Top Right
    badge_label = "AKTIF" if ticket.status == "unused" else "SUDAH DIPAKAI"
    badge_color = C_GREEN_TEXT if ticket.status == "unused" else C_MUTED
    badge_bg = C_GREEN_BG if ticket.status == "unused" else (35, 35, 45)

    badge_bbox = draw.textbbox((0, 0), badge_label, font=f_badge)
    bw = badge_bbox[2] - badge_bbox[0] + 50 * _S
    bh = 34 * _S
    badge_x = stub_x - bw - 35 * _S
    badge_y = 32 * _S

    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + bw, badge_y + bh],
        radius=bh // 2, fill=badge_bg, outline=badge_color, width=2 * _S
    )
    
    # Checkmark Icon inside Badge
    chk_cx, chk_cy = badge_x + 18 * _S, badge_y + bh // 2
    r_c = 6 * _S
    draw.ellipse([chk_cx - r_c, chk_cy - r_c, chk_cx + r_c, chk_cy + r_c], outline=badge_color, width=2 * _S)
    draw.line([(chk_cx - 3 * _S, chk_cy), (chk_cx - 1 * _S, chk_cy + 2 * _S), (chk_cx + 3 * _S, chk_cy - 3 * _S)], fill=badge_color, width=2 * _S)
    
    draw.text((badge_x + 32 * _S, badge_y + 6 * _S), badge_label, font=f_badge, fill=badge_color)

    # 9. Vertical Dashed Divider
    _draw_dashed_line(draw, stub_x, 15 * _S, H - 15 * _S, C_DASH_LINE, dash_len=12 * _S, gap_len=8 * _S, width=2 * _S)

    # 10. Stub Right Side (QR Code & Actions)
    qr_box_size = 175 * _S
    qr_cx = stub_x + (STUB_W // 2)
    qr_top_y = 30 * _S

    # QR Container Box (White Rounded Square)
    draw.rounded_rectangle(
        [qr_cx - qr_box_size // 2, qr_top_y, qr_cx + qr_box_size // 2, qr_top_y + qr_box_size],
        radius=18 * _S, fill=(255, 255, 255)
    )

    # Paste QR Image
    if getattr(ticket, 'qr_code_base64', None):
        try:
            qr_raw = base64.b64decode(ticket.qr_code_base64)
            qr_img = Image.open(io.BytesIO(qr_raw)).convert("RGB")
            pad = 12 * _S
            qr_size = qr_box_size - (pad * 2)
            qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
            card.paste(qr_img, (qr_cx - qr_size // 2, qr_top_y + pad))
        except Exception:
            pass

    # Ticket Code
    tck_code = getattr(ticket, 'ticket_code', 'TCK-000000')
    code_bbox = draw.textbbox((0, 0), tck_code, font=f_code)
    code_w = code_bbox[2] - code_bbox[0]
    code_y = qr_top_y + qr_box_size + 16 * _S
    draw.text((qr_cx - code_w // 2, code_y), tck_code, font=f_code, fill=C_DIM)

    # "Simpan" Link Action
    simpan_y = code_y + 32 * _S
    simpan_text = "Simpan"
    s_bbox = draw.textbbox((0, 0), simpan_text, font=f_simpan)
    s_w = s_bbox[2] - s_bbox[0]
    total_simpan_w = s_w + 22 * _S
    simpan_x = qr_cx - total_simpan_w // 2

    _draw_download_icon(draw, simpan_x, simpan_y + 2 * _S, 16 * _S, C_YELLOW)
    draw.text((simpan_x + 22 * _S, simpan_y), simpan_text, font=f_simpan, fill=C_YELLOW)

    # 11. Apply Card Notches & Rounded Corners
    notch_r = 28 * _S
    cy = H // 2
    
    # Transparency mask
    mask = Image.new("L", (W, H), 255)
    mdraw = ImageDraw.Draw(mask)
    
    # Outer Rounded Corners
    mdraw.rounded_rectangle([0, 0, W, H], radius=RADIUS, fill=255)
    
    # Left & Right Edge Semi-circle Notches
    mdraw.ellipse([-notch_r, cy - notch_r, notch_r, cy + notch_r], fill=0)
    mdraw.ellipse([W - notch_r, cy - notch_r, W + notch_r, cy + notch_r], fill=0)

    # Final Composite
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(card.convert("RGBA"), (0, 0), mask)

    # Supersampled Downscale for Super Sharp Anti-Aliasing
    return canvas.resize((W_OUT, H_OUT), Image.LANCZOS)


# --- Functions used by email_service.py ---

def render_tickets_pngs(tickets, event, category_map, order, poster_img=None):
    """Returns list of (filename, png_bytes) for each ticket."""
    results = []
    for t in tickets:
        cat = category_map.get(t.order_detail_id) if isinstance(category_map, dict) else category_map
        img = render_ticket_png(t, event, cat, order, poster_img=poster_img)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        results.append((f"{t.ticket_code}.png", buf.getvalue()))
    return results


def render_tickets_pdf(tickets, event, category_map, order, poster_img=None):
    """Returns a single multi-page PDF (bytes) containing all tickets, one per page."""
    images = []
    for t in tickets:
        cat = category_map.get(t.order_detail_id) if isinstance(category_map, dict) else category_map
        img = render_ticket_png(t, event, cat, order, poster_img=poster_img).convert("RGB")
        images.append(img)

    if not images:
        return None
    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()