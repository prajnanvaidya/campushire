from app import db
from app.models import PlacementDrive, Application
from datetime import datetime

def close_expired_drives():
    today = datetime.utcnow().date()
    
    expired = PlacementDrive.query.filter(
        PlacementDrive.approval_status == 'Approved',
        PlacementDrive.drive_date < today
    ).all()
    
    for drive in expired:
        drive.approval_status = 'Closed'
        for app in drive.applications:
            if app.status == 'Applied':
                app.status = 'Rejected'
    
    if expired:
        db.session.commit()


def student_eligible(student, drive):
    if drive.min_cgpa:
        if not student.cgpa or student.cgpa < drive.min_cgpa:
            return False, f"Minimum CGPA required is {drive.min_cgpa}. Your CGPA is {student.cgpa}."

    if drive.eligible_branches:
        allowed = [b.strip().upper() for b in drive.eligible_branches.split(',')]
        if not student.branch or student.branch.strip().upper() not in allowed:
            return False, f"This drive is open to {drive.eligible_branches} only."

    if drive.eligible_batches:
        try:
            allowed = [int(b.strip()) for b in drive.eligible_batches.split(',')]
        except ValueError:
            allowed = []
        if not student.graduation_year or student.graduation_year not in allowed:
            return False, f"This drive is open to batch {drive.eligible_batches} only."

    return True, None