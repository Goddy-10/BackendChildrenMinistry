
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import DepartmentMember
from datetime import datetime

#DEPARTMENT MEMBERS ROUTE

department_members_bp = Blueprint("department_members_bp", __name__, url_prefix="/api/department-members")



# GET all members for a department
@department_members_bp.get("/", defaults={"department_id": None})
@department_members_bp.get("/<int:department_id>")
def get_department_members(department_id):
    if department_id:
        members = DepartmentMember.query.filter_by(department_id=department_id).all()
    else:
        members = DepartmentMember.query.all()  # return all if no ID
    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "position": m.position,
            "phone": m.phone,
            "department_id": m.department_id
        } for m in members
    ]), 200
# POST a new department member
@department_members_bp.post("/")
def add_department_member():
    data = request.get_json()
    try:
        member = DepartmentMember(
            name=data["name"],
            position=data.get("position"),
            phone=data.get("phone"),
            department_id=data["department_id"]
        )
        db.session.add(member)
        db.session.commit()
        return jsonify({
            "id": member.id,
            "name": member.name,
            "position": member.position,
            "phone": member.phone,
            "department_id": member.department_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# PATCH (edit) department member
@department_members_bp.patch("/<int:id>")
def update_department_member(id):
    member = DepartmentMember.query.get_or_404(id)
    data = request.get_json()
    try:
        if "name" in data:
            member.name = data["name"]
        if "position" in data:
            member.position = data["position"]
        if "phone" in data:
            member.phone = data["phone"]

        db.session.commit()
        return jsonify({
            "id": member.id,
            "name": member.name,
            "position": member.position,
            "phone": member.phone,
            "department_id": member.department_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# DELETE a department member
@department_members_bp.delete("/<int:id>")
def delete_department_member(id):
    member = DepartmentMember.query.get_or_404(id)
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({"message": "Department member deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400