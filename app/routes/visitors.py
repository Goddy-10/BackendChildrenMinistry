

from flask import Blueprint, request, jsonify
from app.models import Visitor, User
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

visitors_bp = Blueprint("visitors_bp", __name__, url_prefix="/api/visitors")

# -------------------- GET ALL VISITORS --------------------
@visitors_bp.get("")
@jwt_required(optional=True)
def get_visitors():
    visitors = Visitor.query.order_by(Visitor.id.desc()).all()
    return jsonify([v.to_dict() for v in visitors])

# -------------------- ADD NEW VISITOR --------------------
@visitors_bp.post("")
# @jwt_required()
def add_visitor():
    data = request.get_json()
    full_name = data.get("name")  
    phone = data.get("phone")
    email = data.get("email")
    residence = data.get("residence")
    prayer_request = data.get("prayer_request")

    if not full_name:
        return jsonify({"error": "Full name is required"}), 400

    visitor = Visitor(
        full_name=full_name,
        phone=phone,
        email=email,
        residence=residence,
        prayer_request=prayer_request,
        follow_up_status="pending",
        date_of_visit=datetime.utcnow()
    )

    db.session.add(visitor)
    db.session.commit()

    return jsonify(visitor.to_dict()), 201
# -------------------- UPDATE VISITOR --------------------
@visitors_bp.patch("/<int:id>")
@jwt_required()
def update_visitor(id):
    visitor = Visitor.query.get_or_404(id)
    data = request.get_json()

    # allow updates for follow-up status too
    for field in ["full_name", "phone", "email", "residence", "prayer_request", "follow_up_status"]:
        if field in data:
            setattr(visitor, field, data[field])

    db.session.commit()
    return jsonify(visitor.to_dict()), 200

# -------------------- DELETE SINGLE VISITOR --------------------
@visitors_bp.delete("/<int:id>")
@jwt_required()
def delete_visitor(id):
    visitor = Visitor.query.get_or_404(id)
    db.session.delete(visitor)
    db.session.commit()
    return jsonify({"message": "Visitor deleted successfully"}), 200

# -------------------- CLEAR FOLLOWED-UP VISITORS --------------------
@visitors_bp.delete("/clear")
@jwt_required()
def clear_followed_up_visitors():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        # only delete visitors with follow_up_status != pending
        count = Visitor.query.filter(Visitor.follow_up_status != "pending").delete()
        db.session.commit()
        return jsonify({"message": f"Cleared {count} followed-up visitors successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400