from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import sqlite3
import os
import smtplib
from datetime import date, datetime
import heapq
from queue import Queue
import csv
from flask import Response
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


app = Flask(__name__, 
            template_folder='event_management/templates',
            static_folder='event_management/static')
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)

DATABASE_PATH = "database/app.db"

if not os.path.exists("database"):
    os.makedirs("database")

# Data Structures
user_map = {}  # For fast lookup of users
# event_map = {}  # For fast lookup of events
notification_heap = []  # Priority Queue for notifications
payment_queue = Queue()  # Queue for processing payments


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    # cursor.execute("SELECT * FROM users")
    # data = cursor.fetchall()
    # headers = [description[0] for description in cursor.description]

    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    headers = [description[0] for description in cursor.description]

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            organizer TEXT NOT NULL,
            venue TEXT NOT NULL,
            category TEXT NOT NULL,
            registration_fee REAL NOT NULL
        )
    """)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id),
            UNIQUE(user_id, event_id)
        )
    ''')

    conn.commit()
    conn.close()

    def generate():
        yield ','.join(headers) + '\n'
        for row in data:
            yield ','.join(map(str, row)) + '\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=users.csv"})

init_db()

user_roles = {"admin": "Admin", "organizer": "Organizer", "student": "Student"}

@app.route("/")
def home():
    return redirect(url_for("login"))

import re

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         email = request.form["username"]
#         raw_password = request.form["password"]
#         role = request.form["role"]

#         # Email validation
#         email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
#         if not re.match(email_pattern, email):
#             flash("Invalid email format. Please enter a valid email address.", "error")
#             return render_template("register.html", roles=user_roles)

#         if role in ["Admin", "Organizer"] and not email.lower().endswith("@ssn.edu.in"):
#             flash("Only institutional emails (@ssn.edu.in) allowed for Admin and Organizer.", "error")
#             return render_template("register.html", roles=user_roles)

#         # Hash password
#         password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

#         conn = sqlite3.connect(DATABASE_PATH)
#         cursor = conn.cursor()

#         try:
#             cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (email, password, role))
#             conn.commit()
#             user_map[email] = {"role": role}
#             flash("Registration successful!", "success")
#             return redirect(url_for("login"))
#         except sqlite3.IntegrityError:
#             flash("Username already exists!", "error")
#             return render_template("register.html", roles=user_roles)
#         finally:
#             conn.close()

#     # For GET requests, just load the form
#     return render_template("register.html", roles=user_roles)

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]

#         conn = sqlite3.connect(DATABASE_PATH)
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
#         user = cursor.fetchone()
#         conn.close()

#         if user and bcrypt.check_password_hash(user[2], password):
#             session["user"] = username
#             session["role"] = user[3]
#             user_map[username] = {"id": user[0], "role": user[3]}
#             return redirect(url_for("dashboard"))

#         return "Invalid credentials!"

#     return render_template("login.html")

import re
from flask import flash

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["username"]
        raw_password = request.form["password"]
        role = request.form["role"]

        # Email validation
        if not email.lower().endswith("@ssn.edu.in"):
            flash("Only institutional emails (@ssn.edu.in) are allowed for all roles.", "error")
            return render_template("register.html", roles=user_roles)

        # Password validation
        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
        if not re.match(password_pattern, raw_password):
            flash("Password must be at least 8 characters long, contain one uppercase, one lowercase, and one digit.", "error")
            return render_template("register.html", roles=user_roles)

        # Hash password
        password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (email, password, role))
            conn.commit()
            user_map[email] = {"role": role}
            flash("Registration successful!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
            return render_template("register.html", roles=user_roles)
        finally:
            conn.close()

    return render_template("register.html", roles=user_roles)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check for SSN email
        if not username.lower().endswith("@ssn.edu.in"):
            flash("Only SSN email addresses (@ssn.edu.in) are allowed.", "error")
            return render_template("login.html")

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            session["user"] = username
            session["role"] = user[3]
            user_map[username] = {"id": user[0], "role": user[3]}
            return redirect(url_for("dashboard"))

        flash("Invalid username or password!", "error")
        return render_template("login.html")

    return render_template("login.html")


def delete_past_events():
    today = date.today().isoformat()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE date < ?", (today,))
    conn.commit()
    conn.close()

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    delete_past_events()
    role = session.get("role", "Unknown")

    if role == "admin":
        return redirect(url_for("admin_panel"))
    elif role == "organizer":
        return redirect(url_for("organizer_dash"))
    elif role == "student":
        return redirect(url_for("student_dash"))

    return "Invalid role!"

@app.route("/admin")
def admin_panel():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()

    return render_template("admin_panel.html", users=users, events=events)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))

@app.route("/delete_event/<int:event_id>")
def delete_event(event_id):
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))

@app.route("/delete_own_event/<int:event_id>")
def delete_own_event(event_id):
    if "user" not in session or session["role"] != "organizer":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id=? AND organizer=?", (event_id, session["user"]))
    conn.commit()
    conn.close()
    return redirect(url_for("organizer_dash"))

@app.route("/organizer")
def organizer_dash():
    if "user" not in session or session["role"] != "organizer":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE organizer=?", (session["user"],))
    events = cursor.fetchall()
    conn.close()

    return render_template("organizer_dash.html", events=events)

@app.route("/student")
def student_dash():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    # Get filter parameters from query string
    category = request.args.get('category')
    venue = request.args.get('venue')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Base SQL query
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    # Apply filters
    if category:
        query += " AND category = ?"
        params.append(category)

    if venue:
        query += " AND venue LIKE ?"
        params.append(f"%{venue}%")

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    

    # Execute the query
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category FROM events")
    categories = [row[0] for row in cursor.fetchall()]
    
    cursor.execute(query, params)
    events = cursor.fetchall()
    conn.close()

    return render_template("student_dash.html", events=events, categories=categories)


from datetime import timedelta

# Define the BST Node and Tree class for event storage
class EventNode:
    def __init__(self, title, data):
        self.title = title
        self.data = data
        self.left = None
        self.right = None

class EventBST:
    def __init__(self):
        self.root = None

    def insert(self, title, data):
        self.root = self._insert(self.root, title, data)

    def _insert(self, node, title, data):
        if node is None:
            return EventNode(title, data)
        if title < node.title:
            node.left = self._insert(node.left, title, data)
        elif title > node.title:
            node.right = self._insert(node.right, title, data)
        return node

    def search(self, title):
        return self._search(self.root, title)

    def _search(self, node, title):
        if not node or node.title == title:
            return node
        elif title < node.title:
            return self._search(node.left, title)
        else:
            return self._search(node.right, title)

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append((node.title, node.data))
            self._inorder(node.right, result)


# Replace the hash map with the BST structure
event_bst = EventBST()

# In create_event, update this section
@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if "user" not in session or session["role"] != "organizer":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        date_value = request.form["date"]
        organizer = session["user"]
        venue = request.form["venue"]
        category = request.form["category"]
        registration_fee = request.form["registration_fee"]
        

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (title, description, date, organizer, venue, category, registration_fee )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, date_value, organizer, venue, category, registration_fee ))
        conn.commit()
        conn.close()

        # Insert into BST
        event_bst.insert(title, {
            "description": description,
            "date": date_value,
            "organizer": organizer,
            "venue": venue,
            "category": category,
            "registration_fee": registration_fee
        })

        heapq.heappush(notification_heap, (date_value, title))

        return redirect(url_for("organizer_dash"))

    return render_template("create_event.html", current_date=date.today().isoformat())


# You can now use event_bst.search(title) or event_bst.inorder() wherever needed


@app.route("/register_event/<int:event_id>", methods=["GET", "POST"])
def register_event(event_id):
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        return redirect(url_for("confirm_registration", event_id=event_id))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    if not event:
        return "Event not found!", 404

    return render_template("register_event.html", event=event, event_id=event_id)

@app.route("/available_events", methods=["GET"])
def available_events():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    category = request.args.get("category", "")
    venue = request.args.get("venue", "")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = "SELECT id, title, description, date, venue, category FROM events WHERE 1=1"
    params = []

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if venue:
        query += " AND venue LIKE ?"
        params.append(f"%{venue}%")

    cursor.execute(query, params)
    events = cursor.fetchall()
    conn.close()

    return render_template("available_events.html", events=events, category=category, venue=venue)



# @app.route("/confirm_registration/<int:event_id>", methods=["POST"])
# def confirm_registration(event_id):
#     if "user" not in session or session["role"] != "student":
#         return redirect(url_for("login"))

#     name = request.form["name"]
#     email = request.form["email"]
#     department = request.form["department"]
#     register_number = request.form["register_number"]
#     phone = request.form["phone"]

#     conn = sqlite3.connect(DATABASE_PATH)
#     cursor = conn.cursor()
    
#     cursor.execute("SELECT id FROM users WHERE username = ?", (session["user"],))
#     user = cursor.fetchone()

#     if user:
#         user_id = user[0]

#         # Check for duplicate registration
#         cursor.execute("SELECT * FROM registrations WHERE event_id = ? AND user_id = ?", (event_id, user_id))
#         already_registered = cursor.fetchone()

#         if already_registered:
#             conn.close()
#             flash("You are already registered for this event.", "warning")
#             return redirect(url_for("registered_events"))

#         cursor.execute("INSERT INTO registrations (event_id, user_id) VALUES (?, ?)", (event_id, user_id))
#         conn.commit()

    conn.close()
    return redirect(url_for("send_email_notification", email=email))


@app.route("/send_email_notification/<email>")
def send_email_notification(email):
    sender_email = "hariniharibabu06@gmail.com"
    sender_password = "kjqs wcin ujwq fvgs"  # Use environment variables in production!
    subject = "Event Registration Confirmation"
    message = f"Hello,\n\nYou have successfully registered for the event.\n\nThank you!"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        email_message = f"Subject: {subject}\n\n{message}"
        server.sendmail(sender_email, email, email_message)
        server.quit()
        return render_template("email_sent.html", email=email)

    except Exception as e:
        return f"Error sending email: {str(e)}"
    
    
@app.route("/registered_events")
def registered_events():
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
# Now valid because users + events + registrations are in same DB
    cursor.execute("""
        SELECT events.id, events.title, events.description, events.date, events.organizer
        FROM registrations
        JOIN events ON registrations.event_id = events.id
        JOIN users ON registrations.user_id = users.id
        WHERE users.username = ?
    """, (session["user"],))

    events = cursor.fetchall()
    conn.close()

    return render_template("registered_events.html", events=events)


@app.route("/unregister_event/<int:event_id>")
def unregister_event(event_id):
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM registrations 
        WHERE event_id = ? AND user_id = (SELECT id FROM users WHERE username = ?)
    """, (event_id, session["user"]))
    conn.commit()
    conn.close()

    flash("You have successfully unregistered from the event.", "info")
    return redirect(url_for("registered_events"))

