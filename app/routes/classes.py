# app/routes/classes_routes.py
from flask import Blueprint, request, jsonify
from app.models import  SundayClass, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db

classes_bp = Blueprint("classes_bp", __name__, url_prefix="/api/classes")

@classes_bp.get("")
def list_classes():
    classes = SundayClass.query.order_by(SundayClass.name).all()
    data=[c.to_dict() for c in classes]
    print("Returning classes:",data)
    return jsonify({"items": [c.to_dict() for c in classes]}), 200

@classes_bp.post("")
@jwt_required()
def create_class():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin required"}), 403

    data = request.get_json() or {}
    name = data.get("name")
    min_age = data.get("min_age")
    max_age = data.get("max_age")
    if not name:
        return jsonify({"error": "name required"}), 400

    if SundayClass.query.filter_by(name=name).first():
        return jsonify({"error": "Class with that name already exists"}), 400

    c = SundayClass(name=name, min_age=min_age, max_age=max_age)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@classes_bp.put("/<int:id>")
@jwt_required()
def update_class(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin required"}), 403

    c = SundayClass.query.get_or_404(id)
    data = request.get_json() or {}
    c.name = data.get("name", c.name)
    c.min_age = data.get("min_age", c.min_age)
    c.max_age = data.get("max_age", c.max_age)
    db.session.commit()
    return jsonify(c.to_dict()), 200

@classes_bp.delete("/<int:id>")
@jwt_required()
def delete_class(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin required"}), 403
    c = SundayClass.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200