from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models import  FinanceEntry, Project, Mission, Department, NewMember
from app.extensions import db

adults_bp = Blueprint("adults_bp", __name__, url_prefix="/adults")

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
    for field in ["date", "amount", "service_type", "source"]:
        if field in data:
            setattr(entry, field, data[field])
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
    project = Project(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "planned"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
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
            setattr(project, field, data[field])
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
    mission = Mission(
        title=data["title"],
        description=data.get("description"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
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
            setattr(mission, field, data[field])
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
    for field in ["name", "phone", "email", "join_date", "notes", "sunday_class_id", "department_id"]:
        if field in data:
            setattr(member, field, data[field])
    db.session.commit()
    return jsonify(member.to_dict()), 200

@adults_bp.route("/new-members/<int:id>", methods=["DELETE"])
def delete_new_member(id):
    member = NewMember.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "New member deleted"}), 200