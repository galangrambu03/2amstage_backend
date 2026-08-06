import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Masa berlaku access token JWT, dalam menit. Default 15 menit dari
    # Flask-JWT-Extended kerasa kependekan buat pemakaian sehari-hari
    # (admin/organizer suka ke-logout tiba-tiba), jadi diperpanjang ke 7 hari.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_EXPIRES_MINUTES", 60 * 24 * 7)))

    # --- Email (Brevo SMTP relay, gratis 300 email/hari, tanpa kartu kredit) ---
    # 1. Daftar gratis di https://www.brevo.com
    # 2. Menu "SMTP & API" -> tab SMTP -> catat Login, lalu "Generate a new SMTP key"
    # 3. Menu "Senders, Domains & Dedicated IPs" -> verifikasi 1 email pengirim
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)