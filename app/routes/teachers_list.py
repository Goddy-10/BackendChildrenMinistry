# # app/routes/teachers_route.py
# from flask import Blueprint, jsonify
# from app.models import User

# teachers_bp = Blueprint("teachers_bp", __name__, url_prefix="/api/teachers")

# @teachers_bp.get("/")
# def list_teachers():
#     # returns a simple list of users who can be teachers (role 'teacher' or 'admin')
#     users = User.query.filter(User.role.in_(["teacher", "admin"])).all()
#     items = [{"id": u.id, "username": u.username, "name": getattr(u, "name", None), "email": u.email} for u in users]
#     return jsonify({"items": items}), 200