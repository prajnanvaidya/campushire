from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from functools import wraps
from datetime import datetime, timedelta
from app.models import Student, PlacementDrive, Application
from app.utils import close_expired_drives
from app import db

student_bp = Blueprint("student", __name__, url_prefix="/student")

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != "student":
            flash("Please login first", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route("/dashboard")
@student_required
def dashboard():
    close_expired_drives()
    studId  = session.get('user_id')
    student = Student.query.get(studId)
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('auth.login'))

    today = datetime.utcnow()

    # Stat counts
    applied_app_count = Application.query.filter_by(
        student_id=studId, status='Applied'
    ).count()

    approved_drives_count = PlacementDrive.query.filter_by(
        approval_status='Approved'
    ).count()

    week_end = today + timedelta(days=7)
    closing_week_drives_count = PlacementDrive.query.filter(
        PlacementDrive.approval_status == 'Approved',
        PlacementDrive.application_deadline >= today,
        PlacementDrive.application_deadline <= week_end
    ).count()

    # Placement status
    selected_app = Application.query.filter_by(
        student_id=studId, status='Selected'
    ).first()
    placed        = selected_app is not None
    company_name  = selected_app.drive.company.name if placed else None
    company_role  = selected_app.drive.job_title if placed else None
    salary        = selected_app.drive.salary_package if placed else None
    offer_date    = selected_app.created_at.strftime('%d %b %Y') if placed else None

    # Recent applications — limit 5
    recent_applications = Application.query.filter_by(
        student_id=studId
    ).order_by(Application.created_at.desc()).limit(5).all()

    # Drives closing this week — student has not applied to
    applied_drive_ids = [
        app.drive_id for app in Application.query.filter_by(student_id=studId).all()
    ]
    closing_drives = PlacementDrive.query.filter(
        PlacementDrive.approval_status == 'Approved',
        PlacementDrive.application_deadline >= today,
        PlacementDrive.application_deadline <= week_end,
        ~PlacementDrive.id.in_(applied_drive_ids) if applied_drive_ids else True
    ).all()

    # Offers count
    offers_count = Application.query.filter_by(
        student_id=studId, status='Selected'
    ).count()

    return render_template('student/student.html',
    student                   = student,
    stud_name                 = student.name,
    stud_branch               = student.branch,
    stud_grad_year            = student.graduation_year,
    stud_cgpa                 = student.cgpa,

    applied_app_count         = applied_app_count,
    approved_drives_count     = approved_drives_count,
    closing_week_drives_count = closing_week_drives_count,

    placed                    = placed,
    company_name              = company_name,
    company_role              = company_role,
    salary                    = salary,
    offer_date                = offer_date,

    recent_applications       = recent_applications,
    closing_drives            = closing_drives,
    applied_drive_ids         = applied_drive_ids,   # ← add this
    offers_count              = offers_count,
    now                       = today,

    role  = 'student',
    page  = 'dashboard',

    stud_applied_count        = applied_app_count,
    stud_approved_drives      = approved_drives_count,
)


@student_bp.route('/apply/<int:driveId>', methods=['POST'])
@student_required
def apply(driveId):
    from app.utils import student_eligible
    studId  = session.get('user_id')
    student = Student.query.get(studId)
    drive   = PlacementDrive.query.get(driveId)

    next_page = request.form.get('next', 'dashboard')
    redirect_to = url_for('student.drives') if next_page == 'drives' else url_for('student.dashboard')

    if not drive:
        flash('Drive not found.', 'danger')
        return redirect(redirect_to)

    if drive.approval_status != 'Approved':
        flash('This drive is not open for applications.', 'danger')
        return redirect(redirect_to)

    eligible, reason = student_eligible(student, drive)
    if not eligible:
        flash(f'You are not eligible for this drive. {reason}', 'danger')
        return redirect(redirect_to)

    existing = Application.query.filter_by(
        student_id=studId, drive_id=driveId
    ).first()
    if existing:
        flash('You have already applied to this drive.', 'warning')
        return redirect(redirect_to)

    try:
        new_app = Application(student_id=studId, drive_id=driveId)
        db.session.add(new_app)
        db.session.commit()
        flash(f'Successfully applied to {drive.job_title} at {drive.company.name}!', 'success')
    except Exception:
        db.session.rollback()
        flash('Something went wrong. Please try again.', 'danger')

    return redirect(redirect_to)


@student_bp.route("/companies")
@student_required
def companies():
    studId  = session.get('user_id')
    student = Student.query.get(studId)
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('auth.login'))

    filt = request.args.get('filter', 'all')
    pg   = request.args.get('page', 1, type=int)
    today = datetime.utcnow()

    # Active drives per company for badge
    from app.models import Company
    active_drive_obj = PlacementDrive.query.filter(
        PlacementDrive.approval_status == 'Approved',
        PlacementDrive.application_deadline >= today
    ).all()
    active_drives = {}
    for drive in active_drive_obj:
        active_drives[drive.company_id] = active_drives.get(drive.company_id, 0) + 1

    # Already applied company ids
    applied_company_ids = [
        app.drive.company_id
        for app in Application.query.filter_by(student_id=studId).all()
        if app.drive
    ]

    if filt == 'hiring':
        # Companies with at least one active approved drive
        hiring_ids = list(active_drives.keys())
        companies = Company.query.filter(
            Company.approval_status == 'Approved',
            Company.is_blacklisted == False,
            Company.id.in_(hiring_ids)
        ).paginate(page=pg, per_page=12, error_out=False)
        active_filter = 'hiring'
    elif filt == 'applied':
        companies = Company.query.filter(
            Company.id.in_(applied_company_ids)
        ).paginate(page=pg, per_page=12, error_out=False)
        active_filter = 'applied'
    else:
        companies = Company.query.filter_by(
            approval_status='Approved', is_blacklisted=False
        ).paginate(page=pg, per_page=12, error_out=False)
        active_filter = 'all'

    return render_template('student/companyList.html',
        student         = student,
        companies       = companies,
        active_filter   = active_filter,
        active_drives   = active_drives,
        applied_company_ids = applied_company_ids,

        total_count     = Company.query.filter_by(approval_status='Approved', is_blacklisted=False).count(),
        hiring_count    = len(active_drives),

        role  = 'student',
        page  = 'companies',

        stud_applied_count   = Application.query.filter_by(student_id=studId, status='Applied').count(),
        stud_approved_drives = PlacementDrive.query.filter_by(approval_status='Approved').count(),
        now = today,
    )




