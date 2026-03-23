from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect 

from flask_migrate import Migrate

from dotenv import load_dotenv
import os

load_dotenv()

mail = Mail()

db=SQLAlchemy()

csrf  = CSRFProtect()   

def create_app():
    app=Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI']=os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    app.config['SECRET_KEY']=os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

    migrate=Migrate(app, db)

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    mail.init_app(app)

    db.init_app(app)
    csrf.init_app(app)

    from .routes.home import home_bp
    app.register_blueprint(home_bp)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from .routes.company import company_bp
    app.register_blueprint(company_bp)

    from .routes.student import student_bp
    app.register_blueprint(student_bp)

    return app