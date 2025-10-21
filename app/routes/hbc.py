from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import HomeChurch
from datetime import datetime

homechurch_bp = Blueprint("homechurches", __name__)

# ✅ CREATE Home Church
@homechurch_bp.route("/", methods=["POST"])
def create_homechurch():
    data = request.get_json()
    name = data.get("name")
    contact = data.get("contact")
    location = data.get("location")

    if not name or not contact:
        return jsonify({"error": "Name and contact are required"}), 400

    new_homechurch = HomeChurch(
        name=name,
        contact=contact,
        location=location
    )
    db.session.add(new_homechurch)
    db.session.commit()
    return jsonify({"message": "Home church created successfully", "homechurch": new_homechurch.to_dict()}), 201


# ✅ READ all Home Churches
@homechurch_bp.route("/", methods=["GET"])
def get_homechurches():
    churches = HomeChurch.query.order_by(HomeChurch.id.desc()).all()
    return jsonify([church.to_dict() for church in churches])


# ✅ READ one Home Church by ID
@homechurch_bp.route("/<int:id>", methods=["GET"])
def get_homechurch(id):
    church = HomeChurch.query.get_or_404(id)
    return jsonify(church.to_dict())


# ✅ UPDATE Home Church
@homechurch_bp.route("/<int:id>", methods=["PATCH", "PUT"])
def update_homechurch(id):
    church = HomeChurch.query.get_or_404(id)
    data = request.get_json()

    church.name = data.get("name", church.name)
    church.contact = data.get("contact", church.contact)
    church.location = data.get("location", church.location)

    db.session.commit()
    return jsonify({"message": "Home church updated successfully", "homechurch": church.to_dict()}), 200


# ✅ DELETE one Home Church
@homechurch_bp.route("/<int:id>", methods=["DELETE"])
def delete_homechurch(id):
    church = HomeChurch.query.get_or_404(id)
    db.session.delete(church)
    db.session.commit()
    return jsonify({"message": "Home church deleted successfully"}), 200


# ✅ CLEAR all Home Churches (admin use)
@homechurch_bp.route("/clear", methods=["DELETE"])
def clear_homechurches():
    num_deleted = db.session.query(HomeChurch).delete()
    db.session.commit()
    return jsonify({"message": f"All ({num_deleted}) home churches cleared"}), 200