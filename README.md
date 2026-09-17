# AchieveX

AchieveX is a digital student and faculty achievement management system built with Flask and SQLite. It enables achievement submission, verification workflows, public showcase, analytics, reporting, and digital passport generation.

## Features

- Role-based authentication for Student, Faculty, and Verifier/Admin
- Achievement submission with certificate and evidence uploads
- Verification workflow with approve and reject actions
- Public gallery for verified achievements only
- Dashboard analytics with real SQLite-backed metrics
- CSV reporting and filterable tables
- Profile views and achievement passport printing
- Demo data for hackathon presentation

## Demo Accounts

- Student: student@demo.com / student123
- Faculty: faculty@demo.com / faculty123
- Admin: admin@demo.com / admin123

## Run locally

1. Open a terminal in the AchieveX folder.
2. Create a virtual environment (optional but recommended):
   python -m venv .venv
3. Activate it:
   - Windows: .venv\Scripts\activate
4. Install requirements:
   pip install -r requirements.txt
5. Initialize and seed the database:
   python seed_data.py
6. Start the application:
   python app.py
7. Open http://127.0.0.1:5000

## Project structure

- app.py: Flask application and route logic
- database.py: SQLite initialization and database connection helpers
- seed_data.py: demo users and sample achievement data
- static/: CSS, JS, and images
- templates/: HTML pages
- uploads/: uploaded certificate and evidence files
- database/achievex.db: SQLite database file

## Notes

The app uses secure password hashing, session-based authentication, and upload validation for PDF, PNG, JPG, and JPEG files.
