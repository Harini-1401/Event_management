# 🎉 Event Management System

A full-stack web application built using **Python**, **Flask**, **HTML**, **CSS**, and **SQLite** that streamlines the process of organizing, managing, and participating in events within an educational institution.

---

## 📖 Overview

The **Event Management System** is designed to simplify event management for colleges and universities by providing dedicated portals for **Administrators**, **Organizers**, and **Students**. The platform enables organizers to create and manage events, allows students to discover and register for events, and provides administrators with a centralized dashboard to monitor platform activities.

---

## ✨ Features

### 👨‍💼 Administrator

* Secure administrator login
* Monitor all events created on the platform
* View registered users
* Monitor overall platform activity
* Manage organizers and students
* Access system-wide statistics

### 📝 Organizer

* Secure organizer authentication
* Create new events
* Update event details
* Delete events
* View students registered for each event
* Manage event information

### 🎓 Student

* Secure student authentication
* Browse available events
* View detailed event information
* Register for events
* View registered events
* Manage event registrations

---

## 🛠️ Tech Stack

| Category         | Technologies                |
| ---------------- | --------------------------- |
| **Backend**      | Python, Flask               |
| **Frontend**     | HTML, CSS                   |
| **Database**     | SQLite                      |
| **Architecture** | MVC (Model-View-Controller) |

---

## 📂 Project Structure

```text
Event-Management/
│
├── static/             # CSS, images, and static assets
├── templates/          # HTML templates
├── routes/             # Application routes
├── models/             # Database models
├── database/           # SQLite database
├── app.py              # Application entry point
├── requirements.txt
└── README.md
```

> *The folder structure may vary slightly depending on your implementation.*

---

## 🚀 Getting Started

### Prerequisites

* Python 3.x
* pip

### Installation

1. Clone the repository

```bash
git clone https://github.com/your-username/Event-Management.git
```

2. Navigate to the project directory

```bash
cd Event-Management
```

3. Install the required packages

```bash
pip install -r requirements.txt
```

4. Run the Flask application

```bash
python app.py
```

5. Open your browser and visit

```text
http://127.0.0.1:5000
```

---

## 👥 User Roles

### Administrator

The administrator oversees the complete platform and is responsible for monitoring users, organizers, and events. The admin dashboard provides insights into overall platform activity and event statistics.

### Organizer

Organizers can create, update, and manage events. They can also view the list of students who have registered for their events, enabling efficient event coordination.

### Student

Students can explore available events, view event details, register for events of interest, and manage their registrations through a dedicated dashboard.

---

## 🔄 Application Workflow

1. Users register and log in based on their assigned role.
2. Organizers create and publish events.
3. Students browse available events.
4. Students register for preferred events.
5. Organizers monitor participant registrations.
6. Administrators oversee all users and platform activities.

---

## 📊 Key Functionalities

* Role-Based Authentication
* Event Creation and Management
* Student Registration System
* Event Listing
* Dashboard for Administrators
* Organizer Management
* Registration Tracking
* SQLite Database Integration
* Responsive User Interface

---

## 📷 Screenshots


* Login Page
  <img width="718" height="904" alt="image" src="https://github.com/user-attachments/assets/116b9c86-1eb8-4ff7-95d2-45063d75af92" />

* Student Dashboard
  <img width="2248" height="1374" alt="image" src="https://github.com/user-attachments/assets/0ddabaa5-06c6-49ef-b2c8-3ce1c8d128d5" />

* Organizer Dashboard
  
  <img width="2248" height="1387" alt="image" src="https://github.com/user-attachments/assets/df43be23-35d9-4d92-8928-406ac8ee53dd" />
  <img width="2233" height="1377" alt="image" src="https://github.com/user-attachments/assets/4b551f31-0ba5-4d64-a941-afa68ba4b666" />

* Admin Dashboard
  <img width="2245" height="1386" alt="image" src="https://github.com/user-attachments/assets/8bf3b1be-d920-4a45-b568-63e10a2c64b5" />

* Event Registration Page
  <img width="1127" height="689" alt="image" src="https://github.com/user-attachments/assets/10afa195-73ae-4013-9122-a15e866b4690" />


---

## 🔮 Future Enhancements

* Email notifications for event registration
* Event approval workflow
* QR code-based attendance tracking
* Certificate generation
* Event reminders
* Search and filtering options
* Pagination
* User profile management
* Analytics dashboard with charts
* Cloud database integration
* Docker deployment

---

## 📄 License

This project is intended for educational and learning purposes.

---

## 👨‍💻 Author

Developed as a Full Stack Web Development project using Flask and SQLite.
