



# routes/reports.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.models import Attendance, Offering, Report
from app.extensions import db

reports_bp = Blueprint("reports_bp", __name__, url_prefix="/api/reports")

def parse_date(s, default=None):
    if not s:
        return default
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return default

# --- KPI endpoint ---
@reports_bp.route("/kpi", methods=["GET"])
@jwt_required(optional=True)
def kpi():
    d = parse_date(request.args.get("date"), date.today())
    class_id = request.args.get("class_id")

    q = Attendance.query.filter(Attendance.date == d, Attendance.present == True)
    if class_id:
        q = q.filter(Attendance.class_id == class_id)
    todays_attendance = q.count()

    oq = Offering.query.filter(Offering.date == d)
    if class_id:
        oq = oq.filter(Offering.class_id == class_id)
    todays_offering = oq.with_entities(func.coalesce(func.sum(Offering.amount), 0)).scalar() or 0

    first_of_month = d.replace(day=1)
    last_of_month = (first_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    mon_att_q = Attendance.query.filter(Attendance.date >= first_of_month, Attendance.date <= last_of_month, Attendance.present == True)
    mon_off_q = Offering.query.filter(Offering.date >= first_of_month, Offering.date <= last_of_month)
    if class_id:
        mon_att_q = mon_att_q.filter(Attendance.class_id == class_id)
        mon_off_q = mon_off_q.filter(Offering.class_id == class_id)
    month_attendance = mon_att_q.count()
    month_offering = mon_off_q.with_entities(func.coalesce(func.sum(Offering.amount), 0)).scalar() or 0

    return jsonify({
        "date": d.isoformat(),
        "todays_attendance": todays_attendance,
        "todays_offering": float(todays_offering),
        "month_attendance": month_attendance,
        "month_offering": float(month_offering)
    }), 200

# --- Weekly reports ---
@reports_bp.route("/weekly", methods=["GET"])
@jwt_required(optional=True)
def weekly_reports():
    start = parse_date(request.args.get("start"))
    end = parse_date(request.args.get("end"))
    class_id = request.args.get("class_id")

    q = Report.query
    if start:
        q = q.filter(Report.date >= start)
    if end:
        q = q.filter(Report.date <= end)
    if class_id:
        q = q.filter(Report.class_id == class_id)

    items = q.order_by(Report.date.desc()).all()
    out = [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "class_id": r.class_id,
            "topic": r.topic or "",
            "bible_reference": r.bible_reference or "",
            "resources": r.resources or "",
            "remarks": r.remarks or "",
        } for r in items
    ]
    return jsonify(out), 200

# --- Add report ---
@reports_bp.route("/", methods=["POST"])
@jwt_required()
def add_report():
    data = request.get_json() or {}
    dt = parse_date(data.get("date"), date.today())
    report = Report(
        date=dt,
        class_id=data.get("class_id"),
        topic=data.get("topic"),
        bible_reference=data.get("bible_reference"),
        resources=data.get("resources"),
        remarks=data.get("remarks"),
        teacher_id=get_jwt_identity()
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({
        "id": report.id,
        "date": report.date.isoformat(),
        "class_id": report.class_id,
        "topic": report.topic or "",
        "bible_reference": report.bible_reference or "",
        "resources": report.resources or "",
        "remarks": report.remarks or "",
    }), 201

# --- Update report ---
@reports_bp.route("/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_report(id):
    report = Report.query.get_or_404(id)
    data = request.get_json() or {}

    report.topic = data.get("topic", report.topic)
    report.bible_reference = data.get("bible_reference", report.bible_reference)
    report.resources = data.get("resources", report.resources)
    report.remarks = data.get("remarks", report.remarks)
    db.session.commit()

    return jsonify({
        "id": report.id,
        "date": report.date.isoformat(),
        "class_id": report.class_id,
        "topic": report.topic or "",
        "bible_reference": report.bible_reference or "",
        "resources": report.resources or "",
        "remarks": report.remarks or "",
    }), 200

# --- Delete report ---
@reports_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_report(id):
    report = Report.query.get_or_404(id)
    db.session.delete(report)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200