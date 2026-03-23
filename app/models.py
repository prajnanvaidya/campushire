from app import db
from datetime import datetime

#Admin
class Admin(db.Model):
    __tablename__="admin"
    id=db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(200), unique=True, nullable=False)
    password_hash=db.Column(db.String(200), nullable=False)

#company
class Company(db.Model):
    __tablename__="companies"
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(200), nullable=False)
    email=db.Column(db.String(250), unique=True, nullable=False)
    password_hash=db.Column(db.String(200), nullable=False)

    hr_contact=db.Column(db.String(20))
    website=db.Column(db.String(200))
    description=db.Column(db.Text)  
    
    approval_status=db.Column(db.Enum("Pending", "Approved", "Rejected"), default="Pending", nullable=False)
    is_blacklisted=db.Column(db.Boolean, default=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

    drives=db.relationship("PlacementDrive", backref="company", lazy=True)

#student
class Student(db.Model):
    __tablename__="students"
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(150), nullable=False)
    email=db.Column(db.String(200), unique=True, nullable=False)
    usn=db.Column(db.String(20), nullable=False, unique=True)
    password_hash=db.Column(db.String(200), nullable=False)

    phone=db.Column(db.String(20))
    branch=db.Column(db.String(50))
    cgpa=db.Column(db.Float)
    graduation_year=db.Column(db.Integer)
    resume=db.Column(db.String(200))

    is_blacklisted=db.Column(db.Boolean, default=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

    applications=db.relationship("Application", backref="student", lazy=True)

#Drives
class PlacementDrive(db.Model):
    __tablename__="placement_drives"
    id=db.Column(db.Integer, primary_key=True)
    company_id=db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    job_title=db.Column(db.String(200), nullable=False)

    job_description=db.Column(db.Text)
    eligibility_criteria=db.Column(db.String(200))
    min_cgpa = db.Column(db.Float, nullable=True)       
    eligible_branches = db.Column(db.String(200), nullable=True)
    eligible_batches = db.Column(db.String(100), nullable=True) 
    salary_package = db.Column(db.String(50))
    application_deadline = db.Column(db.Date, nullable=False)
    drive_date=db.Column(db.Date, nullable=False)

    approval_status=db.Column(db.Enum("Pending","Approved", "Rejected", "Closed"), default="Pending", nullable=False)
    date_rejected=db.Column(db.Boolean, default=False)
    date_rejection_note=db.Column(db.String(300), nullable=True )  
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    
    applications=db.relationship("Application", backref="drive", lazy=True)

#Application
class Application(db.Model):
    __tablename__="applications"
    id=db.Column(db.Integer, primary_key=True)
    student_id=db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    drive_id=db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)

    status=db.Column(db.Enum("Applied", "Cancelled", "Selected", "Rejected"), default="Applied", nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__=(db.UniqueConstraint("student_id", "drive_id", name="unique_student_application"), )

#Placement Stats(Additional table)
class PlacementStat(db.Model):  
    __tablename__="placement_stats"
    id=db.Column(db.Integer, primary_key=True)
    student_id=db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    company_id=db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    drive_id=db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)

    package=db.Column(db.String(70))
    recruited_date=db.Column(db.DateTime, default=datetime.utcnow)
