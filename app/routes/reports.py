# routes/reports_routes.py
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.models import Attendance, Offering, Report, User
from app.extensions import db
import io

reports_bp = Blueprint("reports_bp", __name__, url_prefix="/api/reports")

# Helper: parse dates
def parse_date(s, default=None):
    if not s:
        return default
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return default

# GET KPI: /api/reports/kpi?date=YYYY-MM-DD&class_id=...
@reports_bp.route("/kpi", methods=["GET"])
@jwt_required(optional=True)
def kpi():
    d = parse_date(request.args.get("date"), date.today())
    class_id = request.args.get("class_id")
    # today's attendance count
    q = Attendance.query.filter(Attendance.date == d, Attendance.present == True)
    if class_id:
        q = q.filter(Attendance.class_id == class_id)
    todays_attendance = q.count()
    # today's offering total
    oq = Offering.query.filter(Offering.date == d)
    if class_id:
        oq = oq.filter(Offering.class_id == class_id)
    todays_offering = oq.with_entities(func.coalesce(func.sum(Offering.amount), 0)).scalar() or 0

    # monthly totals (for the month of date d)
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

# Weekly reports: store weekly teacher-submitted reports in a Report model (you have a Report model earlier)
# GET /api/reports/weekly?class_id=&start=YYYY-MM-DD&end=YYYY-MM-DD
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
    out = [r.to_dict() if hasattr(r, "to_dict") else {
        "id": r.id, "date": r.date, "attendance": r.attendance, "offering": r.offering, "notes": r.notes
    } for r in items]
    return jsonify(out), 200

# POST /api/reports (teacher/admin)
@reports_bp.route("/", methods=["POST"])
@jwt_required()
def add_report():
    data = request.get_json() or {}
    dt = parse_date(data.get("date"), date.today())
    report = Report(
        date=dt,
        attendance=data.get("attendance"),
        offering=data.get("offering"),
        notes=data.get("notes"),
        class_id=data.get("class_id"),
        created_by=get_jwt_identity()
    )
    db.session.add(report)
    db.session.commit()
    return jsonify(report.to_dict() if hasattr(report, "to_dict") else {"id": report.id}), 201

# PUT /api/reports/<id>
@reports_bp.route("/<int:id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_report(id):
    report = Report.query.get_or_404(id)
    data = request.get_json() or {}
    report.attendance = data.get("attendance", report.attendance)
    report.offering = data.get("offering", report.offering)
    report.notes = data.get("notes", report.notes)
    db.session.commit()
    return jsonify(report.to_dict() if hasattr(report, "to_dict") else {"id": report.id}), 200

# DELETE /api/reports/<id>
@reports_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_report(id):
    report = Report.query.get_or_404(id)
    db.session.delete(report)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

# EXPORT endpoints (placeholders) — you said docx/pdf required. Implementations depend on python-docx or pdf libs.
# For now return 501 if not implemented.
@reports_bp.route("/export/docx", methods=["GET"])
@jwt_required()
def export_docx():
    # implement python-docx creation here (return file)
    return jsonify({"error": "Not implemented, add server-side python-docx generation"}), 501

@reports_bp.route("/export/pdf", methods=["GET"])
@jwt_required()
def export_pdf():
    # implement server side PDF generation (pdf-lib or reportlab)
    return jsonify({"error": "Not implemented, add server-side PDF generation"}), 501