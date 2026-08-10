import os
import base64
from flask import render_template, current_app
from playwright.sync_api import sync_playwright

def _image_to_base64(filepath):
    """Membaca file gambar lokal dan mengubahnya ke string Base64."""
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            ext = os.path.splitext(filepath)[1].lstrip(".").lower()
            mime_type = "image/png" if ext == "png" else "image/jpeg"
            return f"data:{mime_type};base64,{encoded_string}"
    except Exception:
        return None

def generate_tickets_pdf(tickets, event, category_by_detail, order, tanggal_display, waktu_display):
    try:
        # 1. Konversi poster_url ke Base64 agar terbaca 100% oleh Playwright
        poster_base64 = None
        if getattr(event, 'poster_url', None):
            relative_path = event.poster_url.lstrip("/")
            full_path = os.path.join(current_app.root_path, relative_path)
            poster_base64 = _image_to_base64(full_path)

        # 2. Susun data tiket
        tickets_data = []
        for t in tickets:
            cat = category_by_detail.get(t.order_detail_id)
            tickets_data.append({
                "ticket": t,
                "category": cat
            })

        # 3. Render HTML
        html_content = render_template(
            "email/ticket_pdf.html",
            event=event,
            order=order,
            tickets_data=tickets_data,
            tanggal_display=tanggal_display,
            waktu_display=waktu_display,
            poster_base64=poster_base64  # Kirimkan data poster Base64
        )

        # 4. Render ke PDF via Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page()
            # Set content dan tunggu sampai gambar & font selesai dimuat
            page.set_content(html_content, wait_until="networkidle")
            
            pdf_bytes = page.pdf(
                print_background=True,
                prefer_css_page_size=True
            )
            browser.close()

        return pdf_bytes

    except Exception:
        current_app.logger.exception("GAGAL MENG-GENERATE PDF TIKET VIA PLAYWRIGHT")
        return None