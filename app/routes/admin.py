from flask import Blueprint, render_template, flash, redirect, url_for, request,session
from functools import wraps
from datetime import datetime, timedelta
from app.models import Company, Student, PlacementDrive, Application
from app.utils import close_expired_drives
from app import db
 
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role')!="admin":
            flash("Please login first", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


admin_bp=Blueprint("admin", __name__, url_prefix='/admin')

@admin_bp.route("/search")
@admin_required
def search():
    q = request.args.get('q', '').strip()

    if not q:
        flash("Please enter a search term.", "warning")
        return redirect(url_for('admin.dashboard'))

    students = Student.query.filter(
        db.or_(
            Student.name.ilike(f'%{q}%'),
            Student.email.ilike(f'%{q}%'),
            Student.usn.ilike(f'%{q}%'),
            Student.branch.ilike(f'%{q}%')
        )
    ).all()

    companies = Company.query.filter(
        db.or_(
            Company.name.ilike(f'%{q}%'),
            Company.email.ilike(f'%{q}%'),
            Company.description.ilike(f'%{q}%')
        )
    ).all()

    return render_template('admin/search_results.html',
        students  = students,
        companies = companies,
        query     = q,
        total     = len(students) + len(companies),

        role      = 'admin',
        page      = 'search',

        # sidebar — these were missing
        company_count = Company.query.count(),
        student_count = Student.query.count(),
        drive_count   = PlacementDrive.query.count(),
        app_count     = Application.query.count(),
        pending_count = Company.query.filter_by(approval_status='Pending').count()
    )

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    close_expired_drives()
    today=datetime.utcnow()
    #For sidebar
    tot_comp=Company.query.count()
    tot_drives=PlacementDrive.query.count()
    tot_students=Student.query.count()
    tot_applications=Application.query.count()

    #For company
    app_comp=Company.query.filter_by(approval_status="Approved").count()
    pen_comp=Company.query.filter(Company.approval_status=="Pending").order_by(Company.created_at.desc()).all()
    pen_comp_count=Company.query.filter_by(approval_status="Pending").count()
    rem_comp=Company.query.filter_by(approval_status="Rejected").count()
    comp=Company.query.order_by(Company.created_at.desc()).limit(5).all()
    active_drive_object=PlacementDrive.query.join(Company).filter(PlacementDrive.approval_status=="Approved", Company.approval_status=="Approved", PlacementDrive.drive_date>=today).all()
    active_drives={}
    for drive in active_drive_object:
        active_drives[drive.company_id]=active_drives.get(drive.company_id,0)+1

    #For students
    stud=Student.query.order_by(Student.created_at.desc()).limit(5).all()
    start_of_week=today-timedelta(days=today.weekday())
    start_of_week=start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    new_student=Student.query.filter(Student.created_at>=start_of_week).count()
    rem_students=Student.query.filter_by(is_blacklisted=True).count()

    #for drives
    all_drives=PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).limit(5).all()
    if(today.month==12):
        end_of_month=today.replace(year=today.year+1, month=1, day=1)
    else:
        end_of_month=today.replace(month=today.month+1, day=1)
    yet_drive=PlacementDrive.query.filter_by(approval_status="Approved").count()
    closing_dr=PlacementDrive.query.filter(PlacementDrive.application_deadline>=today, PlacementDrive.drive_date<end_of_month).count()
    completed_dr=PlacementDrive.query.filter_by(approval_status="Closed").count()

    #for student_application
    all_applications=Application.query.order_by(Application.created_at.desc()).limit(5).all()
    stud_applications=Application.query.join(PlacementDrive).filter(PlacementDrive.approval_status=="Approved").count()
    stud_progress=Application.query.join(PlacementDrive).filter(PlacementDrive.approval_status=="Approved", Application.status=="Applied").count()
    selected_stud=Application.query.filter_by(status="Selected").count()

    return render_template("admin/admin.html", 
                           reg_company=app_comp,
                           company_pending=pen_comp,
                           pending_company_count=pen_comp_count,
                           rejected_companies=rem_comp, 
                           ac_drives=active_drives,

                           reg_stud=tot_students, 
                           new_stud=new_student, 
                           removed_stud=rem_students,

                           current_drives=yet_drive,
                           closing_drives=closing_dr, 
                           reg_students=stud_applications,
                           completed_drives=completed_dr,
                           
                           inprogress_students=stud_progress,
                           selected_students=selected_stud,
                           
                           companies=comp,
                           students=stud,
                           drives=all_drives,
                           applications=all_applications,
                           now=today,
                           role="admin",
                           approved_comp=(app_comp-pen_comp_count),
                           
                           company_count=tot_comp,
                           student_count=tot_students,
                           drive_count=tot_drives,
                           app_count=tot_applications,
                           pending_count=pen_comp_count)

