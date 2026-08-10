from flask import render_template, current_app
from playwright.sync_api import sync_playwright

def generate_tickets_pdf(tickets, event, category_by_detail, order, tanggal_display, waktu_display):
    """
    Merender template 'email/ticket_pdf.html' dan mengonversinya
    menjadi file PDF (bytes) menggunakan Playwright.
    """
    try:
        # Susun pasangan tiket dan kategorinya
        tickets_data = []
        for t in tickets:
            cat = category_by_detail.get(t.order_detail_id)
            tickets_data.append({
                "ticket": t,
                "category": cat
            })

        # 1. Render template HTML PDF
        html_content = render_template(
            "email/ticket_pdf.html",
            event=event,
            order=order,
            tickets_data=tickets_data,
            tanggal_display=tanggal_display,
            waktu_display=waktu_display
        )

        # 2. Gunakan Playwright untuk merender ke PDF
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page()
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