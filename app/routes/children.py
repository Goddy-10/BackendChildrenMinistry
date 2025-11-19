


# routes/children_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from app.models import Child, Attendance, Offering, SundayClass
from app.extensions import db

children_bp = Blueprint("children_bp", __name__, url_prefix="/api/children")

# ------------------------
# Utility Functions
# ------------------------
def get_sundays_between(start_date, end_date):
    """Return a list of all Sundays between start_date and end_date (inclusive)."""
    sundays = []
    d = start_date
    while d <= end_date:
        if d.weekday() == 6:  # Sunday
            sundays.append(d)
        d += timedelta(days=1)
    return sundays

# ------------------------
# CHILD CRUD
# ------------------------

# GET all children (optionally by class or search)
@children_bp.route("/", methods=["GET"])
def list_children():
    search = request.args.get("search", "").strip()
    class_filter = request.args.get("class")

    q = Child.query
    if search:
        q = q.filter(Child.name.ilike(f"%{search}%"))

    children = q.order_by(Child.id.desc()).all()

    # Fetch Sunday classes with age ranges
    sunday_classes = SundayClass.query.all()

    result = []
    for c in children:
        # Determine the child's class dynamically based on age
        child_class = None
        for sc in sunday_classes:
            if sc.min_age is not None and sc.max_age is not None:
                if c.age is not None and sc.min_age <= c.age <= sc.max_age:
                    child_class = sc
                    break

        # If a class filter is applied, skip children not in that class
        if class_filter and (not child_class or child_class.name != class_filter):
            continue

        result.append({
            "id": c.id,
            "name": c.name,
            "age": c.age,
            "gender": c.gender,
            "parent_name": c.parent_name,
            "parent_contact": c.parent_contact,
            "class_id": child_class.id if child_class else None,
            "class_name": child_class.name if child_class else None
        })
    return jsonify(result), 200


# POST add a new child
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
        parent_name=data.get("parent_name") or data.get("parent"),
        parent_contact=data.get("parent_contact") or data.get("contact"),
        class_id=data.get("class_id"),
        added_by_id=get_jwt_identity()
    )
    # --- AUTOMATIC CLASS ASSIGNMENT ---
    if child.age is not None:
        sunday_classes = SundayClass.query.all()
    assigned_class = None
    for sc in sunday_classes:
        if sc.min_age is not None and sc.max_age is not None:
            if sc.min_age <= child.age <= sc.max_age:
                assigned_class = sc
                break
    if assigned_class:
        child.class_id = assigned_class.id

    # ----------------------------------
    db.session.add(child)
    db.session.commit()
    return jsonify({"id": child.id}), 201

# PUT update child
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
    return jsonify({"id": child.id}), 200

# DELETE child
@children_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_child(id):
    child = Child.query.get_or_404(id)
    db.session.delete(child)
    db.session.commit()
    return jsonify({"message": "Child deleted"}), 200

# ------------------------
# ATTENDANCE
# ------------------------

# POST mark attendance for a child
@children_bp.route("/<int:child_id>/attendance", methods=["POST"])
@jwt_required()
def mark_attendance(child_id):
    child = Child.query.get_or_404(child_id)
    data = request.get_json() or {}
    dt_str = data.get("date")
    if dt_str:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400
    else:
        dt = date.today()

    present = bool(data.get("present", True))
    remarks = data.get("remarks")

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

# GET attendance matrix for a child (last 5 months)
@children_bp.route("/<int:child_id>/attendance_matrix", methods=["GET"])
@jwt_required(optional=True)
def attendance_matrix(child_id):
    child = Child.query.get_or_404(child_id)
    today = date.today()
    start_date = today - timedelta(days=150)  # approx last 5 months

    sundays = get_sundays_between(start_date, today)
    attendance_records = Attendance.query.filter(
        Attendance.child_id == child_id,
        Attendance.date.in_(sundays)
    ).all()

    att_map = {r.date: "X" if r.present else "0" for r in attendance_records}

    matrix = []
    for d in sundays:
        matrix.append({
            "date": d.isoformat(),
            "status": att_map.get(d, "0")  # default absent
        })

    return jsonify({
        "child_id": child_id,
        "child_name": child.name,
        "class_id": child.class_id,
        "attendance": matrix
    }), 200

# ------------------------
# OFFERINGS (per class)
# ------------------------

# POST add offering
@children_bp.route("/offerings", methods=["POST"])
@jwt_required()
def add_offering():
    data = request.get_json() or {}
    dt_str = data.get("date")
    dt = date.today()
    if dt_str:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    class_id = data.get("class_id")
    amount = data.get("amount")
    if amount is None:
        return jsonify({"error": "Amount required"}), 400

    offering = Offering(
        date=dt,
        class_id=class_id,
        amount=amount,
        recorded_by=get_jwt_identity(),
        note=data.get("note")
    )
    db.session.add(offering)
    db.session.commit()
    return jsonify({"id": offering.id, "date": offering.date.isoformat(), "amount": float(offering.amount)}), 201

# GET offerings
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