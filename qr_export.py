import base64
import os
import sys
from app import create_app
from app.models.ticket import Ticket
from app.models.order_detail import OrderDetail
from app.models.order import Order

app = create_app()

OUTPUT_DIR = "qr_exports"


def parse_args():
    status_filter = None
    user_filter = None
    order_detail_filter = None

    args = sys.argv[1:]
    if "--status" in args:
        status_filter = args[args.index("--status") + 1]
    if "--user" in args:
        user_filter = int(args[args.index("--user") + 1])
    if "--order-detail" in args:
        order_detail_filter = int(args[args.index("--order-detail") + 1])

    return status_filter, user_filter, order_detail_filter


def main():
    status_filter, user_filter, order_detail_filter = parse_args()

    with app.app_context():
        query = Ticket.query

        if status_filter:
            query = query.filter(Ticket.status == status_filter)

        if order_detail_filter:
            query = query.filter(Ticket.order_detail_id == order_detail_filter)

        if user_filter:
            query = (
                query
                .join(OrderDetail, Ticket.order_detail_id == OrderDetail.id)
                .join(Order, OrderDetail.order_id == Order.id)
                .filter(Order.user_id == user_filter)
            )

        tickets = query.all()

        if not tickets:
            print("⚠️  Tidak ada tiket yang cocok dengan filter.")
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        print(f"Ditemukan {len(tickets)} tiket. Mengekspor ke folder '{OUTPUT_DIR}/'...\n")

        for ticket in tickets:
            if not ticket.qr_code_base64:
                print(f"⏭️  Skip {ticket.ticket_code} (belum punya QR)")
                continue

            img_data = base64.b64decode(ticket.qr_code_base64)
            filename = os.path.join(OUTPUT_DIR, f"{ticket.ticket_code}_{ticket.status}.png")

            with open(filename, "wb") as f:
                f.write(img_data)

            print(f"✅ {ticket.ticket_code}  (status: {ticket.status})  -> {filename}")

        print(f"\nSelesai. Total {len(tickets)} file QR ada di folder '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()