@admin_bp.route("/companyblock/<int:id>")
@admin_required
def CompBlock(id):
    next_page=request.args.get('next', 'dashboard')
    if next_page == 'companies':
        redirect_to = url_for('admin.companies')
    elif next_page == 'compProfile':
        redirect_to = url_for('admin.companyProfile', id=id)
    else:
        redirect_to = url_for('admin.dashboard')
    try:
        company=Company.query.get(id)
        if(company):
            company.is_blacklisted=True
            for drive in company.drives:
                if drive.approval_status=='Pending' or drive.approval_status=='Approved':
                    drive.approval_status="Rejected"
                    drive.date_rejected=False
                    drive.date_rejection_note=None
                    for app in drive.applications:
                        if(app.status=='Applied'):
                            app.status="Cancelled"
            db.session.commit()
            flash(f"{company.name} got blocklisted")
            return redirect(redirect_to)
        else:
            flash(f"Company id {id} was not found!", "danger")
            return redirect(redirect_to)
    except Exception:
        db.session.rollback()
        flash("Error updating in database")
        return redirect(redirect_to)


@admin_bp.route("/studentblock/<int:id>")
@admin_required
def StudBlock(id):
    next_page=request.args.get('next', 'dashboard')
    redirect_to=url_for('admin.students') if next_page=="students" else url_for('admin.dashboard')
    try:
        student=Student.query.get(id)
        if(student):
            student.is_blacklisted=True
            for app in student.applications:
                if(app.status=="Applied"):
                    app.status="Cancelled"
            db.session.commit()
            flash(f"Student {student.name} with id {id} blocked")
            return redirect(redirect_to)
        else:
            flash(f"No student exist with that id {id}")
            return redirect(redirect_to)
    except Exception:
        db.session.rollback()
        flash("Error updating in database")
        return redirect(redirect_to)
    

@admin_bp.route("/companyAction/<action>/<int:id>")
@admin_required
def companyAction(action, id):
    next_page=request.args.get('next', 'dashboard')
    if(next_page=='companies'):
        redirect_to=url_for('admin.companies')
    elif(next_page=='compProfile'):
        redirect_to=url_for('admin.companyProfile', id=id)
    else:
        redirect_to=url_for('admin.dashboard')
    try:
        company=Company.query.get(id)
        if(company):
            if(action=="Approve"):
                company.approval_status="Approved"
                db.session.commit()
                flash(f"{company.name} approved")
                return redirect(redirect_to)
            elif(action=="Reject"):
                company.approval_status="Rejected"
                db.session.commit()
                flash(f"{company.name} rejected")
                return redirect(redirect_to)
        else:
            flash(f"Company with id {id} doesnt exist!!")
            return redirect(redirect_to)
    except Exception:
        db.session.rollback()
        flash("Database updation resulted in some problem")
        return redirect(redirect_to)
    


