from flask import Blueprint, render_template, url_for, flash, redirect, session, request

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError, InputRequired

from werkzeug.security import generate_password_hash, check_password_hash

from app.models import Admin, Company, Student
from app import db

class LoginForm(FlaskForm):
    role=RadioField("Login As", choices=[('student', 'Student'), ('company', 'Company'), ('admin', 'Admin')], validators=[DataRequired(message="Confirm role!")])

    email=StringField("Email: ", validators=[DataRequired(message="Enter Email!"), Email(message="Email format is invalid!")])

    password=PasswordField("Password: ", validators=[DataRequired(message="Enter password!!")])
    
    submit=SubmitField("submit")

    

class StudentRegister(FlaskForm):
    name=StringField("Name: ", validators=[DataRequired(message="Enter Name!")])
    email=StringField("Email: ", validators=[DataRequired(message="Enter Email!"), Email(message="Email format is invalid!")])
    usn=StringField("USN: ", validators=[DataRequired(message="Enter USN"), Length(max=15)])
    password=PasswordField("Password: ", validators=[DataRequired(message="Enter password!!"), Length(min=6, max=15, message="Password should be between 6 and 15char length!")])
    confirm_password=PasswordField("Confirm Password: ", validators=[DataRequired(), EqualTo('password', message="Password must match")])

    phone=StringField("Contact No.: ", validators=[Length(min=10, max=10, message="Phone number must be exactly 10 digits"), Regexp(r'^\d{10}$', message="Phone number must contain only digits")])
    branch=StringField("Branch: ", validators=[DataRequired(message="Enter btranch!")])
    cgpa=FloatField("CGPA: ", validators=[DataRequired(message="Enter CGPA!")])
    graduation_year=IntegerField("Graduating Year: ", validators=[InputRequired(message="Enter passing year")])
    resume=StringField("Resume Link: ", validators=[DataRequired(message="Provide resume link!")])

    submit = SubmitField("Create Student Account", name="student_submit")

    def validate_resume(self, field):
        if(field.data):
            if( not field.data.startswith(('http://','https://'))):
                raise ValidationError("Please provide a valid url starting with http:// or https://")
            
    def validate_cgpa(self, field):
        if(field.data):
            if field.data is not None:
                if field.data<0 or field.data>10:
                    raise ValidationError("CGPA must be between 0 and 10")
        
    def validate_graduation_year(self, field):
        if(field.data):
            from datetime import datetime
            current_year=datetime.utcnow().year
            if(field.data<current_year or field.data>current_year+6):
                raise ValidationError(f"graduation year must be between {current_year} and {current_year + 6}")

class CompanyRegister(FlaskForm):
    name=StringField("Name: ", validators=[DataRequired(message="Enter Name!")])
    email=StringField("Email: ", validators=[DataRequired(message="Enter Email!"), Email(message="Email format is invalid!")])
    password=PasswordField("Password: ", validators=[DataRequired(message="Enter password!!"), Length(min=6, max=15, message="Password should be between 6 and 15char length!")])
    confirm_password=PasswordField("Confirm Password: ", validators=[DataRequired(), EqualTo('password', message="Password must match")])

    hr_contact=StringField("HR Contact: ", validators=[Length(min=10, max=10, message="Phone number must be exactly 10 digits"), Regexp(r'^\d{10}$', message="Phone number must contain only digits")])
    website=StringField("Website Link: ")
    description=StringField("Describe: ", validators=[DataRequired(message="Describe your company")])

    submit = SubmitField("Create Company Account", name="company_submit")

    def validate_website(self, field):
        if(field.data):
            if not field.data.startswith(('http://', 'https://')):
                raise ValidationError("Website link should start with http or https")


auth_bp=Blueprint("auth", __name__)

