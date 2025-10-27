from flask import Blueprint, request, jsonify,send_file
from datetime import datetime
from app.models import  FinanceEntry, Project, Mission, Department, NewMember
from app.extensions import db
from sqlalchemy import and_
from io import BytesIO
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


adults_bp = Blueprint("adults_bp", __name__, url_prefix="/adults")





#--------Helper function for filtering FINANCE logic----------#

def filter_finance_entries(query, start_date=None, end_date=None, service_type=None):
    filters = []
    if start_date:
        filters.append(FinanceEntry.date >= start_date)
    if end_date:
        filters.append(FinanceEntry.date <= end_date)
    if service_type:
        filters.append(FinanceEntry.service_type.ilike(f"%{service_type}%"))
    if filters:
        query = query.filter(and_(*filters))
    return query



#------------FINANCE PDF------------#

@adults_bp.route("/finance/export/pdf", methods=["GET"])
def export_finance_pdf():
    # Parse query params: ?service_type=Sunday&start=2025-01-01&end=2025-06-30
    service_type = request.args.get("service_type")
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else None
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else None

    query = FinanceEntry.query.order_by(FinanceEntry.date.desc())
    query = filter_finance_entries(query, start_date, end_date, service_type)
    entries = query.all()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Finance Report")
    y -= 20
    p.setFont("Helvetica", 10)

    filter_info = []
    if service_type:
        filter_info.append(f"Service: {service_type}")
    if start_date:
        filter_info.append(f"From: {start_date}")
    if end_date:
        filter_info.append(f"To: {end_date}")
    if filter_info:
        p.drawString(50, y, " | ".join(filter_info))
        y -= 20

    for e in entries:
        line = f"{e.date} | {e.service_type or ''} | {e.source or ''} | Ksh {e.amount}"
        p.drawString(50, y, line)
        y -= 18
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="finance_report.pdf", mimetype="application/pdf")




#------------WORD--------#

@adults_bp.route("/finance/export/docx", methods=["GET"])
def export_finance_docx():
    service_type = request.args.get("service_type")
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else None
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else None

    query = FinanceEntry.query.order_by(FinanceEntry.date.desc())
    query = filter_finance_entries(query, start_date, end_date, service_type)
    entries = query.all()

    doc = Document()
    title = "Finance Report"
    if service_type:
        title += f" - {service_type.title()}"
    doc.add_heading(title, level=1)

    if start_date or end_date:
        range_text = f"Period: {start_date or '...'} to {end_date or '...'}"
        doc.add_paragraph(range_text)

    table = doc.add_table(rows=1, cols=4)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Date"
    hdr_cells[1].text = "Service Type"
    hdr_cells[2].text = "Source"
    hdr_cells[3].text = "Amount (Ksh)"

    for e in entries:
        row_cells = table.add_row().cells
        row_cells[0].text = e.date.strftime("%Y-%m-%d")
        row_cells[1].text = e.service_type or ""
        row_cells[2].text = e.source or ""
        row_cells[3].text = str(e.amount)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="finance_report.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")



# -------------------- FINANCE ENTRIES --------------------
@adults_bp.route("/finance", methods=["GET"])

def get_finances():
    entries = FinanceEntry.query.all()
    return jsonify([e.to_dict() for e in entries]), 200

@adults_bp.route("/finance/<int:id>", methods=["GET"])
def get_finance(id):
    entry = FinanceEntry.query.get_or_404(id)
    return jsonify(entry.to_dict()), 200

@adults_bp.route("/finance", methods=["POST"])
def add_finance():
    data = request.get_json()
    entry = FinanceEntry(
        date=datetime.strptime(data["date"], "%Y-%m-%d"),
        amount=data["amount"],
        service_type=data.get("service_type"),
        source=data.get("source"),
        created_by=data.get("created_by")
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201




@adults_bp.route("/finance/<int:id>", methods=["PATCH"])
def update_finance(id):
    entry = FinanceEntry.query.get_or_404(id)
    data = request.get_json()

    if "date" in data and data["date"]:
        entry.date = datetime.strptime(data["date"], "%Y-%m-%d")  # same style as POST

    if "amount" in data:
        entry.amount = data["amount"]

    if "service_type" in data:
        entry.service_type = data["service_type"]

    if "source" in data:
        entry.source = data["source"]

    db.session.commit()
    return jsonify(entry.to_dict()), 200


@adults_bp.route("/finance/<int:id>", methods=["DELETE"])
def delete_finance(id):
    entry = FinanceEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Finance entry deleted"}), 200


# -------------------- PROJECTS --------------------
@adults_bp.route("/projects", methods=["GET"])
def get_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects]), 200