@admin_bp.route("/recruited/<int:id>")
@admin_required
def recruitedDetails(id):
    next_page=request.args.get('next', 'dashboard')
    if next_page=='driveList':
        redirect_to=url_for('admin.drives')
        pg='drives'
    elif next_page=='driveProfile':
        redirect_to=url_for('admin.driveProfile', id=id)
        pg='drives'
    else:
        redirect_to=url_for('admin.dashboard')
        pg='dashboard'
    
    drive=PlacementDrive.query.get(id)
    if not drive:
        flash(f"Drive with id {id} not found", "danger")
        return redirect(redirect_to)

    
    students=Application.query.filter_by(drive_id=drive.id, status="Selected").all()
    if not students:
        flash("Oops! No student selected by company!")
        return redirect(redirect_to)

    return render_template('admin/SelectedStudDetails.html', 
                                    students=students, 
                                    company_name=drive.company.name, 
                                    role_name=drive.job_title, 
                                    back=pg,
                                    link=redirect_to,

                                    role="admin",
                                    page=pg,
                                    
                                    company_count = Company.query.count(),
                                    student_count = Student.query.count(),
                                    drive_count   = PlacementDrive.query.count(),
                                    app_count     = Application.query.count(),
                                    pending_count = Company.query.filter_by(approval_status="Pending").count()
                                    )


#company_list.html
@admin_bp.route("/companies/")
@admin_required
def companies():
    today=datetime.utcnow()
    filt=request.args.get('filter', 'all')
    pg=request.args.get('page', 1, type=int)
    active_drive_object=PlacementDrive.query.join(Company).filter(PlacementDrive.approval_status=="Approved", Company.approval_status=="Approved", PlacementDrive.drive_date>=today).all()
    pen_comp_count=Company.query.filter_by(approval_status="Pending").count()
    active_drives={}
    for drive in active_drive_object:
        active_drives[drive.company_id]=active_drives.get(drive.company_id,0)+1
    
    if(filt=="all"):
        companies=Company.query.paginate(page=pg, per_page=10, error_out=False)
        act_filter="all"
    elif(filt=="approved"):
        companies=Company.query.filter_by(approval_status="Approved", is_blacklisted=False).paginate(page=pg, per_page=10, error_out=False)
        act_filter="approved"
    elif(filt=="pending"):
        companies=Company.query.filter_by(approval_status="Pending").paginate(page=pg, per_page=10, error_out=False)
        act_filter="pending"
    elif(filt=="rejected"):
        companies=Company.query.filter_by(approval_status="Rejected").paginate(page=pg, per_page=10, error_out=False)
        act_filter="rejected"
    else:
        companies=Company.query.filter_by(is_blacklisted=True).paginate(page=pg, per_page=10, error_out=False)
        act_filter='blacklisted'

    return render_template("admin/company_list.html", 
                            companies=companies, 
                            drives=active_drives, 
                            active_filter=act_filter,
                            total_companies=Company.query.count(),
                            approved_companies=Company.query.filter_by(approval_status="Approved", is_blacklisted=False).count(),
                            pending_companies=pen_comp_count,
                            blacklisted_companies=Company.query.filter_by(is_blacklisted=True).count(),

                            #role for nav and page for sidebar focus:active for buttons
                            role="admin",
                            page="companies",
                                
                            #for sidebar numbers
                            company_count         = Company.query.count(),
                            student_count         = Student.query.count(),
                            drive_count           = PlacementDrive.query.count(),
                            app_count             = Application.query.count(),
                            pending_count         = pen_comp_count
                            )

