from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

def create_app():
    app=Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///site.db"
    app.config['SECRET_KEY']="mad1_secret_key"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

    db.init_app(app)

    #Routes will be included in future

    return app