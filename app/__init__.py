from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.subjects import subjects_bp
    from app.routes.quiz import quiz_bp
    from app.routes.analytics import analytics_bp
    from app.routes.planner import planner_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(subjects_bp, url_prefix='/api/subjects')
    app.register_blueprint(quiz_bp, url_prefix='/api/quiz')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(planner_bp, url_prefix='/api/planner')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(main_bp)

    return app
