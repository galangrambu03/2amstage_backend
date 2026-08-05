import cv2
from pyzbar.pyzbar import decode
import requests

API_URL = "http://127.0.0.1:5000/api/tickets/validate"
TOKEN_PETUGAS = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc4NTMwOTEzNywianRpIjoiMDNlMjlmNDItYjgxYS00ZTdlLTkyODgtMTViZTQyMTlhOGQ3IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjciLCJuYmYiOjE3ODUzMDkxMzcsImNzcmYiOiJkMWYwOTAxNC04YzBiLTRkYjktYmM1Mi04MDU2MjQ1N2RhNDgiLCJleHAiOjE3ODUzMTAwMzcsInJvbGUiOiJwZXR1Z2FzIn0._Y6VlXPyA_pDoOem_LMEqBaKwyCmRT7VskWm_QgAl0o" 


def validate_ticket(ticket_code):
    headers = {"Authorization": f"Bearer {TOKEN_PETUGAS}"}
    body = {"ticket_code": ticket_code}

    try:
        res = requests.post(API_URL, json=body, headers=headers, timeout=5)
        data = res.json()
        return res.status_code, data
    except Exception as e:
        return None, {"message": f"Gagal konek ke backend: {e}"}


def main():
    cap = cv2.VideoCapture(0) 

    if not cap.isOpened():
        print("❌ Tidak bisa membuka webcam. Cek apakah kamera dipakai aplikasi lain.")
        return

    print("📷 Kamera aktif. Arahkan QR tiket ke kamera. Tekan 'q' untuk keluar.\n")

    last_scanned = None 

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1) 
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            ticket_code = obj.data.decode("utf-8")
            points = obj.polygon

            # Gambar kotak hijau di sekeliling QR yang terdeteksi
            if len(points) == 4:
                pts = [(p.x, p.y) for p in points]
                for i in range(4):
                    cv2.line(frame, pts[i], pts[(i + 1) % 4], (0, 255, 0), 3)

            cv2.putText(
                frame, ticket_code, (obj.rect.left, obj.rect.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )

            if ticket_code != last_scanned:
                last_scanned = ticket_code
                print(f"🔍 Terdeteksi: {ticket_code}")

                status_code, data = validate_ticket(ticket_code)

                if status_code == 200:
                    print(f"✅ SUKSES: {data.get('message')}\n")
                elif status_code == 400:
                    print(f"❌ DITOLAK ({data.get('status')}): {data.get('message')}\n")
                elif status_code == 404:
                    print(f"⚠️  TIDAK DITEMUKAN: {data.get('message')}\n")
                elif status_code == 403:
                    print(f"⚠️  AKSES DITOLAK: {data.get('message')}\n")
                else:
                    print(f"⚠️  ERROR: {data}\n")

        cv2.imshow("Ticket Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if TOKEN_PETUGAS == "PASTE_TOKEN_PETUGAS_DI_SINI":
        print("⚠️  Isi dulu TOKEN_PETUGAS di bagian atas script sebelum menjalankan.")
    else:
        main()