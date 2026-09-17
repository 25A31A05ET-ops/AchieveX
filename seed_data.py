import os
import sqlite3
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from database import DB_PATH, init_db


def seed_database():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    users = [
        ("Aarav Sharma", "student@demo.com", "student123", "STUDENT", "Computer Science and Engineering", "2024-25"),
        ("Diya Nair", "diya@demo.com", "student123", "STUDENT", "Electronics and Communication Engineering", "2023-24"),
        ("Rohan Mehta", "rohan@demo.com", "student123", "STUDENT", "Mechanical Engineering", "2022-23"),
        ("Sneha Iyer", "sneha@demo.com", "student123", "STUDENT", "Information Technology", "2024-25"),
        ("Karthik Rao", "karthik@demo.com", "student123", "STUDENT", "Electrical Engineering", "2023-24"),
        ("Priya Singh", "priya@demo.com", "student123", "STUDENT", "Computer Science and Engineering", "2024-25"),
        ("Vikram Patel", "vikram@demo.com", "student123", "STUDENT", "Mechanical Engineering", "2022-23"),
        ("Ananya Joshi", "ananya@demo.com", "student123", "STUDENT", "Electronics and Communication Engineering", "2024-25"),
        ("Dr. Meera Kulkarni", "faculty@demo.com", "faculty123", "FACULTY", "Computer Science and Engineering", "2024-25"),
        ("Prof. Anil Deshmukh", "anil@demo.com", "faculty123", "FACULTY", "Mechanical Engineering", "2024-25"),
        ("Dr. Snehal Verma", "snehal@demo.com", "faculty123", "FACULTY", "Electrical Engineering", "2024-25"),
        ("Prof. Arjun Nand", "arjun@demo.com", "faculty123", "FACULTY", "Information Technology", "2024-25"),
        ("Admin Verifier", "admin@demo.com", "admin123", "VERIFIER", "Administration", "2024-25"),
    ]

    existing = conn.execute("SELECT email FROM users").fetchall()
    existing_emails = {row["email"] for row in existing}
    for user in users:
        if user[1] not in existing_emails:
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, department, academic_year, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user[0], user[1], generate_password_hash(user[2]), user[3], user[4], user[5], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
            )

    conn.commit()

    student_rows = conn.execute("SELECT id, name FROM users WHERE role = 'STUDENT' ORDER BY id").fetchall()
    faculty_rows = conn.execute("SELECT id, name FROM users WHERE role = 'FACULTY' ORDER BY id").fetchall()
    verifier_rows = conn.execute("SELECT id, name FROM users WHERE role = 'VERIFIER' ORDER BY id").fetchall()

    achievements = [
        {
            "user_id": student_rows[0]["id"], "title": "Smart City IoT Challenge Winner", "category": "Hackathon", "achievement_type": "Competition", "organization": "NIT Trichy Innovation Fest", "achievement_date": "2025-02-12", "position": "1st Place", "description": "Built an end-to-end smart city monitoring dashboard using IoT sensors and predictive analytics.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 1,
        },
        {
            "user_id": student_rows[0]["id"], "title": "AWS Cloud Practitioner", "category": "Certification", "achievement_type": "Certification", "organization": "Amazon Web Services", "achievement_date": "2025-01-18", "position": "Certified", "description": "Completed foundational cloud architecture and services training with AWS.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[1]["id"], "title": "Robotics Line Follower Design", "category": "Technical", "achievement_type": "Project", "organization": "TechnoVation Robotics Club", "achievement_date": "2024-11-08", "position": "Top 5", "description": "Designed and demonstrated autonomous obstacle avoidance and line-following robot.", "department": "Electronics and Communication Engineering", "academic_year": "2023-24", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[1]["id"], "title": "Paper Presentation on AI in Healthcare", "category": "Research", "achievement_type": "Presentation", "organization": "IEEE Student Chapter", "achievement_date": "2024-09-14", "position": "Second Prize", "description": "Presented a study on AI-aided diagnostics and predictive models in healthcare systems.", "department": "Electronics and Communication Engineering", "academic_year": "2023-24", "status": "PENDING", "is_featured": 0,
        },
        {
            "user_id": student_rows[2]["id"], "title": "National Level CAD Design Contest", "category": "Technical", "achievement_type": "Competition", "organization": "DesignX India", "achievement_date": "2024-08-22", "position": "Runner Up", "description": "Developed a CAD prototype for sustainable mechanical systems and won second place.", "department": "Mechanical Engineering", "academic_year": "2022-23", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[2]["id"], "title": "Campus Marathon Participation", "category": "Sports", "achievement_type": "Event", "organization": "College Sports Fest", "achievement_date": "2024-12-02", "position": "Third Place", "description": "Completed 10K run with podium finish in campus annual sports meet.", "department": "Mechanical Engineering", "academic_year": "2022-23", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[3]["id"], "title": "HackSphere 2025 Finalist", "category": "Hackathon", "achievement_type": "Hackathon", "organization": "HackSphere Bengaluru", "achievement_date": "2025-03-09", "position": "Finalist", "description": "Built a secure campus resource allocation platform for improved student services.", "department": "Information Technology", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 1,
        },
        {
            "user_id": student_rows[3]["id"], "title": "Web Development Bootcamp", "category": "Coding", "achievement_type": "Certification", "organization": "Skillrack Academy", "achievement_date": "2024-10-13", "position": "Completion", "description": "Completed a hands-on training on responsive web technologies and JavaScript frameworks.", "department": "Information Technology", "academic_year": "2024-25", "status": "REJECTED", "is_featured": 0,
        },
        {
            "user_id": student_rows[4]["id"], "title": "Power Systems Innovation Demo", "category": "Innovation", "achievement_type": "Project", "organization": "Green Energy Expo", "achievement_date": "2024-07-20", "position": "Selected", "description": "Presented a low-cost power optimization prototype for sustainable campus utility planning.", "department": "Electrical Engineering", "academic_year": "2023-24", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[4]["id"], "title": "Intercollege Debate Winner", "category": "Leadership", "achievement_type": "Event", "organization": "VIT Intercollege Forum", "achievement_date": "2024-11-18", "position": "Winner", "description": "Won an inter-college debate on sustainability and institutional leadership.", "department": "Electrical Engineering", "academic_year": "2023-24", "status": "PENDING", "is_featured": 0,
        },
        {
            "user_id": student_rows[5]["id"], "title": "CodeSprint 2025 Team Winner", "category": "Coding", "achievement_type": "Competition", "organization": "CodeSprint Council", "achievement_date": "2025-01-16", "position": "1st Place", "description": "Built a high-performance algorithmic solution for urban mobility analytics.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[5]["id"], "title": "Cultural Dance Performance", "category": "Cultural", "achievement_type": "Performance", "organization": "Annual Cultural Fest", "achievement_date": "2024-02-13", "position": "Best Performance", "description": "Performed a contemporary dance sequence representing the college in the annual cultural festival.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[6]["id"], "title": "Industrial Internship Approval", "category": "Technical", "achievement_type": "Internship", "organization": "Infosys Innovation Lab", "achievement_date": "2024-06-01", "position": "Selected Intern", "description": "Completed a project internship focused on digital transformation and enterprise workflow automation.", "department": "Mechanical Engineering", "academic_year": "2022-23", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[6]["id"], "title": "Startup Pitch Round", "category": "Entrepreneurship", "achievement_type": "Pitch", "organization": "E-Cell Startup Weekend", "achievement_date": "2025-02-03", "position": "Shortlisted", "description": "Pitched a sustainable mobility prototype addressing local commute efficiency with smart micro-logistics.", "department": "Mechanical Engineering", "academic_year": "2022-23", "status": "PENDING", "is_featured": 0,
        },
        {
            "user_id": student_rows[7]["id"], "title": "Embedded Systems Project Expo", "category": "Innovation", "achievement_type": "Project", "organization": "Embedded Systems Expo", "achievement_date": "2024-09-25", "position": "Merit Winner", "description": "Developed a sensor-driven assistive device for real-time environmental monitoring.", "department": "Electronics and Communication Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[7]["id"], "title": "Volunteer Leadership Recognition", "category": "Leadership", "achievement_type": "Recognition", "organization": "Campus Volunteer Council", "achievement_date": "2024-11-23", "position": "Leadership Award", "description": "Led student volunteer planning for community events with measurable operational success.", "department": "Electronics and Communication Engineering", "academic_year": "2024-25", "status": "PENDING", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[0]["id"], "title": "AI in Education Research Grant", "category": "Research", "achievement_type": "Grant", "organization": "DST SERB", "achievement_date": "2025-01-10", "position": "Principal Investigator", "description": "Secured a research grant focused on adaptive AI models for personalized learning systems.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 1,
        },
        {
            "user_id": faculty_rows[0]["id"], "title": "Published IEEE Conference Paper", "category": "Research", "achievement_type": "Publication", "organization": "IEEE International Conference", "achievement_date": "2024-08-28", "position": "Author", "description": "Published a peer-reviewed paper on secure distributed learning architectures for smart campuses.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[1]["id"], "title": "Advanced Manufacturing Patent Filed", "category": "Innovation", "achievement_type": "Patent", "organization": "IPR Cell", "achievement_date": "2024-10-30", "position": "Inventor", "description": "Filed a patent for a low-cost additive manufacturing process for industrial prototypes.", "department": "Mechanical Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[1]["id"], "title": "Faculty Development Program Completion", "category": "Certification", "achievement_type": "Certification", "organization": "NPTEL", "achievement_date": "2024-12-05", "position": "Elite Category", "description": "Completed an advanced certification in industry 4.0 and digital manufacturing systems.", "department": "Mechanical Engineering", "academic_year": "2024-25", "status": "PENDING", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[2]["id"], "title": "Power Grid Optimization Workshop", "category": "Technical", "achievement_type": "Conference", "organization": "IEEE PES Conference", "achievement_date": "2024-09-19", "position": "Session Chair", "description": "Chaired a technical session on intelligent power distribution and smart energy planning.", "department": "Electrical Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[2]["id"], "title": "Sustainability Research Award", "category": "Leadership", "achievement_type": "Award", "organization": "Green Campus Council", "achievement_date": "2025-02-19", "position": "Awardee", "description": "Recognized for impactful sustainability research and implementation in campus energy systems.", "department": "Electrical Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[3]["id"], "title": "Cloud Security Webinar Speaker", "category": "Technical", "achievement_type": "Conference", "organization": "CyberSec Summit", "achievement_date": "2024-11-11", "position": "Keynote Speaker", "description": "Delivered a keynote on secure cloud infrastructure and resilient digital systems in higher education.", "department": "Information Technology", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[3]["id"], "title": "Data Science Lab Accreditation", "category": "Technical", "achievement_type": "Certification", "organization": "Microsoft Learn", "achievement_date": "2024-07-09", "position": "Accredited Mentor", "description": "Achieved mentorship accreditation for digital transformation and AI lab operations.", "department": "Information Technology", "academic_year": "2024-25", "status": "REJECTED", "is_featured": 0,
        },
        {
            "user_id": student_rows[0]["id"], "title": "Campus Tech Fest Quiz Champion", "category": "Technical", "achievement_type": "Competition", "organization": "Campus Tech Fest", "achievement_date": "2024-03-06", "position": "Champion", "description": "Won the annual campus quiz competition on computing fundamentals and innovation.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[4]["id"], "title": "Solar Energy Prototype Showcase", "category": "Innovation", "achievement_type": "Project", "organization": "Green Energy Challenge", "achievement_date": "2024-04-16", "position": "Finalist", "description": "Showcased a renewable microgrid prototype for distributed energy management.", "department": "Electrical Engineering", "academic_year": "2023-24", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[7]["id"], "title": "Cultural Team Leadership", "category": "Leadership", "achievement_type": "Recognition", "organization": "Cultural Team Council", "achievement_date": "2025-02-28", "position": "Team Captain", "description": "Led a student team in the college cultural showcase with successful event curation and coordination.", "department": "Electronics and Communication Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": faculty_rows[0]["id"], "title": "Innovation Mentor Recognition", "category": "Leadership", "achievement_type": "Award", "organization": "Student Innovation Cell", "achievement_date": "2024-05-17", "position": "Mentor of the Year", "description": "Recognized for mentoring student innovation projects and startup incubation support.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "VERIFIED", "is_featured": 0,
        },
        {
            "user_id": student_rows[5]["id"], "title": "Open Source Contribution", "category": "Technical", "achievement_type": "Contribution", "organization": "GitHub Community", "achievement_date": "2025-03-12", "position": "Contributor", "description": "Contributed to an open-source repository improving UI components and API integration docs.", "department": "Computer Science and Engineering", "academic_year": "2024-25", "status": "PENDING", "is_featured": 0,
        },
    ]

    existing_achievements = conn.execute("SELECT id, user_id, title FROM achievements").fetchall()
    if not existing_achievements:
        for achievement in achievements:
            conn.execute(
                "INSERT INTO achievements (user_id, title, category, achievement_type, organization, achievement_date, position, description, department, academic_year, status, is_featured, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    achievement["user_id"],
                    achievement["title"],
                    achievement["category"],
                    achievement["achievement_type"],
                    achievement["organization"],
                    achievement["achievement_date"],
                    achievement["position"],
                    achievement["description"],
                    achievement["department"],
                    achievement["academic_year"],
                    achievement["status"],
                    achievement["is_featured"],
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

    conn.commit()

    achievement_rows = conn.execute("SELECT id, user_id, status FROM achievements ORDER BY id").fetchall()
    if not conn.execute("SELECT id FROM verifications LIMIT 1").fetchone():
        for index, item in enumerate(achievement_rows):
            if item["status"] == "VERIFIED":
                verifier_id = verifier_rows[0]["id"] if verifier_rows else None
                conn.execute(
                    "INSERT INTO verifications (achievement_id, verifier_id, status, remarks, verified_at) VALUES (?, ?, ?, ?, ?)",
                    (item["id"], verifier_id, "APPROVED", "Verified against institutional records and uploaded evidence.", (datetime.utcnow() - timedelta(days=15 + index)).strftime("%Y-%m-%d %H:%M:%S")),
                )
            elif item["status"] == "REJECTED":
                conn.execute(
                    "INSERT INTO verifications (achievement_id, verifier_id, status, remarks, verified_at) VALUES (?, ?, ?, ?, ?)",
                    (item["id"], verifier_rows[0]["id"] if verifier_rows else None, "REJECTED", "Supporting evidence was incomplete or not aligned with the stated achievement.", (datetime.utcnow() - timedelta(days=10 + index)).strftime("%Y-%m-%d %H:%M:%S")),
                )

    conn.commit()
    conn.close()
    print("Demo data inserted successfully.")


if __name__ == "__main__":
    seed_database()
