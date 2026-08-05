import base64
import io
import math
from PIL import Image, ImageDraw, ImageFont

# --- Theme colors ---
C_BG = (15, 13, 22)
C_CARD = (24, 21, 33)
C_SURFACE = (34, 30, 47)
C_BORDER = (48, 43, 66)

C_ACCENT_AMBER = (255, 184, 76)
C_ACCENT_STAGE = (255, 64, 105)
C_TEXT_MAIN = (248, 247, 252)
C_TEXT_MUTED = (160, 153, 180)
C_TEXT_DIM = (105, 98, 125)

C_STATUS_ACTIVE = (46, 213, 115)
C_STATUS_ACTIVE_BG = (20, 50, 35)
C_STATUS_USED_BG = (40, 35, 50)

_FONT_PATHS = {
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ],
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ],
}


def _font(weight, size):
    for path in _FONT_PATHS.get(weight, []):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _format_tanggal(tanggal):
    if not tanggal:
        return "-"
    return f"{tanggal.strftime('%A')}, {tanggal.day} {tanggal.strftime('%b')} {tanggal.year}"


def _draw_dashed_line(draw, start, end, fill, width=2, dash_len=8, gap_len=6):
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    dist = 0
    
    while dist < length:
        curr_dash = min(dash_len, length - dist)
        sx = x1 + dx * dist
        sy = y1 + dy * dist
        ex = sx + dx * curr_dash
        ey = sy + dy * curr_dash
        draw.line([(sx, sy), (ex, ey)], fill=fill, width=width)
        dist += dash_len + gap_len


