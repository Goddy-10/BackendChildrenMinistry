from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Member
from datetime import datetime

members_bp = Blueprint("members_bp", __name__ ,url_prefix="/api/members")

@members_bp.get("")
def get_members():
    print("GET /members reached")
    members = Member.query.all()
    return jsonify([m.to_dict() for m in members]), 200



@members_bp.post("")
def add_member():
    data = request.get_json()
    try:
        member = Member(
            full_name=data.get("name"),
            phone=data.get("phone"),
            residence=data.get("residence"),
            
            department_id=data.get("department_id"),
        )
        db.session.add(member)
        db.session.commit()
        return jsonify({
            
            "member": {
                "id": member.id,
                "name": member.full_name,        # include 'name' for frontend
                "residence": member.residence,     # include 'position'
                "phone": member.phone,
                "department_id": member.department_id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    

@members_bp.patch("/<int:id>")
def update_member(id):
    member = Member.query.get_or_404(id)
    data = request.get_json()

    try:
        if "name" in data:
            member.full_name = data["name"]
        if "phone" in data:
            member.phone = data["phone"]
        if "position" in data:
            member.position = data["position"]
        if "gender" in data:
            member.gender = data["gender"]
        if "department_id" in data:
            member.department_id = data["department_id"]

        db.session.commit()
        return jsonify({"message": "Member updated successfully", "member": member.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@members_bp.delete("/<int:id>")
def delete_member(id):
    member = Member.query.get_or_404(id)
    try:
        db.session.delete(member)
        db.session.commit()
        return jsonify({"message": "Member deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400