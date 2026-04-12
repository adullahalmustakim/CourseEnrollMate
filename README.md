# 🎓 CourseEnrollMate  
*A University Course Enrollment Management System*

---

## 📌 Overview

CourseEnrollMate is a role-based web application designed to automate and streamline the university course enrollment process. It replaces manual and inefficient registration systems with a structured, transparent and rule-based platform.

The system allows students to request course enrollment while administrators manage courses, semesters, prerequisites, seat limits and enrollment approvals efficiently.

---

## 🚀 Features

### 👨‍🎓 Student Features
- User registration and login  
- View available courses  
- Submit enrollment requests  
- View enrolled courses with total credit hours  
- Drop courses within deadline  
- View rejected courses with reasons  

---

### 🛠️ Admin Features
- Add, edit and delete courses  
- Manage credit hours  
- Define prerequisites  
- Manage semesters (create, activate)  
- Assign courses to semesters  
- Set seat limits  
- Approve/reject enrollment requests  
- Manage enrollment & drop deadlines  
- View enrollment reports  

---

### 👨‍💻 Developer Features
- Approve or reject admin registration requests  
- Maintain system access control  

---

## 🧠 System Highlights

- Role-Based Access Control (RBAC)  
- Prerequisite validation  
- Seat limit enforcement  
- Enrollment & drop deadline control  
- Enrollment tracking system  
- Reporting and analytics  

---

## 🏗️ Tech Stack

- **Backend:** Python (Flask)  
- **Frontend:** HTML, CSS  
- **Database:** SQLite  
- **Authentication:** Flask-Session, Werkzeug Security  

---

## ⚙️ Installation & Setup

### 1. Clone Repository

git clone https://github.com/adullahalmustakim/CourseEnrollMate

cd courseenrollmate


### 2. Create Virtual Environment

python -m venv venv


Activate:
- Windows:

venv\Scripts\activate

- Mac/Linux:

source venv/bin/activate


### 3. Install Dependencies

pip install -r requirements.txt


### 4. Setup Database

python create_db.py


### 5. Run Application

python app.py


### 6. Open in Browser

http://127.0.0.1:5000/


---

## 🔐 Usage Flow

- Register as **Student** → Login directly  
- Register as **Admin** → Requires developer approval  
- Developer approves admin → Admin can access system  

---

## 📊 Database Overview

Main Tables:
- users  
- courses  
- course_offerings  
- enrollment_requests  
- course_prerequisites  
- enrollment_deadline  
- drop_deadline  
- admin_requests  
- developers  

---

## 👥 Team Members

- Abdullah Al Mustakim (0242310005341093) – Backend Developer & & Project Deployment
- Md. Mirajul Islam (0242310005341094) – Database Designer & Frontend Developer
- Md. Hashibur Rahman Shuvo (0242310005341169) – System Logic & Rule Enforcement Developer  

---

## 🔮 Future Enhancements

- Faculty/Instructor role  
- CGPA-based eligibility  
- Notification system  
- Analytics dashboard  
- Payment integration  
- Mobile-friendly UI  

---

## 📜 License

This project is developed for academic purposes only.