#Other routes for company-list
@admin_bp.route('/undoBlacklist/<role>/<int:id>')
@admin_required
def undoBlacklist(role, id):
    if role=="company":
        next_page=request.args.get('next', 'companies')
        redirect_to=url_for('admin.companyProfile', id=id) if next_page=='compProfile' else url_for('admin.companies')
        try:
            company=Company.query.get(id)
            if(company):
                if(company.is_blacklisted==True):
                    company.is_blacklisted=False
                    for drive in company.drives:
                        if drive.approval_status=='Rejected':
                            drive.approval_status='Pending'
                            for app in drive.applications:
                                if app.status=='Cancelled':
                                    app.status='Applied'
                    db.session.commit()
                    flash(f"{company.name} removed from blacklist", "success")
                    return redirect(redirect_to)
                else:
                    flash(f"{company.name} is not in blacklist", "danger")
                    return redirect(redirect_to)
            else:
                flash(f"No company with id {id} exist", "danger")
                return redirect(redirect_to)
        except Exception:
            db.session.rollback()
            flash("Database updation resulted in some problem")
            return redirect(redirect_to)
    elif role=="student":
        next_page=request.args.get('next', 'students')
        redirect_to=url_for('admin.studentProfile', id=id) if next_page=='studProfile' else url_for('admin.students')
        try:
            student=Student.query.get(id)
            if(student):
                if(student.is_blacklisted==True):
                    student.is_blacklisted=False
                    for app in student.applications:
                        if(app.status=='Cancelled'):
                            if(app.drive.approval_status=='Approved' or app.drive.approval_status=='Pending'):
                                app.status='Applied'
                            elif(app.drive.approval_status=='Closed'):
                                app.status='Rejected'
                    db.session.commit()
                    flash(f"{student.name} with id {id} is removed from blacklist", "success")
                    return redirect(redirect_to)
                else:
                    flash(f"Student with id {id} is not blacklisted", "danger")
                    return redirect(redirect_to)
            else:
                flash(f"No Student with id {id} exist", "danger")
                return redirect(redirect_to)
        except Exception:
            db.session.rollback()
            flash("Database updation resulted in some problem")
            return redirect(redirect_to)
        
@admin_bp.route('/reapprovecomp/<int:id>')
@admin_required
def ReapproveComp(id):
    next_page=request.args.get('next', 'companies')
    redirect_to=url_for('admin.companyProfile', id=id) if next_page=="compProfile" else url_for('admin.companies')
    try:
        company=Company.query.get(id)
        if(company):
            if(company.approval_status=="Rejected"):
                company.approval_status="Approved"
                db.session.commit()
                flash(f"{company.name} Approved", "success")
                return redirect(redirect_to)
            else:
                flash(f"Company with id {id} is not rejected", "danger")
                return redirect(redirect_to)
        else:
            flash(f"No company with id {id} exist", "danger")
            return redirect(redirect_to)
    except Exception:
        db.session.rollback()
        flash("Database updation resulted in some problem")
        return redirect(redirect_to)
    
@admin_bp.route('/companyProfile/<int:id>')
@admin_required
def companyProfile(id):
    company=Company.query.get(id)
    if(company):
        company_drive_count=len(company.drives)
        app_per_drive_obj=Application.query.filter(Application.status!='Cancelled').all()
        app_per_drive={}
        for app in app_per_drive_obj:
            app_per_drive[app.drive_id]=app_per_drive.get(app.drive_id, 0)+1

        
        return render_template('admin/companyProfile.html',
                                role='admin',
                                page='companies',
                               
                                company=company,
                                total_drives=company_drive_count,
                                application_per_drive=app_per_drive,

                                #for sidebar numbers
                                company_count         = Company.query.count(),
                                student_count         = Student.query.count(),
                                drive_count           = PlacementDrive.query.count(),
                                app_count             = Application.query.count(),
                                pending_count         = Company.query.filter_by(approval_status="Pending").count()
                               )
    else:
        flash(f"Company not found with id {id}", "danger")
        return redirect(url_for('admin.companies'))



#students_list.html
@admin_bp.route("/students")  
@admin_required
def students():
    filt=request.args.get('filter', 'all')
    pg=request.args.get('page', 1, type=int)
    all_apps = Application.query.filter(
    Application.status != "Cancelled"
    ).all()
    student_applications = {}
    for app in all_apps:
        student_applications[app.student_id] = student_applications.get(app.student_id, 0) + 1
    if(filt=="all"):
        students=Student.query.paginate(page=pg, per_page=10, error_out=False)
        active_filter='all'
    elif(filt=='active'):
        students=Student.query.filter_by(is_blacklisted=False).paginate(page=pg, per_page=10, error_out=False)
        active_filter="active"
    else:
        students=Student.query.filter_by(is_blacklisted=True).paginate(page=pg, per_page=10, error_out=False)
        active_filter="rejected"
    return render_template("admin/students_list.html", 
                            studs=students, 
                            act_filter=active_filter, 
                            stud_app=student_applications,

                            total_students      = Student.query.count(),
                            active_students     = Student.query.filter_by(is_blacklisted=False).count(),
                            blacklisted_students = Student.query.filter_by(is_blacklisted=True).count(),
                            applied_students    = db.session.query(Student.id).join(Application).distinct().count(),
                           
                            role='admin',
                            page='students',

                            company_count       = Company.query.count(),
                            student_count       = Student.query.count(),
                            drive_count         = PlacementDrive.query.count(),
                            app_count           = Application.query.count(),
                            pending_count       = Company.query.filter_by(approval_status="Pending").count()
                           )

