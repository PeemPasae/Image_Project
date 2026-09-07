from flask import Flask
from flask_cors import CORS
from config import Config
from app.utils.errors import register_error_handlers


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    register_error_handlers(app)

    CORS(
        app,
        resources={r"/api/v1/*": {"origins": config_class.CORS_ORIGINS}},
        supports_credentials=True,
    )

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/v1")

    return app
