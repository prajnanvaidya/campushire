from flask import Blueprint, session, flash, redirect, url_for, render_template, request
from app.models import Company, PlacementDrive, Application
from functools import wraps
from datetime import datetime, date 
from app.utils import close_expired_drives

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired, ValidationError, Optional
from app import db

company_bp=Blueprint("company", __name__, url_prefix="/company")

def company_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if(session.get('role')!="company"):
            flash("Login First", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


class CreateDriveForm(FlaskForm):
    jobTitle=StringField("JOB TITLE *", validators=[DataRequired(message='Enter job title')], render_kw={"placeholder":"e.g. Software Engineer, Data Analyst"})

    salaryPackage=StringField('SALARY PACKAGE (optional)', render_kw={"placeholder":"e.g. 6 LPA or 50,000/month"})

    jobDescription=StringField('JOB DESCRIPTION (optional)', render_kw={"placeholder": "Describe the role, responsibilities and what the candidate will work on.."})

    eligibilityCriteria=StringField('ELIGIBILITY CRITERIA (optional)', render_kw={"placeholder": "e.g. CGPA>=7.5, CSE/ISE/ECE branches, Batch 2025-2026"})
    
    minCgpa=FloatField("MIN CGPA (optional)", validators=[Optional()], render_kw={"placeholder": "e.g. 7.5"})
    eligibleBranch=StringField("ELIGIBLE BRANCHES (optional)", render_kw={"placeholder": "e.g. CSE, ISE, AIML"})
    eligibleBatch=StringField("ELIGIBLE BATCH (optional)", render_kw={"placeholder": "e.g. 2027, 2028"})

    appDeadline=DateField('APPLICATION DEADLINE *', format='%Y-%m-%d', validators=[DataRequired(message='Give application deadline')], render_kw={"placeholder": "yyyy-mm-dd"})

    driveDate=DateField('DRIVE DATE *',format='%Y-%m-%d', validators=[DataRequired(message='Provide drive date')], render_kw={"placeholder": "yyyy-mm-dd"})

    submit=SubmitField("submit")

    def validate_appDeadline(self, field):
        if field.data<date.today():
            raise ValidationError("The date cannot be in the past!")
    def validate_driveDate(self, field):
        if field.data<date.today():
            raise ValidationError("The date cannot be in the past!")
        if self.appDeadline.data and field.data <= self.appDeadline.data:
            raise ValidationError("Drive date must be after the application deadline!")
        

class ProposeDateForm(FlaskForm):
    newDate=DateField("PROPOSE DRIVE DATE", format='%Y-%m-%d', validators=[DataRequired(message="Enter new date")])
    submit=SubmitField("submit")
    def validate_newDate(self, field):
        if field.data < date.today():
            raise ValidationError("Proposed date cannot be in the past!")


@company_bp.route("/dashboard")
@company_required
def dashboard():
    close_expired_drives()
    id=session.get('user_id')
    company=Company.query.get(id)
    if not company:
        flash('Company does not exist', 'danger')
        return redirect(url_for('auth.login'))
    
    drive_ids=[drive.id for drive in company.drives]

    total_drives_count=PlacementDrive.query.filter_by(company_id=id).count()

    active_drives_count=PlacementDrive.query.filter_by(company_id=id, approval_status='Approved').count()

    pending_drives_count=PlacementDrive.query.filter_by(company_id=id, approval_status='Pending').count()
    
    active_apps_count=Application.query.filter(Application.drive_id.in_(drive_ids), Application.status=='Applied').count() if drive_ids else 0

    selected_apps_count=Application.query.filter(Application.drive_id.in_(drive_ids), Application.status=='Selected').count() if drive_ids else 0

    closed_drives_count=PlacementDrive.query.filter_by(company_id=id, approval_status='Closed').count()

    recent_applications = Application.query.filter(
    Application.drive_id.in_(drive_ids)
).order_by(Application.created_at.desc()).limit(5).all() if drive_ids else []

    today=datetime.utcnow()
    upcoming_confirmed_drive_count=PlacementDrive.query.filter(PlacementDrive.company_id==id, PlacementDrive.drive_date>=today, PlacementDrive.approval_status=="Approved").count()

    upcoming_drives=PlacementDrive.query.filter(PlacementDrive.company_id==id, PlacementDrive.drive_date>=today, PlacementDrive.approval_status.in_(['Approved', 'Pending'])).all()

    drive_app_obj=Application.query.filter(Application.drive_id.in_(drive_ids), Application.status!='Cancelled').all()
    drive_app={}
    for app in drive_app_obj:
        drive_app[app.drive_id]=drive_app.get(app.drive_id, 0)+1

    return render_template('company/company.html',
                            company=company,
                            total_drives_count=total_drives_count,
                            active_drives_count=active_drives_count,
                            pending_drives_count=pending_drives_count,
                            active_apps_count=active_apps_count,
                            selected_apps_count=selected_apps_count,
                            closed_drives_count=closed_drives_count,

                            upcoming_confirmed_drive_count=upcoming_confirmed_drive_count,
                            upcoming_drives=upcoming_drives,
                            drive_app=drive_app,
                            now=today,

                            recent_applications=recent_applications,

                            role='company',
                            page='dashboard',
                            
                            #sidebar
                            side_drive_count=len(drive_ids),
                            side_application_count=Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0,
                            company_state=company.approval_status
                            )

@company_bp.route('/proposeDate/<int:driveId>', methods=['GET', 'POST'])
@company_required
def proposeDate(driveId):
    next=request.args.get('next', 'dashboard')
    if next=='driveList':
        redirect_to=url_for('company.drives')
        pg='drives'
    else:
        redirect_to=url_for('company.dashboard')
        pg='dashboard'

    compId=session.get('user_id')
    drive=PlacementDrive.query.get(driveId)
    if not drive:
        flash('Drive not exist', "danger")
        return redirect(redirect_to)
    
    company=Company.query.get(compId)
    if not company:
        flash('Company does not exist', 'danger')
        return redirect(url_for('auth.login'))
    
    form=ProposeDateForm()
    if form.validate_on_submit():
        newDate=form.newDate.data
        if newDate <= drive.application_deadline:
            flash("Drive date must be after the application deadline.", "danger")
            return redirect(url_for('company.proposeDate', driveId=drive.id))
        try:
            drive.drive_date=newDate
            drive.date_rejected=False
            drive.date_rejection_note=None
            drive.approval_status='Pending'
            db.session.commit()
            flash("Drive date updated", "success")
            return redirect(redirect_to)
        except Exception:
            db.session.rollback()
            flash("Something went wrong")
            return redirect(url_for('company.proposeDate', driveId=drive.id))

    drive_ids=[drive.id for drive in company.drives]
    return render_template('company/proposeDate.html',
                            company=company,
                            drive=drive,
                            form=form,
                            back=pg,
                            redirect_to=redirect_to,
                            
                            role='company',
                            page=pg,
                            
                            #sidebar
                            side_drive_count=len(drive_ids),
                            side_application_count=Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0,
                            company_state=company.approval_status
                            )



@company_bp.route('/driveProfile/<int:driveId>')
@company_required
def driveProfile(driveId):
    next=request.args.get('next', 'dashboard')
    if next=='driveList':
        redirect_to=url_for('company.drives')
        pg='drives'
    else:
        redirect_to=url_for('company.dashboard')
        pg='dashboard'

    compId=session.get('user_id')
    company=Company.query.get(compId)
    if not company:
        flash("Company not exist", "danger")
        return redirect(url_for('auth.login'))

    drive=PlacementDrive.query.get(driveId)
    if not drive:
        flash("Drive not exist", "danger")
        return redirect(url_for('company.dashboard'))
    
    drive_ids=[drive.id for drive in company.drives]
    return render_template('company/driveProfile.html', 
                            drive=drive,
                            now=datetime.utcnow(),
                            back=pg,
                            redirect_to=redirect_to,

                            role='company',
                            page=pg,
                            in_progress_count=Application.query.filter_by(drive_id=drive.id, status="Applied").count() ,
                            total_applications=Application.query.filter_by(drive_id=drive.id).count(),
                            selected_count=Application.query.filter_by(drive_id=drive.id,status='Selected').count(),
                            application_list=Application.query.filter_by(drive_id=drive.id).all(),
                            
                            #sidebar
                            side_drive_count=len(drive_ids),
                            side_application_count=Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0,
                            company_state=company.approval_status
                            )


@company_bp.route('/recruitedDetails/<int:driveId>')
@company_required
def recruitedDetails(driveId):
    next=request.args.get('next', 'dashboard')
    if next=='driveList':
        redirect_to=url_for('company.drives')
        pg='drives'
    else:
        redirect_to=url_for('company.dashboard')
        pg='dashboard'

    compId=session.get('user_id')
    company=Company.query.get(compId)
    if not company:
        flash('Company not exist')
        return redirect(url_for('auth.login'))
    
    drive=PlacementDrive.query.get(driveId)
    if not drive:
        flash('Drive not exist', "danger")
        return redirect(url_for('company.dashboard'))
    
    drive_ids=[drive.id for drive in company.drives]
    students=Application.query.filter_by(drive_id=drive.id, status='Selected').all()
    if not students:
        flash('Oops no student recruited')
        return redirect(url_for('company.dashboard'))

    return render_template('admin/SelectedStudDetails.html',
                            students=students,
                            company_name=company.name, 
                            role_name=drive.job_title, 
                            link=redirect_to,

                            role='company',
                            page=pg,
                            
                            #sidebar
                            side_drive_count=len(drive_ids),
                            side_application_count=Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0,
                            company_state=company.approval_status
                            )

@company_bp.route('/reviewApplication/<int:appId>', methods=['POST', 'GET'])
@company_required
def reviewApplication(appId):
    next=request.args.get('next', 'dashboard')
    if next=='applicationList':
        redirect_to=url_for('company.applications')
        pg='applications'
    else:
        redirect_to=url_for('company.dashboard')
        pg='dashboard'

    compId=session.get('user_id')
    company=Company.query.get(compId)
    if not company:
        flash("Company not exist", "danger")
        return redirect(url_for('auth.login'))
    
    drive_ids=[drive.id for drive in company.drives]
    application=Application.query.get(appId)
    if not application:
        flash("Application not found")
        return redirect(url_for('company.dashboard'))
    if(application.drive_id not in drive_ids):
        flash("Unauthorized access", "danger")
        return redirect(redirect_to)
    
    if request.method=='POST':
        action=request.form.get('decision', None)
        if application.status!='Applied':
            flash("This application cannot be reviewed", "danger")
            return redirect(redirect_to)
        elif action=='Select':
            try:
                application.status='Selected'
                db.session.commit()
                flash(f"Student {application.student.name} selected for drive {application.drive.job_title}", "success")
                return redirect(redirect_to)
            except Exception:
                db.session.rollback()
                flash("Something went wrong", "danger")
                return redirect(url_for('company.reviewApplication', appId=application.id))
        elif action=="Reject":
            try:
                application.status='Rejected'
                db.session.commit()
                flash(f"Student {application.student.name} rejected for drive {application.drive.job_title}", "success")
                return redirect(redirect_to)
            except Exception:
                db.session.rollback()
                flash("Something went wrong", "danger")
                return redirect(url_for('company.reviewApplication', appId=application.id))
        
    return render_template('company/applicationProfile.html',
                            app=application,
                            back=pg,
                            redirect_to=redirect_to,
                            role='company',
                            page=pg,
                            
                            #sidebar
                            side_drive_count=len(drive_ids),
                            side_application_count=Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0,
                            company_state=company.approval_status
                            )

@company_bp.route('/createDrive', methods=['GET', 'POST'])
@company_required
def createDrive():
    next=request.args.get('next', 'dashboard')
    if next=='driveList':
        redirect_to=url_for('company.drives')
        pg='drives'
    else:
        redirect_to=url_for('company.dashboard')
        pg='dashboard'

    compId=session.get('user_id')

    company=Company.query.get(compId)
    if not company:
        flash("Company not exist")
        return redirect(url_for('auth.login'))
    
    form=CreateDriveForm()

    if form.validate_on_submit():
        jobTitle=form.jobTitle.data
        jobDes=form.jobDescription.data
        salary=form.salaryPackage.data
        eligibility=form.eligibilityCriteria.data
        eliBranch=form.eligibleBranch.data
        eliBatch=form.eligibleBatch.data
        minCgpa=form.minCgpa.data
        appDead=form.appDeadline.data
        driveDate=form.driveDate.data
        new_drive=PlacementDrive(company_id=company.id, 
                            job_title=jobTitle,
                            job_description=jobDes if jobDes else "",
                            eligibility_criteria=eligibility if eligibility else "",
                            min_cgpa=minCgpa if minCgpa else None,
                            eligible_branches=eliBranch if eliBranch else None,
                            eligible_batches=eliBatch if eliBatch else None,
                            salary_package=salary if salary else "",
                            application_deadline=appDead,
                            drive_date=driveDate  )
        try:
            db.session.add(new_drive)
            db.session.commit()
            flash(f'Drive {jobTitle} created', "success")
            return redirect(redirect_to)
        except Exception:
            db.session.rollback()
            flash("Something went wrong", "danger")
            return redirect(url_for('company.createDrive'))

    drive_ids=[drive.id for drive in company.drives]
    return render_template('company/createDrive.html',
                            form=form,
                            company=company,
                            back=pg,
                            redirect_to=redirect_to,

                            role='company',
                            page=pg,


                            #sidebar
                            side_drive_count=len(drive_ids),
                            side_application_count=Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0,
                            company_state=company.approval_status
                           
                           )



@company_bp.route("/drives")
@company_required
def drives():
    compId = session.get('user_id')
    company = Company.query.get(compId)
    if not company:
        flash('Company does not exist', 'danger')
        return redirect(url_for('auth.login'))

    filt = request.args.get('filter', 'all')
    pg   = request.args.get('page', 1, type=int)

    base_query = PlacementDrive.query.filter_by(company_id=compId)

    if filt == 'live':
        drives = base_query.filter_by(approval_status='Approved').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'live'
    elif filt == 'pending':
        drives = base_query.filter_by(approval_status='Pending').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'pending'
    elif filt == 'ended':
        drives = base_query.filter_by(approval_status='Closed').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'ended'
    elif filt == 'cancelled':
        drives = base_query.filter_by(approval_status='Rejected').paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'cancelled'
    else:
        drives = base_query.paginate(page=pg, per_page=10, error_out=False)
        active_filter = 'all'

    # App counts per drive
    drive_ids = [d.id for d in company.drives]
    app_obj = Application.query.filter(
        Application.drive_id.in_(drive_ids),
        Application.status != 'Cancelled'
    ).all() if drive_ids else []
    drive_app = {}
    for app in app_obj:
        drive_app[app.drive_id] = drive_app.get(app.drive_id, 0) + 1

    # Date rejection banners — all drives with date_rejected=True
    rejected_date_drives = PlacementDrive.query.filter_by(
        company_id=compId, date_rejected=True
    ).all()

    today = datetime.utcnow()

    return render_template('company/driveList.html',
        company          = company,
        drives           = drives,
        active_filter    = active_filter,
        drive_app        = drive_app,
        rejected_date_drives = rejected_date_drives,
        now              = today,

        total_count      = base_query.count(),
        live_count       = base_query.filter_by(approval_status='Approved').count(),
        pending_count_d  = base_query.filter_by(approval_status='Pending').count(),
        ended_count      = base_query.filter_by(approval_status='Closed').count(),

        role             = 'company',
        page             = 'drives',

        side_drive_count        = len(drive_ids),
        side_application_count  = Application.query.filter(
            Application.drive_id.in_(drive_ids)
        ).count() if drive_ids else 0,
        company_state    = company.approval_status
    )




@company_bp.route("/applications")
@company_required   
def applications():
    compId = session.get('user_id')
    company = Company.query.get(compId)
    if not company:
        flash('Company does not exist', 'danger')
        return redirect(url_for('auth.login'))

    drive_ids = [drive.id for drive in company.drives]

    filt = request.args.get('filter', 'all')
    pg   = request.args.get('page', 1, type=int)

    base_query = Application.query.filter(
        Application.drive_id.in_(drive_ids)
    ) if drive_ids else Application.query.filter_by(id=None)

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

    today = datetime.utcnow()

    return render_template('company/applicationList.html',
        company        = company,
        apps           = apps,
        active_filter  = active_filter,
        now            = today,

        total_count     = base_query.count(),
        applied_count   = base_query.filter_by(status='Applied').count(),
        selected_count  = base_query.filter_by(status='Selected').count(),
        rejected_count  = base_query.filter_by(status='Rejected').count(),
        cancelled_count = base_query.filter_by(status='Cancelled').count(),

        role           = 'company',
        page           = 'applications',

        side_drive_count       = len(drive_ids),
        side_application_count = Application.query.filter(
            Application.drive_id.in_(drive_ids)
        ).count() if drive_ids else 0,
        company_state  = company.approval_status
    )


@company_bp.route('/editProfile', methods=['GET', 'POST'])
@company_required
def editProfile():
    compId  = session.get('user_id')
    company = Company.query.get(compId)
    if not company:
        flash('Company not found', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        hr_contact  = request.form.get('hr_contact', '').strip()
        website     = request.form.get('website', '').strip()
        description = request.form.get('description', '').strip()

        if website and not website.startswith(('http://', 'https://')):
            flash('Website must start with http:// or https://', 'danger')
            return redirect(url_for('company.editProfile'))

        try:
            company.hr_contact  = hr_contact  if hr_contact  else company.hr_contact
            company.website     = website     if website     else company.website
            company.description = description if description else company.description
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('company.editProfile'))
        except Exception:
            db.session.rollback()   
            flash('Something went wrong', 'danger')
            return redirect(url_for('company.editProfile'))

    drive_ids = [drive.id for drive in company.drives]
    return render_template('company/editProfile.html',
        company        = company,
        role           = 'company',
        page           = 'profile',
        side_drive_count       = len(drive_ids),
        side_application_count = Application.query.filter(
            Application.drive_id.in_(drive_ids)
        ).count() if drive_ids else 0,
        company_state  = company.approval_status
    )