def render_ticket_png(ticket, event, category, order, poster_img=None):
    """Draws an aesthetic ticket stub with optional poster image."""
    W, H = 1200, 400
    
    img = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)
    
    card_r = 20
    draw.rounded_rectangle((0, 0, W, H), radius=card_r, fill=C_CARD)

    # 1. Status Indicator Accent Bar
    badge_active = ticket.status == "unused"
    accent_color = C_STATUS_ACTIVE if badge_active else C_TEXT_DIM
    draw.rounded_rectangle((0, 0, 10, H), radius=4, fill=accent_color)

    # 2. Poster Rendering (Kiri)
    poster_w = 200
    poster_loaded = False

    if poster_img:
        try:
            # Jika poster_img dikirim berupa bytes, load dengan Image.open
            if isinstance(poster_img, (bytes, bytearray)):
                p_image = Image.open(io.BytesIO(poster_img)).convert("RGB")
            elif isinstance(poster_img, Image.Image):
                p_image = poster_img.convert("RGB")
            else:
                p_image = None

            if p_image:
                # Resize poster agar pas di area poster_w x H (crop/fit)
                p_ratio = p_image.width / p_image.height
                target_ratio = poster_w / H
                if p_ratio > target_ratio:
                    new_w = int(H * p_ratio)
                    p_resized = p_image.resize((new_w, H), Image.Resampling.LANCZOS)
                    crop_x = (new_w - poster_w) // 2
                    p_cropped = p_resized.crop((crop_x, 0, crop_x + poster_w, H))
                else:
                    new_h = int(poster_w / p_ratio)
                    p_resized = p_image.resize((poster_w, new_h), Image.Resampling.LANCZOS)
                    crop_y = (new_h - H) // 2
                    p_cropped = p_resized.crop((0, crop_y, poster_w, crop_y + H))

                img.paste(p_cropped, (10, 0))
                poster_loaded = True
        except Exception:
            poster_loaded = False

    # Fallback Placeholder jika poster gagal/tidak ada
    if not poster_loaded:
        draw.rectangle((10, 0, poster_w, H), fill=C_SURFACE)
        f_poster_title = _font("bold", 24)
        short_title = (event.artis or event.nama)[:12].upper()
        draw.text((30, H // 2 - 10), short_title, font=f_poster_title, fill=C_BORDER)

    # 3. Main Details Section
    f_badge = _font("bold", 13)
    f_title = _font("bold", 34)
    f_sub = _font("regular", 18)
    f_label = _font("bold", 13)
    f_val = _font("regular", 16)
    f_cat = _font("bold", 18)

    x_start = poster_w + 35
    
    draw.text((x_start, 35), "E-TICKET EVENT", font=f_badge, fill=C_ACCENT_AMBER)
    
    title_text = event.artis or event.nama
    draw.text((x_start, 58), title_text, font=f_title, fill=C_TEXT_MAIN)
    draw.text((x_start, 105), event.nama, font=f_sub, fill=C_TEXT_MUTED)

    tanggal = _format_tanggal(event.tanggal)
    waktu = (event.waktu.strftime("%H:%M") + " WIB") if event.waktu else "-"
    
    draw.text((x_start, 155), "TANGGAL", font=f_label, fill=C_TEXT_DIM)
    draw.text((x_start, 175), tanggal, font=f_val, fill=C_TEXT_MAIN)
    
    draw.text((x_start + 260, 155), "WAKTU", font=f_label, fill=C_TEXT_DIM)
    draw.text((x_start + 260, 175), waktu, font=f_val, fill=C_TEXT_MAIN)

    draw.text((x_start, 215), "LOKASI", font=f_label, fill=C_TEXT_DIM)
    draw.text((x_start, 235), event.lokasi, font=f_val, fill=C_TEXT_MAIN)

    cat_name = category.nama_kategori.upper()
    cat_bbox = draw.textbbox((0, 0), cat_name, font=f_cat)
    cat_w = cat_bbox[2] - cat_bbox[0] + 28
    draw.rounded_rectangle((x_start, 290, x_start + cat_w, 328), radius=8, fill=C_SURFACE)
    draw.text((x_start + 14, 298), cat_name, font=f_cat, fill=C_ACCENT_STAGE)

    # 4. Perforation & Cutouts
    stub_x = W - 280
    _draw_dashed_line(draw, (stub_x, 25), (stub_x, H - 25), fill=C_BORDER, width=2, dash_len=8, gap_len=6)
    
    cutout_r = 16
    draw.ellipse((stub_x - cutout_r, -cutout_r, stub_x + cutout_r, cutout_r), fill=C_BG)
    draw.ellipse((stub_x - cutout_r, H - cutout_r, stub_x + cutout_r, H + cutout_r), fill=C_BG)

    # 5. Status Badge & QR Code
    f_status = _font("bold", 12)
    f_code = _font("bold", 14)

    status_text = "AKTIF" if badge_active else ("SUDAH DIPAKAI" if ticket.status == "used" else "TIDAK BERLAKU")
    status_color = C_STATUS_ACTIVE if badge_active else C_TEXT_DIM
    status_bg = C_STATUS_ACTIVE_BG if badge_active else C_STATUS_USED_BG

    s_bbox = draw.textbbox((0, 0), status_text, font=f_status)
    s_w, s_h = s_bbox[2] - s_bbox[0] + 24, s_bbox[3] - s_bbox[1] + 12
    s_x = stub_x + ((W - stub_x) // 2) - (s_w // 2)
    s_y = 35
    
    draw.rounded_rectangle((s_x, s_y, s_x + s_w, s_y + s_h), radius=s_h // 2, fill=status_bg)
    draw.text((s_x + 12, s_y + 5), status_text, font=f_status, fill=status_color)

    qr_size = 170
    qr_x = stub_x + ((W - stub_x) // 2) - (qr_size // 2)
    qr_y = 95
    
    if ticket.qr_code_base64:
        try:
            qr_img = Image.open(io.BytesIO(base64.b64decode(ticket.qr_code_base64))).convert("RGB")
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            pad = 10
            draw.rounded_rectangle(
                (qr_x - pad, qr_y - pad, qr_x + qr_size + pad, qr_y + qr_size + pad),
                radius=12,
                fill=(255, 255, 255)
            )
            img.paste(qr_img, (qr_x, qr_y))
        except Exception:
            draw.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), fill=C_SURFACE)

    code_text = ticket.ticket_code
    code_bbox = draw.textbbox((0, 0), code_text, font=f_code)
    code_w = code_bbox[2] - code_bbox[0]
    code_x = stub_x + ((W - stub_x) // 2) - (code_w // 2)
    draw.text((code_x, qr_y + qr_size + 22), code_text, font=f_code, fill=C_TEXT_MUTED)

    return img


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
    """Returns a single multi-page PDF (bytes) containing all tickets."""
    images = [
        render_ticket_png(t, event, category_map[t.order_detail_id], order, poster_img=poster_img).convert("RGB")
        for t in tickets
    ]
    if not images:
        return None
    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()