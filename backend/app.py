from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from models import db
from constants import SQLALCHEMY_DATABASE_URI, SECRET_KEY, JWT_SECRET_KEY, UPLOAD_FOLDER
from blacklist import blacklist
import nltk
import os

# Initialize the punkt tokenizer data
nltk.download('punkt')

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # or any other value you prefer
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 30 * 24 * 3600  # 30 days
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True if using HTTPS
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    app.config['JWT_COOKIE_SAMESITE'] = 'Strict'

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.before_request
    def enforce_foreign_keys():
        if db.engine.dialect.name == "sqlite":
            db.session.execute(text("PRAGMA foreign_keys=ON"))

    return app

app = create_app()
jwt = JWTManager(app)

# Register Blueprints
from auth import auth_bp
from feed import feed_bp
from comment import comment_bp
from todo import todo_bp
from scraper import scraper_bp
from weather import weather_bp
from calculator import calculator_bp
from group import group_bp

app.register_blueprint(auth_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(todo_bp)
app.register_blueprint(scraper_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(calculator_bp)
app.register_blueprint(group_bp)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in blacklist

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return (
        jsonify({"description": "The token has been revoked.", "error": "token_revoked"}),
        401,
    )

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return (
        jsonify({"message": "The token has expired.", "error": "token_expired"}),
        401,
    )

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return (
        jsonify({"message": "Signature verification failed.", "error": "invalid_token"}),
        401,
    )

@jwt.unauthorized_loader
def missing_token_callback(error):
    return (
        jsonify({
            "description": "Request does not contain an access token.",
            "error": "authorization_required",
        }),
        401,
    )

if __name__ == '__main__':
    app.run(debug=True)