@admin_bp.route('/studentProfile/<int:id>')
@admin_required
def studentProfile(id):
    student=Student.query.get(id)
    if(student):
        return render_template('admin/StudProfile.html', 
                                stud=student,
                                role='admin',
                                page='students',
                                #for sidebar
                                company_count = Company.query.count(),
                                student_count = Student.query.count(),
                                drive_count   = PlacementDrive.query.count(),
                                app_count     = Application.query.count(),
                                pending_count = Company.query.filter_by(approval_status="Pending").count())
    else:
        flash(f"Student not found with id {id}")
        return redirect(url_for('admin.students'))



#drives_list.html
@admin_bp.route("/drives")
@admin_required
def drives():
    today=datetime.utcnow()
    filt=request.args.get('filter', 'all')
    pg=request.args.get('page', 1, type=int)
    if filt=='all':
        drives=PlacementDrive.query.paginate(page=pg, per_page=10, error_out=False)
        act_filter='all'
    elif filt=='pending':
        drives=PlacementDrive.query.filter_by(approval_status='Pending').paginate(page=pg, per_page=10, error_out=False)
        act_filter='pending'
    elif filt=='closed':
        drives=PlacementDrive.query.filter_by(approval_status='Closed').paginate(page=pg, per_page=10, error_out=False)
        act_filter='closed'
    elif filt=='approved':
        drives=PlacementDrive.query.filter_by(approval_status='Approved').paginate(page=pg, per_page=10, error_out=False)
        act_filter='approved'
    else:
        drives=PlacementDrive.query.filter_by(approval_status='Rejected').paginate(page=pg, per_page=10, error_out=False)
        act_filter='rejected'

    total_drives=PlacementDrive.query.count()
    waiting_count=PlacementDrive.query.filter_by(approval_status='Pending').count()
    active_count=PlacementDrive.query.filter_by(approval_status='Approved').count()
    closed_count=PlacementDrive.query.filter_by(approval_status='Closed').count()
    Application_count={}
    Application_obj=Application.query.all()
    for app in Application_obj:
        Application_count[app.drive_id]=Application_count.get(app.drive_id,0)+1


    return render_template("admin/drives_list.html", 
                            drives=drives,
                            active_filter=act_filter,
                            total_drives=total_drives,
                            waiting_count=waiting_count,
                            active_count=active_count,
                            closed_count=closed_count,
                            Application_count=Application_count,
                            now=today,

                            role='admin',
                            page='drives',

                            #for sidebar
                            company_count = Company.query.count(),
                            student_count = Student.query.count(),
                            drive_count   = PlacementDrive.query.count(),
                            app_count     = Application.query.count(),
                            pending_count = Company.query.filter_by(approval_status="Pending").count()

                            )


@admin_bp.route('/driveApprove/<int:id>')
@admin_required
def driveApprove(id):
    next_page=request.args.get('next', 'drives')
    redirect_to=url_for('admin.driveProfile', id=id) if next_page=='driveProfile' else url_for('admin.drives')
    try:
        drive=PlacementDrive.query.get(id)
        if(drive):
            if(drive.approval_status=='Pending'):
                drive.approval_status='Approved'
                if(drive.date_rejected==True):
                    drive.date_rejected=False
                db.session.commit()
                flash(f"Drive with id {id} is approved")
                return redirect(redirect_to)
            else:
                flash(f'Drives status is not pending', "warning")
                return redirect(url_for('admin.drives'))
        else:
            flash(f'No drive exist with id {id}', "danger")
            return redirect(redirect_to)
    except Exception:
        db.session.rollback()
        flash('Something went wrong in updating database', "danger")
        return redirect(redirect_to)
    
