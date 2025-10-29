
# app/routes/teacher.py
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
import cloudinary.uploader

teachers_bp = Blueprint("teachers", __name__, url_prefix="/api/teachers")

# ✅ Get all teachers (admin only)
@teachers_bp.route("", methods=["GET"])
@jwt_required()
def get_teachers():
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    teachers = User.query.filter_by(role="teacher").all()
    return jsonify([
        {
            "id": t.id,
            "name": t.name,
            "username": t.username,
            "phone": t.phone,
            "bio": t.bio,
            "profile_pic": t.profile_pic,
            "must_change_password": t.must_change_password,
        } for t in teachers
    ]), 200



#✅ Public list of teachers (any logged-in user can view)
# @teachers_bp.route("/public", methods=["GET"])
# @jwt_required()
# def get_teachers_public():
#     teachers = User.query.filter_by(role="teacher").all()
#     return jsonify({
#         "items": [
#             {
#                 "id": t.id,
#                 "name": t.name,
#                 "username": t.username,
#                 "phone": t.phone,
#                 "bio": t.bio,
#                 "profile_pic": t.profile_pic,
#             } for t in teachers
#         ]
#     }), 200



# ✅ Get single teacher (admin only)
@teachers_bp.route("/<int:teacher_id>", methods=["GET"])
@jwt_required()
def get_teacher(teacher_id):
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    teacher = User.query.filter_by(id=teacher_id, role="teacher").first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    return jsonify({
        "id": teacher.id,
        "name": teacher.name,
        "username": teacher.username,
        "phone": teacher.phone,
        "bio": teacher.bio,
        "profile_pic": teacher.profile_pic,
        "must_change_password": teacher.must_change_password,
    }), 200


# ✅ Create teacher (admin action)
@teachers_bp.route("", methods=["POST"])
@jwt_required()
def create_teacher():
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    data = request.form.to_dict()
    name = data.get("name")
    username = data.get("username")
    phone = data.get("phone")
    bio = data.get("bio")
    password = data.get("password")

    if not name or not username or not password:
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    # handle profile picture
    profile_pic_url = None
    if "profile_pic" in request.files:
        upload_result = cloudinary.uploader.upload(request.files["profile_pic"])
        profile_pic_url = upload_result.get("secure_url")

    new_teacher = User(
        name=name,
        username=username,
        phone=phone,
        bio=bio,
        role="teacher",
        must_change_password=True,  # enforce password change on first login
        profile_pic=profile_pic_url,
    )
    new_teacher.set_password(password)

    db.session.add(new_teacher)
    db.session.commit()

    return jsonify({
        "message": "Teacher created successfully",
        "id": new_teacher.id,
    }), 201


# ✅ Update teacher (admin only)
@teachers_bp.route("/<int:teacher_id>", methods=["PUT"])
@jwt_required()
def update_teacher(teacher_id):
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    teacher = User.query.filter_by(id=teacher_id, role="teacher").first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    data = request.form.to_dict()
    teacher.name = data.get("name", teacher.name)
    teacher.username = data.get("username", teacher.username)
    teacher.phone = data.get("phone", teacher.phone)
    teacher.bio = data.get("bio", teacher.bio)

    if "profile_pic" in request.files:
        upload_result = cloudinary.uploader.upload(request.files["profile_pic"])
        teacher.profile_pic = upload_result.get("secure_url")

    db.session.commit()
    return jsonify({"message": "Teacher updated"}), 200


# ✅ Delete teacher (admin only)
@teachers_bp.route("/<int:teacher_id>", methods=["DELETE"])
@jwt_required()
def delete_teacher(teacher_id):
    current_user_id = get_jwt_identity()
    admin = User.query.get(current_user_id)

    if not admin or admin.role != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 403

    teacher = User.query.filter_by(id=teacher_id, role="teacher").first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    db.session.delete(teacher)
    db.session.commit()
    return jsonify({"message": "Teacher deleted"}), 200