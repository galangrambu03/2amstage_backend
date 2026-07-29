import base64
from app import create_app
from app.models.ticket import Ticket

app = create_app()

with app.app_context():
    ticket_id = 1

    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        print("❌ Tiket tidak ditemukan")
    else:
        print("Ticket code:", ticket.ticket_code)
        print("Status:", ticket.status)

        img_data = base64.b64decode(ticket.qr_code_base64)
        filename = f"qr_test_{ticket.ticket_code}.png"

        with open(filename, "wb") as f:
            f.write(img_data)

        print(f"✅ QR berhasil disimpan sebagai {filename}")