@app.route("/view_registrations/<int:event_id>")
def view_registrations(event_id):
    if "user" not in session or session["role"] != "organizer":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Fetch students who registered for the given event
    cursor.execute("""
        SELECT users.username 
        FROM registrations
        JOIN users ON registrations.user_id = users.id
        WHERE registrations.event_id = ?
    """, (event_id,))

    registrations = cursor.fetchall()
    conn.close()

    return render_template("view_registrations.html", registrations=registrations, event_id=event_id)

# Generate PDF with a clean report format
def generate_pdf(user_name, events):
    buffer = BytesIO()
    
    # Create the PDF document using SimpleDocTemplate for better layout management
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Container for all elements to be added to the PDF
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=16, 
        textColor=colors.HexColor('#2a5885'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
        leftIndent=5,
        spaceAfter=6
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#1c4587'),
        spaceAfter=10,
        spaceBefore=20
    )
    
    # Add title and subtitle
    elements.append(Paragraph("<b>Event Registration Report</b>", title_style))
    elements.append(Paragraph(f"{user_name}", subtitle_style))
    
    # Add generation date
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"<i>Generated on: {date_str}</i>", info_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add decorative separator
    separator_data = [[' ']]
    separator_table = Table(separator_data, colWidths=[7*inch], rowHeights=[2])
    separator_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#4a86e8')),
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#2a5885')),
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#2a5885')),
    ]))
    elements.append(separator_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add event summary
    elements.append(Paragraph(f"<b>Event Summary</b> ({len(events)} event{'s' if len(events) != 1 else ''})", header_style))
    
    # Create data for the events table
    if events:
        # Header row for table
        table_data = [['#', 'Event Title', 'Date', 'Organizer']]
        
        # Add event data
        for idx, event in enumerate(events, 1):
            event_title = event[1]
            event_date = event[3]
            event_organizer = event[4]
            
            table_data.append([str(idx), event_title, event_date, event_organizer])
        
        # Create the table with specific column widths
        col_widths = [0.3*inch, 2.7*inch, 1.5*inch, 2.2*inch]
        event_table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        table_style = TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a86e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Body styling
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Index column centered
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f3f6f9'), colors.HexColor('#ffffff')]),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4a86e8')),
            
            # Row padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        # Apply the style to the table
        event_table.setStyle(table_style)
        elements.append(event_table)
        
        # Add detailed event information
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("<b>Event Details</b>", header_style))
        
        for idx, event in enumerate(events, 1):
            event_title = event[1]
            event_description = event[2]
            event_date = event[3]
            event_organizer = event[4]
            
            # Event card styling
            event_card = []
            event_card.append([Paragraph(f"<b>{idx}. {event_title}</b>", styles['Heading3'])])
            
            # Event details in 2-column layout
            detail_data = [
                [Paragraph("<b>Date:</b>", styles['Normal']), Paragraph(event_date, styles['Normal'])],
                [Paragraph("<b>Organizer:</b>", styles['Normal']), Paragraph(event_organizer, styles['Normal'])],
                [Paragraph("<b>Description:</b>", styles['Normal']), Paragraph(event_description, styles['Normal'])]
            ]
            
            details_table = Table(detail_data, colWidths=[1*inch, 5.7*inch])
            details_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            event_card.append([details_table])
            
            # Create card table
            card_table = Table(event_card, colWidths=[6.7*inch])
            card_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9eef7')),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc')),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ]))
            
            elements.append(card_table)
            elements.append(Spacer(1, 0.2*inch))
    else:
        # No events message
        elements.append(Paragraph("No events have been registered.", styles['Normal']))
    
    # Add footer with separator
    elements.append(Spacer(1, 0.3*inch))
    elements.append(separator_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # Footer text
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("SSN College of Engineering - Event Management System", footer_style))
    
    # Build the PDF document
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