@student_bp.route("/drives")
@student_required
def drives():
    studId  = session.get('user_id')
    student = Student.query.get(studId)
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('auth.login'))

    filt    = request.args.get('filter', 'all')
    pg      = request.args.get('page', 1, type=int)
    company_filter = request.args.get('company', None)  # from companyList View Drives
    today   = datetime.utcnow()

    # Applied drive ids for this student
    applied_drive_ids = [
        app.drive_id for app in Application.query.filter_by(student_id=studId).all()
    ]

    base_query = PlacementDrive.query.filter_by(approval_status='Approved')

    # If came from company list — filter by company
    if company_filter:
        base_query = base_query.filter_by(company_id=company_filter)

    if filt == 'eligible':
        # All approved drives — eligibility checked in template
        drives = base_query.paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'eligible'
    elif filt == 'applied':
        drives = base_query.filter(
            PlacementDrive.id.in_(applied_drive_ids)
        ).paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'applied'
    elif filt == 'closing':
        week_end = today + timedelta(days=7)
        drives = base_query.filter(
            PlacementDrive.application_deadline >= today,
            PlacementDrive.application_deadline <= week_end
        ).paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'closing'
    else:
        drives = base_query.paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'all'

    return render_template('student/driveList.html',
        student           = student,
        drives            = drives,
        active_filter     = active_filter,
        applied_drive_ids = applied_drive_ids,
        company_filter    = company_filter,
        now               = today,

        total_count       = PlacementDrive.query.filter_by(approval_status='Approved').count(),
        applied_count     = len(applied_drive_ids),

        role  = 'student',
        page  = 'drives',

        stud_applied_count   = len(applied_drive_ids),
        stud_approved_drives = PlacementDrive.query.filter_by(approval_status='Approved').count(),
    )

@student_bp.route("/applications")
@student_required
def applications():
    studId  = session.get('user_id')
    student = Student.query.get(studId)
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('auth.login'))

    filt = request.args.get('filter', 'all')
    pg   = request.args.get('page', 1, type=int)
    today = datetime.utcnow()

    base_query = Application.query.filter_by(student_id=studId)

    if filt == 'applied':
        apps = base_query.filter_by(status='Applied').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'applied'
    elif filt == 'selected':
        apps = base_query.filter_by(status='Selected').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'selected'
    elif filt == 'rejected':
        apps = base_query.filter_by(status='Rejected').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'rejected'
    elif filt == 'cancelled':
        apps = base_query.filter_by(status='Cancelled').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'cancelled'
    else:
        apps = base_query.order_by(Application.created_at.desc()).paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'all'

    return render_template('student/applicationList.html',
        student        = student,
        apps           = apps,
        active_filter  = active_filter,
        now            = today,

        total_count    = base_query.count(),
        applied_count  = base_query.filter_by(status='Applied').count(),
        selected_count = base_query.filter_by(status='Selected').count(),
        rejected_count = base_query.filter_by(status='Rejected').count(),
        cancelled_count= base_query.filter_by(status='Cancelled').count(),

        role  = 'student',
        page  = 'applications',

        stud_applied_count   = base_query.filter_by(status='Applied').count(),
        stud_approved_drives = PlacementDrive.query.filter_by(approval_status='Approved').count(),
    )

@student_bp.route('/editProfile', methods=['GET', 'POST'])
@student_required
def editProfile():
    studId  = session.get('user_id')
    student = Student.query.get(studId)
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        phone           = request.form.get('phone', '').strip()
        resume          = request.form.get('resume', '').strip()
        cgpa_str        = request.form.get('cgpa', '').strip()

        # Validate resume
        if resume and not resume.startswith(('http://', 'https://')):
            flash('Resume link must start with http:// or https://', 'danger')
            return redirect(url_for('student.editProfile'))

        # Validate CGPA
        cgpa = None
        if cgpa_str:
            try:
                cgpa = float(cgpa_str)
                if cgpa < 0 or cgpa > 10:
                    flash('CGPA must be between 0 and 10', 'danger')
                    return redirect(url_for('student.editProfile'))
            except ValueError:
                flash('CGPA must be a valid number', 'danger')
                return redirect(url_for('student.editProfile'))

        try:
            if phone:   student.phone  = phone
            if resume:  student.resume = resume
            if cgpa is not None: student.cgpa = cgpa
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('student.editProfile'))
        except Exception:
            db.session.rollback()
            flash('Something went wrong', 'danger')
            return redirect(url_for('student.editProfile'))   

    return render_template('student/editProfile.html',
        student              = student,
        role                 = 'student',
        page                 = 'profile',
        stud_applied_count   = Application.query.filter_by(student_id=studId, status='Applied').count(),
        stud_approved_drives = PlacementDrive.query.filter_by(approval_status='Approved').count(),
    )