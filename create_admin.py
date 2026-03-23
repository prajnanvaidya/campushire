from app import db, create_app
from werkzeug.security import generate_password_hash
from app.models import Admin

import os
from dotenv import load_dotenv

load_dotenv()

app=create_app()

with app.app_context():
    email=os.environ.get('ADMIN_EMAIL')
    password=os.environ.get('ADMIN_PASSWORD')

    if not email or not password:
        print(f"Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env")
        exit(1)
    
    existing=Admin.query.filter_by(email=email).first()
    if existing:
        print(f"Admin {email} already exist")
        exit(0)
    else:
        try:
            admin=Admin(email=email, password_hash=generate_password_hash(password))
            db.session.add(admin)
            db.session.commit()
            print("Adminwith email {email} created Successfully!!")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to create admin: {e}")
            exit(1)