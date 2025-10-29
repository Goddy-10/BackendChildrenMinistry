# app/routes/timetable_routes.py
from flask import Blueprint, request, jsonify
from app.models import  TimetableEntry, SundayClass, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import db

timetable_bp = Blueprint("timetable_bp", __name__, url_prefix="/api/timetable")

@timetable_bp.get("")
def list_timetable():
    search = request.args.get("search", "")
    query = TimetableEntry.query
    if search:
        query = query.filter(TimetableEntry.date.like(f"%{search}%"))
    items = [e.to_dict() for e in query.order_by(TimetableEntry.date.desc()).all()]
    return jsonify({"items": items}), 200

@timetable_bp.post("")
@jwt_required()
def add_timetable():
    # admin only
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin required"}), 403

    data = request.get_json() or {}
    date_str = data.get("date")
    class_id = data.get("class_id")
    teacher_id = data.get("teacher_id")

    if not date_str or not class_id or not teacher_id:
        return jsonify({"error": "date, class_id and teacher_id are required"}), 400

    # validate
    cls = SundayClass.query.get(class_id)
    teacher = User.query.get(teacher_id)
    if not cls:
        return jsonify({"error": "Class not found"}), 400
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 400

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    entry = TimetableEntry(date=dt, class_id=class_id, teacher_id=teacher_id)
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201

@timetable_bp.put("/<int:id>")
@jwt_required()
def update_timetable(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin required"}), 403

    entry = TimetableEntry.query.get_or_404(id)
    data = request.get_json() or {}

    date_str = data.get("date")
    class_id = data.get("class_id")
    teacher_id = data.get("teacher_id")

    if date_str:
        try:
            entry.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"error": "date must be YYYY-MM-DD"}), 400
    if class_id:
        if not SundayClass.query.get(class_id):
            return jsonify({"error": "Class not found"}), 400
        entry.class_id = class_id
    if teacher_id:
        if not User.query.get(teacher_id):
            return jsonify({"error": "Teacher not found"}), 400
        entry.teacher_id = teacher_id

    db.session.commit()
    return jsonify(entry.to_dict()), 200

@timetable_bp.delete("/<int:id>")
@jwt_required()
def delete_timetable(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Admin required"}), 403
    entry = TimetableEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200