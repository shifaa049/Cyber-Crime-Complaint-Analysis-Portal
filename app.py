from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import random
import google.generativeai as genai
from flask import send_file
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


app = Flask(__name__)
app.secret_key = "cybercrime123"


def categorize_complaint(description):
    text = description.lower()

    # Social Media Fraud
    if "instagram" in text or "facebook" in text or "whatsapp" in text:
        return "Social Media Fraud"

    # OTP Scam
    elif "otp" in text:
        return "OTP Scam"

    # UPI Fraud
    elif "upi" in text or "gpay" in text or "phonepe" in text:
        return "UPI Fraud"

    # Email Spam
    elif ("email" in text or "mail" in text or "gmail" in text or
          "outlook" in text  or "attachment" in text):
        return "Email Spam"

    # Phishing
    elif "login" in text or "link" in text or "bank" in text:
        return "Phishing"

    # Others
    else:
        return "Other"
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("officer_home"))
        else:
            return "Invalid Credentials"

    return render_template("login.html")


# ✅ CLEAN COMPLAINT ROUTE (MATCHES YOUR FORM)
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if request.method == "POST":

        name = request.form["name"]
        address = request.form["address"]
        phone = request.form["phone"]
        description = request.form["description"]

        category = categorize_complaint(description)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM complaints")
        count = cursor.fetchone()[0]

        case_id = f"CC2026{count+1:04d}"
        cursor.execute("""
        INSERT INTO complaints (case_id,name, address, phone, description, category)
        VALUES (?,?, ?, ?, ?, ?)
        """, (case_id,name, address, phone, description, category))

        conn.commit()
        conn.close()

        return redirect(url_for("receipt", case_id=case_id))

    return render_template("complaint_form.html")

@app.route("/receipt/<case_id>")
def receipt(case_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT case_id, name, address, phone, category
        FROM complaints
        WHERE case_id=?
    """, (case_id,))

    complaint = cursor.fetchone()
    conn.close()

    return render_template("receipt.html", complaint=complaint)
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT category, COUNT(*) FROM complaints GROUP BY category")
    data = cursor.fetchall()

    conn.close()

    return render_template("dashboard.html", data=data)


@app.route("/search", methods=["GET", "POST"])
def search():

    if "user" not in session:
        return redirect(url_for("login"))

    results = []

    if request.method == "POST":
        keyword = request.form["keyword"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT case_id, name, address, phone, description, category
        FROM complaints
        WHERE name LIKE ?
        OR address LIKE ?
        OR phone LIKE ?
        OR category LIKE ?
        """, (
        '%'+keyword+'%',
        '%'+keyword+'%',
        '%'+keyword+'%',
        '%'+keyword+'%'
        ))

        results = cursor.fetchall()
        conn.close()

    return render_template("search.html", results=results)

@app.route("/download")
def download():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM complaints")
    data = cursor.fetchall()

    cursor.execute("""
        SELECT category, COUNT(*)
        FROM complaints
        GROUP BY category
    """)
    summary = cursor.fetchall()

    conn.close()

    file_path = "report.pdf"

    pdf = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=20,
        rightMargin=20,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = []

    # =========================
    # TITLE
    # =========================
    elements.append(
        Paragraph(
            "<font size='18'><b>CYBER CRIME COMPLAINT REPORT</b></font>",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 15))

    # =========================
    # DATE
    # =========================
    date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    elements.append(
        Paragraph(f"<b>Generated On:</b> {date}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"<b>Total Complaints:</b> {len(data)}", styles["Normal"])
    )

    elements.append(Spacer(1, 15))

    # =========================
    # SUMMARY
    # =========================
    elements.append(
        Paragraph("<b>Complaint Summary</b>", styles["Heading2"])
    )

    for cat, count in summary:
        elements.append(
            Paragraph(f"{cat} : {count}", styles["Normal"])
        )

    elements.append(Spacer(1, 15))

    # =========================
    # TABLE HEADER
    # =========================
    table_data = [[
        "Case ID",
        "Name",
        "Address",
        "Phone",
        "Description",
        "Category"
    ]]

    # =========================
    # TABLE ROWS
    # =========================
    for row in data:

        table_data.append([

            Paragraph(str(row[1]), styles["BodyText"]),  # Case ID

            Paragraph(str(row[2]), styles["BodyText"]),  # Name

            Paragraph(str(row[3]), styles["BodyText"]),  # Address

            Paragraph(str(row[4]), styles["BodyText"]),  # Phone

            Paragraph(str(row[5]), styles["BodyText"]),  # Description

            Paragraph(str(row[6]), styles["BodyText"])   # Category

        ])

    # =========================
    # TABLE
    # =========================
    table = Table(
        table_data,
        colWidths=[
            70,    # Case ID
            75,    # Name
            145,   # Address (Increased)
            70,    # Phone
            150,   # Description
            70     # Category
        ]
    )

    table.setStyle(TableStyle([

        # Header
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),

        # Body
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),

        # Borders
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BOX', (0,0), (-1,-1), 1, colors.black),

        # Alignment
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),

        # Font
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),

        # Padding
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),

    ]))

    elements.append(table)

    pdf.build(elements)

    return send_file(file_path, as_attachment=True)
@app.route("/officer_home")
def officer_home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("officer_home.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/category/<category>")
def category_view(category):

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM complaints
        WHERE category=?
    """, (category,))

    complaints = cursor.fetchall()
    conn.close()

    return render_template("category.html", complaints=complaints, category=category)
@app.route("/download_receipt/<case_id>")

def download_receipt(case_id):

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()



    cursor.execute("""

    SELECT case_id, name, address, phone, category

    FROM complaints

    WHERE case_id=?

    """, (case_id,))



    data = cursor.fetchone()

    conn.close()



    if not data:

        return "Receipt not found"



    file_path = f"{case_id}_receipt.pdf"

    pdf = SimpleDocTemplate(file_path, pagesize=letter)



    styles = getSampleStyleSheet()

    elements = []



# TITLE

    elements.append(Paragraph("<b><font size='16'>CYBER CRIME COMPLAINT RECEIPT</font></b>", styles["Title"]))

    elements.append(Spacer(1, 20))



# TABLE (BOX STYLE RECEIPT)

    table_data = [

    ["Field", "Details"],

    ["Case ID", data[0]],

    ["Name", data[1]],

    ["Address", data[2]],

    ["Phone", data[3]],

    ["Category", data[4]]

    ]



    table = Table(table_data, colWidths=[150, 350])



    table.setStyle(TableStyle([



    # Header style

    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),

    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),



    # Box border

    ('BOX', (0, 0), (-1, -1), 2, colors.black),

    ('GRID', (0, 0), (-1, -1), 1, colors.black),



    # Alignment

    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),



    # Padding

    ('PADDING', (0, 0), (-1, -1), 10),



    # Body background

    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),

    ]))



    elements.append(table)



    elements.append(Spacer(1, 30))



    pdf.build(elements)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)