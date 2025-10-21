from flask import Blueprint, request, jsonify
from app.models import Visitor
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity

visitors_bp = Blueprint("visitors_bp", __name__, url_prefix="/api/visitors")


# ✅ List all visitors
@visitors_bp.get("/")
@jwt_required(optional=True)  # public form might not require auth
def get_visitors():
    visitors = Visitor.query.order_by(Visitor.id.desc()).all()
    return jsonify([v.to_dict() for v in visitors])


# ✅ Add new visitor (from QR code form)
@visitors_bp.post("/")
def add_visitor():
    data = request.get_json()

    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    notes = data.get("notes")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    visitor = Visitor(
        name=name,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
    )

    db.session.add(visitor)
    db.session.commit()

    return jsonify(visitor.to_dict()), 201


# ✅ Update visitor info
@visitors_bp.patch("/<int:id>")
@jwt_required()
def update_visitor(id):
    visitor = Visitor.query.get_or_404(id)
    data = request.get_json()

    if "name" in data:
        visitor.name = data["name"]
    if "phone" in data:
        visitor.phone = data["phone"]
    if "email" in data:
        visitor.email = data["email"]
    if "address" in data:
        visitor.address = data["address"]
    if "notes" in data:
        visitor.notes = data["notes"]

    db.session.commit()
    return jsonify(visitor.to_dict()), 200


# ✅ Delete single visitor
@visitors_bp.delete("/<int:id>")
@jwt_required()
def delete_visitor(id):
    visitor = Visitor.query.get_or_404(id)
    db.session.delete(visitor)
    db.session.commit()
    return jsonify({"message": "Visitor deleted successfully"}), 200


# 🚨 CLEAR ALL VISITORS — admin-only route
@visitors_bp.delete("/clear")
@jwt_required()
def clear_visitors():
    user_id = get_jwt_identity()
    from models import User
    user = User.query.get(user_id)

    # Only admin can perform this action
    if not user or user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        count = Visitor.query.delete()
        db.session.commit()
        return jsonify({"message": f"Cleared {count} visitors successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400