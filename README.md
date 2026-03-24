# CampusHire — Campus Placement Management System

> A full-stack web application that simplifies and centralises the campus placement process for students, recruiting companies, and placement administrators.

**🔗 Live Demo:** [https://campushire-ay0t.onrender.com](https://campushire-ay0t.onrender.com)

> ⚠️ Hosted on Render's free tier — the server may take 30–60 seconds to wake up on first visit after a period of inactivity. This is normal behaviour for free tier deployments.

---

## Table of Contents

- [Overview](#overview)
- [Live Demo](#live-demo)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Creating the Admin Account](#creating-the-admin-account)
- [User Roles](#user-roles)
- [Workflow](#workflow)
- [Database Models](#database-models)
- [Author](#author)

---

## Overview

CampusHire is a campus placement portal that connects students with recruiting companies through a structured, admin-moderated workflow. Companies register and post placement drives, students apply based on eligibility criteria, and the placement admin oversees approvals, company verifications, and overall placement activity.

The platform handles the complete placement lifecycle — from company registration and drive creation to student applications, interview outcomes, and final placement records.

---

## Live Demo

🌐 **[https://campushire-ay0t.onrender.com](https://campushire-ay0t.onrender.com)**

### Test Credentials

You can explore the app using the following test accounts:

| Role | How to access |
|---|---|
| Admin | Contact via repo |
| Company | Register at `/register` → Company tab — requires admin approval |
| Student | Register at `/register` → Student tab — immediate access |

---

## Features

### Admin
- Approve or reject company registrations
- Approve or reject proposed placement drive dates
- Blacklist and un-blacklist companies and students
- View all companies, students, drives, and applications with filters and pagination
- Search across students and companies by name, email, USN, or branch
- View recruited student details per drive

### Company
- Register and await admin approval before accessing the full dashboard
- Create placement drives with job title, description, salary, and eligibility criteria
- Propose drive dates for admin confirmation
- Re-propose dates if admin rejects the proposed date
- Review student applications and mark as Selected or Rejected
- View drive profiles, application history, and recruited students

### Student
- Register with academic details — branch, CGPA, graduation year, and resume link
- Browse approved companies and their open placement drives
- Apply to eligible drives — eligibility enforced by CGPA, branch, and graduation year
- Track all application statuses in real time
- View placement record on dashboard once selected by a company

### System
- Automatic drive closure when drive date passes
- Automatic application cancellation when a company is blacklisted
- Automatic application restoration when blacklist is lifted
- Eligibility enforcement at apply time — ineligible students cannot apply

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database ORM | Flask-SQLAlchemy |
| Database | PostgreSQL (production), SQLite (local development) |
| Migrations | Flask-Migrate (Alembic) |
| Forms & Validation | Flask-WTF, WTForms |
| Authentication | Werkzeug password hashing, Flask session |
| Email | Flask-Mail (Gmail SMTP) |
| Frontend | Jinja2, Bootstrap 5.1.3, Bootstrap Icons |
| Environment | python-dotenv |
| Production Server | Gunicorn |
| Hosting | Render |

---

## Project Structure

```
campushire/
├── app/
│   ├── __init__.py          # App factory, extensions initialisation
│   ├── models.py            # SQLAlchemy models
│   ├── utils.py             # Shared utilities (close_expired_drives, student_eligible)
│   ├── routes/
│   │   ├── home.py          # Home page
│   │   ├── auth.py          # Login, register, logout
│   │   ├── admin.py         # Admin dashboard and management routes
│   │   ├── company.py       # Company dashboard and drive management
│   │   └── student.py       # Student dashboard, drives, applications
│   ├── templates/
│   │   ├── base.html
│   │   ├── _nav.html
│   │   ├── _sidebar.html
│   │   ├── _footer.html
│   │   ├── auth/
│   │   ├── home/
│   │   ├── admin/
│   │   ├── company/
│   │   └── student/
│   └── static/
│       ├── css/
│       │   ├── style.css
│       │   └── media.css
│       └── images/
├── migrations/              # Flask-Migrate migration files
├── .env                     # Local environment variables (gitignored)
├── .env.example             # Template for environment variables
├── .gitignore
├── create_admin.py          # Script to seed the admin account
├── requirements.txt
├── run.py                   # App entry point
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip
- Git

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/prajnanvaidya/campushire.git
cd campushire
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
```
Open `.env` and fill in your values. See [Environment Variables](#environment-variables) for details.

**5. Initialise the database**
```bash
flask db upgrade
```

**6. Create the admin account**
```bash
python create_admin.py
```

**7. Run the development server**
```bash
flask run
```

The app will be available at `http://127.0.0.1:5000`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the following:

```env
# Application
SECRET_KEY=your-secret-key-here

# Database — use sqlite:///site.db for local, postgresql://... for production
DATABASE_URL=sqlite:///site.db

# Mail (Gmail SMTP)
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-gmail@gmail.com

# Admin credentials (used by create_admin.py)
ADMIN_EMAIL=your-admin-email@gmail.com
ADMIN_PASSWORD=your-admin-password
```

### Gmail App Password

For `MAIL_PASSWORD` you must use a **Gmail App Password**, not your regular Gmail password:

1. Go to your Google Account → Security
2. Enable 2-Step Verification
3. Go to Security → App Passwords
4. Generate a new App Password for Mail
5. Paste the 16-character password into `MAIL_PASSWORD`

---

## Creating the Admin Account

The admin account does not go through the registration form. After setting up the database, run:

```bash
python create_admin.py
```

This reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your `.env` and inserts the admin record into the database. Running it again on an existing email safely skips without duplicating — it prints a message and exits cleanly.

---

## User Roles

### Admin
- Logs in at `/login` with role = Admin
- Pre-seeded via `create_admin.py` — not available through the registration form
- Full control over companies, students, drives, and applications

### Company
- Registers at `/register` → Company tab
- Starts with `approval_status = Pending` — dashboard is locked until admin approves
- Can be blacklisted — all drives are cancelled and all applications are withdrawn
- Blacklist can be reversed by admin — drives restore to Pending, applications restore to Applied

### Student
- Registers at `/register` → Student tab
- Can browse companies and drives immediately after registration
- Can only apply to `Approved` drives
- Eligibility (CGPA, branch, graduation year) is enforced at apply time

---

## Workflow

```
1. Company registers → status: Pending
2. Admin approves company → status: Approved
3. Company creates a placement drive → drive status: Pending
4. Admin reviews and approves the drive date → drive status: Approved
   └── If admin rejects the date → company proposes a new date → back to Pending
5. Students browse approved drives and apply
   └── Eligibility checked at apply time (CGPA, branch, graduation year)
6. Drive date passes → drive auto-closes → status: Closed
   └── Remaining Applied applications → auto-Rejected
7. Company reviews applications → marks each as Selected or Rejected
8. Selected students see a placement record card on their dashboard
```

---

## Database Models

| Model | Description |
|---|---|
| `Admin` | Placement administrator account |
| `Company` | Recruiting company with approval and blacklist status |
| `Student` | Student with academic details and resume link |
| `PlacementDrive` | A drive posted by a company with eligibility criteria, dates, and approval state |
| `Application` | A student's application to a drive with outcome status |
| `PlacementStat` | Final placement record for reporting |

### Application Status Flow
```
Applied → Selected   (company selects the student after interview)
Applied → Rejected   (company rejects, or drive auto-closes after drive date)
Applied → Cancelled  (company or student is blacklisted by admin)
```

### Drive Status Flow
```
Pending  → Approved  (admin approves the proposed drive date)
Pending  → Rejected  (company was blacklisted — all active drives cancelled)
Approved → Closed    (drive date passes — auto-closed by the system)
```

> **Note on date rejection:** When admin rejects a proposed drive date, `date_rejected`
> is set to `True` while the drive `approval_status` remains `Pending`. The company
> sees a banner notifying them to propose a new date. Once submitted, `date_rejected`
> resets to `False` and the drive re-enters the admin review queue.

---

## Author

Developed as a college project to digitise and streamline the campus placement process.

**GitHub:** [prajnanvaidya](https://github.com/prajnanvaidya)