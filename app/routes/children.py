# routes/children_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app.models import Child, Attendance, Offering, SundayClass, User
from app.extensions import db

children_bp = Blueprint("children_bp", __name__, url_prefix="/api/children")

# GET /api/children?search=...&page=1&page_size=20&class=Beginners
@children_bp.route("/", methods=["GET"])
def list_children():
    search = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    class_filter = request.args.get("class")

    q = Child.query
    if search:
        q = q.filter(Child.name.ilike(f"%{search}%"))
    if class_filter:
        # if your Child has a class_id relation, try to map
        q = q.filter(Child.class_id == (SundayClass.query.filter_by(name=class_filter).first().id if SundayClass.query.filter_by(name=class_filter).first() else None))

    total = q.count()
    items = q.order_by(Child.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "items": [c.to_dict() if hasattr(c, "to_dict") else {
            "id": c.id, "name": c.name, "age": c.age, "gender": c.gender,
            "parent_name": c.parent_name, "parent_contact": c.parent_contact,
            "class_id": c.class_id, "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size
    }), 200

# POST /api/children
# Teachers and admin can add children — protect in frontend with role; allow here with token optional but recommended
@children_bp.route("/", methods=["POST"])
@jwt_required(optional=True)
def add_child():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "Name required"}), 400

    child = Child(
        name=name,
        age=data.get("age"),
        gender=data.get("gender"),
        parent_name=data.get("parent_name") or data.get("parent") or None,
        parent_contact=data.get("parent_contact") or data.get("contact") or None,
        class_id=data.get("class_id"),
        added_by_id=get_jwt_identity() if get_jwt_identity() else None
    )
    db.session.add(child)
    db.session.commit()
    return jsonify(child.to_dict() if hasattr(child, "to_dict") else {"id": child.id}), 201

# PUT /api/children/<id>
@children_bp.route("/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_child(id):
    child = Child.query.get_or_404(id)
    data = request.get_json() or {}
    child.name = data.get("name", child.name)
    child.age = data.get("age", child.age)
    child.gender = data.get("gender", child.gender)
    child.parent_name = data.get("parent_name", child.parent_name)
    child.parent_contact = data.get("parent_contact", child.parent_contact)
    child.class_id = data.get("class_id", child.class_id)
    db.session.commit()
    return jsonify(child.to_dict() if hasattr(child, "to_dict") else {"id": child.id}), 200

# DELETE /api/children/<id>
@children_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_child(id):
    child = Child.query.get_or_404(id)
    db.session.delete(child)
    db.session.commit()
    return jsonify({"message": "Child deleted"}), 200

# ----------------------------
# Attendance endpoints
# POST /api/children/<child_id>/attendance  { date: "YYYY-MM-DD", present: true, remarks: "..." }
@children_bp.route("/<int:child_id>/attendance", methods=["POST"])
@jwt_required()
def mark_attendance(child_id):
    child = Child.query.get_or_404(child_id)
    data = request.get_json() or {}
    dt_str = data.get("date")
    if dt_str:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400
    else:
        dt = date.today()

    present = bool(data.get("present", True))
    remarks = data.get("remarks")

    # If an attendance record exists for that child & date, update it
    rec = Attendance.query.filter_by(child_id=child.id, date=dt).first()
    if rec:
        rec.present = present
        rec.remarks = remarks
        rec.recorded_by = get_jwt_identity()
    else:
        rec = Attendance(
            date=dt,
            child_id=child.id,
            present=present,
            class_id=child.class_id,
            recorded_by=get_jwt_identity(),
            remarks=remarks
        )
        db.session.add(rec)
    db.session.commit()
    return jsonify({"id": rec.id, "child_id": rec.child_id, "date": rec.date.isoformat(), "present": rec.present}), 201

# GET /api/children/<child_id>/attendance?start=YYYY-MM-DD&end=YYYY-MM-DD
@children_bp.route("/<int:child_id>/attendance", methods=["GET"])
@jwt_required(optional=True)
def get_child_attendance(child_id):
    child = Child.query.get_or_404(child_id)
    start = request.args.get("start")
    end = request.args.get("end")
    q = Attendance.query.filter_by(child_id=child.id)
    if start:
        try:
            s = datetime.strptime(start, "%Y-%m-%d").date()
            q = q.filter(Attendance.date >= s)
        except:
            pass
    if end:
        try:
            e = datetime.strptime(end, "%Y-%m-%d").date()
            q = q.filter(Attendance.date <= e)
        except:
            pass
    recs = q.order_by(Attendance.date.desc()).all()
    out = []
    for r in recs:
        out.append({
            "id": r.id,
            "date": r.date.isoformat(),
            "present": bool(r.present),
            "remarks": r.remarks,
            "recorded_by": r.recorded_by
        })
    return jsonify(out), 200

# ----------------------------
# Offerings endpoints (per class)
# POST /api/children/offerings  { date, class_id, amount, note }
@children_bp.route("/offerings", methods=["POST"])
@jwt_required()
def add_offering():
    data = request.get_json() or {}
    dt_str = data.get("date")
    if dt_str:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
        except:
            return jsonify({"error": "Invalid date"}), 400
    else:
        dt = date.today()

    class_id = data.get("class_id")
    amount = data.get("amount")
    if amount is None:
        return jsonify({"error": "amount required"}), 400

    offering = Offering(
        date=dt,
        class_id=class_id,
        amount=amount,
        recorded_by=get_jwt_identity(),
        note=data.get("note")
    )
    db.session.add(offering)
    db.session.commit()
    return jsonify({"id": offering.id, "date": offering.date.isoformat(), "amount": str(offering.amount)}), 201

# GET /api/children/offerings?start=YYYY-MM-DD&end=YYYY-MM-DD&class_id=...
@children_bp.route("/offerings", methods=["GET"])
@jwt_required(optional=True)
def list_offerings():
    start = request.args.get("start")
    end = request.args.get("end")
    class_id = request.args.get("class_id")
    q = Offering.query
    if start:
        try:
            s = datetime.strptime(start, "%Y-%m-%d").date()
            q = q.filter(Offering.date >= s)
        except:
            pass
    if end:
        try:
            e = datetime.strptime(end, "%Y-%m-%d").date()
            q = q.filter(Offering.date <= e)
        except:
            pass
    if class_id:
        q = q.filter(Offering.class_id == class_id)
    items = q.order_by(Offering.date.desc()).all()
    out = [{
        "id": o.id,
        "date": o.date.isoformat(),
        "class_id": o.class_id,
        "amount": float(o.amount),
        "note": o.note,
        "recorded_by": o.recorded_by
    } for o in items]
    return jsonify(out), 200