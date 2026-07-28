import qrcode
import io
import base64
import uuid


def generate_ticket_code():
    return f"TCK-{uuid.uuid4().hex[:12].upper()}"


def generate_qr_base64(data: str) -> str:
    qr = qrcode.make(data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")