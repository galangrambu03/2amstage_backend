import base64
import os
import requests
from flask import render_template, current_app
from PIL import Image

# Import generator PNG dari ticket_image dan generator PDF baru dari pdf_service
from app.utils.ticket_image import render_tickets_pngs
from app.utils.pdf_service import generate_tickets_pdf


def _format_idr(amount):
    return f"Rp {amount:,.0f}".replace(",", ".")


def _format_tanggal(tanggal):
    if not tanggal:
        return "-"
    hari = tanggal.strftime("%A")
    bulan = tanggal.strftime("%B")
    return f"{hari}, {tanggal.day} {bulan} {tanggal.year}"


def _load_poster_image(event):
    if not event.poster_url:
        return None

    try:
        relative = event.poster_url.lstrip("/")
        filepath = os.path.join(current_app.root_path, relative)

        if not os.path.isfile(filepath):
            return None

        return Image.open(filepath)

    except Exception:
        current_app.logger.exception("Gagal memuat poster")
        return None


def send_ticket_email(user, order, event, tickets, order_details, categories):
    if not user.email:
        current_app.logger.warning("User tidak memiliki email.")
        return False

    try:
        current_app.logger.info("========== EMAIL DEBUG (BREVO API) ==========")
        
        # Ambil API Key dari Config / Environment
        api_key = current_app.config.get("BREVO_API_KEY") or os.getenv("BREVO_API_KEY")
        
        if not api_key:
            current_app.logger.error("BREVO_API_KEY belum dikonfigurasi!")
            return False

        category_by_id = {c.id: c for c in categories}
        category_by_detail = {
            d.id: category_by_id.get(d.ticket_category_id)
            for d in order_details
        }

        tanggal_display = _format_tanggal(event.tanggal)
        waktu_display = (event.waktu.strftime("%H:%M") + " WIB") if event.waktu else "-"

        items = [
            {
                "nama_kategori": category_by_id.get(d.ticket_category_id).nama_kategori,
                "jumlah": d.jumlah,
                "subtotal_display": _format_idr(float(d.subtotal)),
            }
            for d in order_details
        ]

        # 1. Render isi email HTML
        html_content = render_template(
            "email/ticket_email.html",
            user=user,
            order=order,
            event=event,
            items=items,
            tickets=tickets,
            tanggal_display=tanggal_display,
            waktu_display=waktu_display,
            total_display=_format_idr(float(order.total_harga)),
        )

        poster_img = _load_poster_image(event)

        # List untuk menampung semua attachment dalam format Base64
        attachments = []

        # 2. Attach PNG Tiket (Opsional)
        for filename, png_bytes in render_tickets_pngs(
            tickets,
            event,
            category_by_detail,
            order,
            poster_img=poster_img,
        ):
            attachments.append({
                "name": filename,
                "content": base64.b64encode(png_bytes).decode('utf-8')
            })

        # 3. Attach PDF Tiket (Menggunakan HTML Template ticket_pdf.html & Playwright)
        pdf_bytes = generate_tickets_pdf(
            tickets=tickets,
            event=event,
            category_by_detail=category_by_detail,
            order=order,
            tanggal_display=tanggal_display,
            waktu_display=waktu_display
        )

        if pdf_bytes:
            attachments.append({
                "name": f"tiket-order-{order.id}.pdf",
                "content": base64.b64encode(pdf_bytes).decode('utf-8')
            })

        # Menyiapkan payload untuk Brevo REST API
        sender_email = current_app.config.get("MAIL_DEFAULT_SENDER_EMAIL", "galangciko86@gmail.com")
        sender_name = current_app.config.get("MAIL_DEFAULT_SENDER_NAME", "2AMSTAGE")

        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": user.email,
                    "name": getattr(user, 'nama', user.email)
                }
            ],
            "subject": f"Tiket kamu untuk {event.nama} sudah siap",
            "htmlContent": html_content,
            "attachment": attachments
        }

        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        current_app.logger.info("Mengirim email via Brevo REST API...")
        
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code in [200, 201, 202]:
            current_app.logger.info(f"EMAIL BERHASIL TERKIRIM! Response: {response.json()}")
            return True
        else:
            current_app.logger.error(f"GAGAL MENGIRIM EMAIL (Status {response.status_code}): {response.text}")
            return False

    except Exception:
        current_app.logger.exception("GAGAL MENGIRIM EMAIL (EXCEPTION)")
        return False