# Send the PDF as email attachment
def send_email_with_pdf(email, user_name, events):
    sender_email = "hariniharibabu06@gmail.com"
    sender_password = "kjqs wcin ujwq fvgs"
    subject = "Your Event Registration Report"
    body = f"Hello {user_name},\n\nPlease find attached your event registration report.\n\nRegards,\nEvent Management Team"

    pdf_buffer = generate_pdf(user_name, events)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        pdf_attachment = MIMEApplication(pdf_buffer.read(), _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename="registration_report.pdf")
        msg.attach(pdf_attachment)

        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        return "Email with report sent successfully!"
    except Exception as e:
        return f"Error sending email: {str(e)}"

# Confirm event registration and send report for the registered event only
@app.route("/confirm_registration/<int:event_id>", methods=["POST"])
def confirm_registration(event_id):
    if "user" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    name = request.form["name"]
    email = request.form["email"]
    department = request.form["department"]
    register_number = request.form["register_number"]
    phone = request.form["phone"]

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (session["user"],))
    user = cursor.fetchone()

    if user:
        user_id = user[0]

        cursor.execute("SELECT * FROM registrations WHERE event_id = ? AND user_id = ?", (event_id, user_id))
        already_registered = cursor.fetchone()

        if already_registered:
            conn.close()
            flash("You are already registered for this event.", "warning")
            return redirect(url_for("registered_events"))

        cursor.execute("INSERT INTO registrations (event_id, user_id) VALUES (?, ?)", (event_id, user_id))
        conn.commit()

        cursor.execute("""
            SELECT events.id, events.title, events.description, events.date, events.organizer
            FROM events
            WHERE events.id = ?
        """, (event_id,))
        new_event = cursor.fetchall()

        conn.close()

        return send_email_with_pdf(email, name, new_event)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
