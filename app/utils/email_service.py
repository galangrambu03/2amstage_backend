from flask import render_template, current_app
from flask_mail import Message
from PIL import Image
import os
from app import mail
from app.utils.ticket_image import render_tickets_pngs, render_tickets_pdf


def _format_idr(amount):
    return f"Rp {amount:,.0f}".replace(",", ".")


def _format_tanggal(tanggal):
    if not tanggal:
        return "-"
    hari = tanggal.strftime("%A")
    bulan = tanggal.strftime("%B")
    return f"{hari}, {tanggal.day} {bulan} {tanggal.year}"


def _load_poster_image(event):
    """Best-effort: load the event poster from local disk (Flask static/uploads)
    so the ticket image can use it. Returns None if unavailable — the renderer
    falls back to a stylized placeholder in that case."""
    if not event.poster_url:
        return None
    try:
        relative = event.poster_url.lstrip("/")  # e.g. "static/uploads/xxx.jpg"
        filepath = os.path.join(current_app.root_path, relative)
        if not os.path.isfile(filepath):
            return None
        return Image.open(filepath)
    except Exception as e:
        current_app.logger.warning(f"Gagal memuat poster event {event.id} untuk email: {e}")
        return None


def send_ticket_email(user, order, event, tickets, order_details, categories):
    """Best-effort: kirim email tiket setelah pembayaran sukses.
    Tidak melempar exception ke pemanggil — kegagalan kirim email dicatat di log
    saja supaya endpoint pembayaran tetap sukses walau email gagal terkirim.
    """
    if not user.email:
        return False

    try:
        category_by_id = {c.id: c for c in categories}
        category_by_detail = {d.id: category_by_id.get(d.ticket_category_id) for d in order_details}

        items = [
            {
                "nama_kategori": category_by_id.get(d.ticket_category_id).nama_kategori,
                "jumlah": d.jumlah,
                "subtotal_display": _format_idr(float(d.subtotal)),
            }
            for d in order_details
        ]

        html = render_template(
            "email/ticket_email.html",
            user=user,
            order=order,
            event=event,
            items=items,
            tickets=tickets,
            tanggal_display=_format_tanggal(event.tanggal),
            waktu_display=(event.waktu.strftime("%H:%M") + " WIB") if event.waktu else "-",
            total_display=_format_idr(float(order.total_harga)),
        )

        msg = Message(
            subject=f"Tiket kamu untuk {event.nama} sudah siap",
            recipients=[user.email],
            html=html,
        )

        poster_img = _load_poster_image(event)

        for filename, png_bytes in render_tickets_pngs(tickets, event, category_by_detail, order, poster_img=poster_img):
            msg.attach(filename, "image/png", png_bytes)

        pdf_bytes = render_tickets_pdf(tickets, event, category_by_detail, order, poster_img=poster_img)
        if pdf_bytes:
            msg.attach(f"tiket-order-{order.id}.pdf", "application/pdf", pdf_bytes)

        mail.send(msg)
        return True

    except Exception as e:
        current_app.logger.error(f"Gagal mengirim email tiket untuk order {order.id}: {e}")
        return False