@admin_bp.route('/rejectDrive/<int:id>', methods=['POST', 'GET'])
@admin_required
def rejectDrive(id):
    next_page=request.args.get('next', 'drives')
    redirect_to=url_for('admin.driveProfile', id=id) if next_page=='driveProfile' else url_for('admin.drives')
    drive=PlacementDrive.query.get(id)
    if not drive:
        flash(f"Drive with id {id} not exist", "danger")
        return redirect(redirect_to)
    
    if request.method=='POST':
        rejection_note=request.form.get('rejection_note', '').strip()
        if not rejection_note:
            flash(f'Please provide a reason for rejection', 'danger')
            return redirect(url_for('admin.rejectDrive', id=id))
        try:
            drive.date_rejected=True
            drive.date_rejection_note=rejection_note
            db.session.commit()
            flash(f'Drive date for {drive.job_title} rejected company notified', 'warning')
            return redirect(redirect_to)
        except Exception:
            db.session.rollback()
            flash('Something went wrong', 'danger')
            return redirect(url_for('admin.rejectDrive', id=id))
    return render_template('admin/rejectDrivePage.html',
                            drive=drive,
                            role='admin',
                            page='drives',

                            #for sidebar
                            company_count = Company.query.count(),
                            student_count = Student.query.count(),
                            drive_count   = PlacementDrive.query.count(),
                            app_count     = Application.query.count(),
                            pending_count = Company.query.filter_by(approval_status="Pending").count()
                           )

    
@admin_bp.route('/driveProfile/<int:id>')
@admin_required
def driveProfile(id):
    drive=PlacementDrive.query.get(id)
    if(drive):
        return render_template('admin/driveProfile.html', 
                                drive=drive,
                                role='admin',
                                page='drives',
                                total_applications=Application.query.filter_by(drive_id=drive.id).count(),
                                selected_count=Application.query.filter_by(drive_id=drive.id,status='Selected').count(),
                                application_list=Application.query.filter_by(drive_id=drive.id).all(),
                                now=datetime.utcnow(),

                                #for sidebar
                                company_count = Company.query.count(),
                                student_count = Student.query.count(),
                                drive_count   = PlacementDrive.query.count(),
                                app_count     = Application.query.count(),
                                pending_count = Company.query.filter_by(approval_status="Pending").count()
                                )
    else:
        flash(f"No drive with id {id} exist")
        return redirect(url_for('admin.drives'))


#application_list.html
@admin_bp.route("/applications")
@admin_required
def applications():
    pg=request.args.get('page', 1, type=int)
    filt=request.args.get('filter', 'all')
    if filt=='all':
        applications=Application.query.paginate(page=pg, per_page=10,error_out=False)
        active_filter='all'
    elif filt=='applied':
        applications=Application.query.filter_by(status='Applied').paginate(page=pg, per_page=10,error_out=False)
        active_filter='applied'
    elif filt=='selected':
        applications=Application.query.filter_by(status='Selected').paginate(page=pg, per_page=10,error_out=False)
        active_filter='selected'
    elif filt=='rejected':
        applications=Application.query.filter_by(status='Rejected').paginate(page=pg, per_page=10,error_out=False)
        active_filter='rejected'
    else:
        applications=Application.query.filter_by(status='Cancelled').paginate(page=pg, per_page=10,error_out=False)
        active_filter='cancelled'



    return render_template("admin/applications_list.html",          
                            apps=applications,
                            active_filter=active_filter,
                            total_count=Application.query.count(),
                            applied_count=Application.query.filter_by(status='Applied').count(),
                            selected_count=Application.query.filter_by(status='Selected').count(),
                            rejected_count=Application.query.filter_by(status='Rejected').count(),
                            cancelled_count=Application.query.filter_by(status='Cancelled').count(),

                            
                            role='admin',
                            page='applications',


                            #for sidebar
                            company_count = Company.query.count(),
                            student_count = Student.query.count(),
                            drive_count   = PlacementDrive.query.count(),
                            app_count     = Application.query.count(),
                            pending_count = Company.query.filter_by(approval_status="Pending").count()
                            )