@auth_bp.route("/login", methods=['POST', 'GET'])
def login():
    form=LoginForm()
    if(form.validate_on_submit()):
        role=form.role.data
        useremail=form.email.data
        userpass=form.password.data
        if(role=="admin"):
            malik=Admin.query.filter_by(email=useremail).first()
            if(malik):
                if(check_password_hash(malik.password_hash, userpass)):
                    session['role']="admin"
                    session['user_id']=malik.id
                    flash("Login successful as Admin", "success")
                    return redirect(url_for('admin.dashboard'))
                else:
                    flash("Wrong Password!", "danger")
                    return redirect(url_for('auth.login'))
            else:
                flash("Email doesnt exist! Wrong Admin", "danger")
                return redirect(url_for('auth.login'))
        elif(role=="student"):
            stud=Student.query.filter_by(email=useremail).first()
            if(stud):
                if(check_password_hash(stud.password_hash, userpass)):
                    session['role']="student"
                    session['user_id']=stud.id
                    flash("Login Successful as student!", "success")
                    return redirect(url_for('student.dashboard'))
                else:
                    flash("Wrong password","danger")
                    return redirect(url_for('auth.login'))
            else:
                flash("Student doesnt exist with this Email-Id!", "danger")
                return redirect(url_for('auth.register'))
        else:
            comp=Company.query.filter_by(email=useremail).first()
            if(comp):
                if check_password_hash(comp.password_hash, userpass):
                    session['role']='company'
                    session['user_id']=comp.id
                    flash("Login Successful as company!", "success")
                    return redirect(url_for('company.dashboard'))
                else:
                    flash("Wrong password", "danger")
                    return redirect(url_for('auth.login'))
            else:
                flash("Company doesnt exist with this Email-Id!", "danger")
                return redirect(url_for('auth.register'))
    return render_template("auth/login.html", form=form, role="guest")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout successful!", "success")
    return redirect(url_for('home.house'))

@auth_bp.route("/register", methods=['POST', 'GET'])
def register():
    Studentform=StudentRegister()
    Companyform=CompanyRegister()

    if('student_submit' in request.form and Studentform.validate_on_submit()):
        uname=Studentform.name.data
        uemail=Studentform.email.data
        uusn=Studentform.usn.data
        upass=generate_password_hash(Studentform.password.data)
        uphone=Studentform.phone.data
        ubranch=Studentform.branch.data.strip().upper()
        grad_year=Studentform.graduation_year.data
        ucgpa=Studentform.cgpa.data
        uresume=Studentform.resume.data
        stud_email=Student.query.filter_by(email=uemail).first()
        stud_usn   = Student.query.filter_by(usn=uusn).first()
        if(stud_email):
            flash("The Email is already registered!", "danger")
            return redirect(url_for('auth.register'))
        if stud_usn:
            flash("This USN is already registered!", "danger")
            return redirect(url_for('auth.register'))
        
        try:
            new_stud=Student(name=uname, email=uemail, password_hash=upass, phone=uphone, graduation_year=grad_year, usn=uusn, branch=ubranch,cgpa=ucgpa, resume=uresume)
            db.session.add(new_stud)
            db.session.commit()
            session['role']="student"
            session['user_id']=new_stud.id
            flash("Registration successful", "success")
            return redirect(url_for('student.dashboard'))
        except Exception:
            db.session.rollback()
            flash("Error registering student", "danger")
            return redirect(url_for('auth.register'))
        

    elif('company_submit' in request.form and Companyform.validate_on_submit()):
        cname=Companyform.name.data
        cemail=Companyform.email.data
        cpass=generate_password_hash(Companyform.password.data)
        chr_contact=Companyform.hr_contact.data
        cweb=Companyform.website.data
        cdes=Companyform.description.data
        comp_exist=Company.query.filter_by(email=cemail).first()
        if(comp_exist):
            flash("Already registered by this email!", "danger")
            return redirect(url_for('auth.register'))
        
        try:
            new_comp=Company(name=cname, email=cemail, password_hash=cpass, hr_contact=chr_contact, website=cweb, description=cdes)
            db.session.add(new_comp)
            db.session.commit()
            session['role']="company"
            session['user_id']=new_comp.id
            flash("Registration successful", "success")
            return redirect(url_for('company.dashboard'))    
        except Exception:
            db.session.rollback()
            flash("Error registering company", "danger")
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html', Studform=Studentform, Compform=Companyform, role="guest")
