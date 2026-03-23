# CampusHire — Campus Placement Management System

A full-stack web application that simplifies and centralises the campus placement process for students, companies, and placement administrators. Built with Flask, SQLAlchemy, and Bootstrap 5.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Creating the Admin Account](#creating-the-admin-account)
- [User Roles](#user-roles)
- [Workflow](#workflow)
- [Database Models](#database-models)

---

## Overview

CampusHire is a campus placement portal that connects students with recruiting companies through a structured, admin-moderated workflow. Companies register and post placement drives, students apply based on eligibility criteria, and the placement admin oversees approvals, company verifications, and overall placement activity.

The platform handles the complete placement lifecycle — from company registration and drive creation to student applications, interview outcomes, and final placement records.

---

## Features

### Admin
- Approve or reject company registrations
- Approve or reject proposed drive dates
- Blacklist and un-blacklist companies and students
- View all companies, students, drives, and applications with filters and pagination
- Search across students and companies
- View recruited student details per drive

### Company
- Register and await admin approval
- Create placement drives with job details, eligibility criteria, and salary
- Propose drive dates for admin confirmation
- Re-propose dates if admin rejects them
- Review student applications and mark as Selected or Rejected
- View drive profiles and application history

### Student
- Register with academic details and resume link
- Browse approved companies and placement drives
- Apply to eligible drives (eligibility enforced by CGPA, branch, graduation year)
- Track application statuses in real time
- View placement record if selected

### System
- Automatic drive closure when drive date passes
- Automatic application cancellation when company is blacklisted
- Automatic application restoration when blacklist is lifted
- Eligibility enforcement at application time — ineligible students cannot apply

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database ORM | Flask-SQLAlchemy |
| Database | SQLite |
| Migrations | Flask-Migrate (Alembic) |
| Forms & Validation | Flask-WTF, WTForms |
| Authentication | Werkzeug password hashing, Flask session |
| Email | Flask-Mail (Gmail SMTP) |
| Frontend | Jinja2, Bootstrap 5.1.3, Bootstrap Icons |
| Environment | python-dotenv |

---

## Project Structure

```
placement-portal-application-v1/
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
git clone https://github.com/yourusername/campushire.git
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

# Database
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

This reads `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your `.env` and inserts the admin record into the database. Run this only once. If you run it again on an existing email it will skip and print a message.

---

## User Roles

### Admin
- Logs in at `/login` with role = Admin
- Pre-seeded via `create_admin.py`
- Full control over companies, students, drives, and applications

### Company
- Registers at `/register` → Company tab
- Starts with `approval_status = Pending`
- Cannot create drives until admin approves registration
- Can be blacklisted — all drives cancelled, all applications withdrawn

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
3. Company creates a drive → drive status: Pending
4. Admin approves drive date → drive status: Approved
   └── If admin rejects date → company proposes new date → back to Pending
5. Students apply to approved drives
   └── Eligibility checked at apply time (CGPA, branch, batch)
6. Drive date passes → auto-closes → status: Closed
   └── Applied applications → Rejected automatically
7. Company reviews applications → marks Selected or Rejected
8. Selected students see placement record on dashboard
```

---

## Database Models

| Model | Description |
|---|---|
| `Admin` | Placement administrator account |
| `Company` | Recruiting company with approval and blacklist status |
| `Student` | Student with academic details and resume |
| `PlacementDrive` | A drive posted by a company with eligibility, dates, and approval state |
| `Application` | A student's application to a drive with outcome status |
| `PlacementStat` | Final placement record (optional, for reporting) |

### Application Status Flow
```
Applied → Selected  (company selects after interview)
Applied → Rejected  (company rejects, or drive auto-closes)
Applied → Cancelled (company blacklisted, or student blacklisted)
```

### Drive Status Flow
```
Pending  → Approved  (admin approves the proposed drive date)
Pending  → Rejected  (company was blacklisted — all drives cancelled)
Approved → Closed    (drive date passes — auto-closed by system)
```

> Note: Date rejection is separate from drive status. When admin rejects a proposed
> date, `date_rejected` is set to `True` while the drive status remains `Pending`.
> The company is notified to propose a new date. Once a new date is submitted,
> `date_rejected` resets to `False` and the drive goes back into admin review.

---

## Author

Developed as a college project to digitise and streamline the campus placement process.