from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
import os

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        from app.models import user

        from app.routes.auth import auth_bp
        from app.routes.events import events_bp
        from app.routes.ticket_categories import tc_bp
        from app.routes.orders import orders_bp
        from app.routes.tickets import tickets_bp
        from app.routes.reports import reports_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(events_bp)
        app.register_blueprint(tc_bp)
        app.register_blueprint(orders_bp)
        app.register_blueprint(tickets_bp)
        app.register_blueprint(reports_bp)

    return app