@adults_bp.route("/projects", methods=["POST"])
def add_project():
    data = request.get_json()

    # convert date strings to date objects if provided
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    project = Project(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "planned"),
        start_date=start_date,
        end_date=end_date,
        created_by=data.get("created_by")
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201

@adults_bp.route("/projects/<int:id>", methods=["PATCH"])
def update_project(id):
    project = Project.query.get_or_404(id)
    data = request.get_json()

    for field in ["title", "description", "status", "start_date", "end_date"]:
        if field in data:
            value = data[field]
            if field in ["start_date", "end_date"] and value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            setattr(project, field, value)

    db.session.commit()
    return jsonify(project.to_dict()), 200

@adults_bp.route("/projects/<int:id>", methods=["DELETE"])
def delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted"}), 200


# -------------------- MISSIONS --------------------
@adults_bp.route("/missions", methods=["GET"])
def get_missions():
    missions = Mission.query.all()
    return jsonify([m.to_dict() for m in missions]), 200

@adults_bp.route("/missions", methods=["POST"])
def add_mission():
    data = request.get_json()
    
    # convert date strings to date objects if provided
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    mission = Mission(
        title=data["title"],
        description=data.get("description"),
        start_date=start_date,
        end_date=end_date,
        partners=data.get("partners"),
        support=data.get("support"),
        contact=data.get("contact"),
    )
    db.session.add(mission)
    db.session.commit()
    return jsonify(mission.to_dict()), 201

@adults_bp.route("/missions/<int:id>", methods=["PATCH"])
def update_mission(id):
    mission = Mission.query.get_or_404(id)
    data = request.get_json()

    for field in ["title", "description", "start_date", "end_date", "partners", "support", "contact"]:
        if field in data:
            value = data[field]
            if field in ["start_date", "end_date"] and value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            setattr(mission, field, value)

    db.session.commit()
    return jsonify(mission.to_dict()), 200

@adults_bp.route("/missions/<int:id>", methods=["DELETE"])
def delete_mission(id):
    mission = Mission.query.get_or_404(id)
    db.session.delete(mission)
    db.session.commit()
    return jsonify({"message": "Mission deleted"}), 200


# -------------------- DEPARTMENTS --------------------
@adults_bp.route("/departments", methods=["GET"])
def get_departments():
    depts = Department.query.all()
    return jsonify([d.to_dict() for d in depts]), 200

@adults_bp.route("/departments", methods=["POST"])
def add_department():
    data = request.get_json()
    dept = Department(
        name=data["name"],
        description=data.get("description"),
        contact_person=data.get("contact_person"),
        contact_phone=data.get("contact_phone"),
        contact_email=data.get("contact_email"),
    )
    db.session.add(dept)
    db.session.commit()
    return jsonify(dept.to_dict()), 201

@adults_bp.route("/departments/<int:id>", methods=["PATCH"])
def update_department(id):
    dept = Department.query.get_or_404(id)
    data = request.get_json()
    for field in ["name", "description", "contact_person", "contact_phone", "contact_email"]:
        if field in data:
            setattr(dept, field, data[field])
    db.session.commit()
    return jsonify(dept.to_dict()), 200

@adults_bp.route("/departments/<int:id>", methods=["DELETE"])
def delete_department(id):
    dept = Department.query.get_or_404(id)
    db.session.delete(dept)
    db.session.commit()
    return jsonify({"message": "Department deleted"}), 200


# -------------------- NEW MEMBERS --------------------
@adults_bp.route("/new-members", methods=["GET"])
def get_new_members():
    members = NewMember.query.all()
    return jsonify([m.to_dict() for m in members]), 200

@adults_bp.route("/new-members", methods=["POST"])
def add_new_member():
    data = request.get_json()
    member = NewMember(
        name=data["name"],
        phone=data.get("phone"),
        email=data.get("email"),
        join_date=datetime.strptime(data["join_date"], "%Y-%m-%d") if data.get("join_date") else datetime.utcnow(),
        notes=data.get("notes"),
        sunday_class_id=data.get("sunday_class_id"),
        department_id=data.get("department_id"),
    )
    db.session.add(member)
    db.session.commit()
    return jsonify(member.to_dict()), 201

@adults_bp.route("/new-members/<int:id>", methods=["PATCH"])
def update_new_member(id):
    member = NewMember.query.get_or_404(id)
    data = request.get_json()
    for field in ["name", "phone", "email", "notes", "sunday_class_id", "department_id"]:
        if field in data:
            setattr(member, field, data[field])

    # Handle join_date separately
    if "join_date" in data:
        member.join_date = datetime.strptime(data["join_date"], "%Y-%m-%d") if data["join_date"] else None

    db.session.commit()
    return jsonify(member.to_dict()), 200

@adults_bp.route("/new-members/<int:id>", methods=["DELETE"])
def delete_new_member(id):
    member = NewMember.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "New member deleted"}), 200