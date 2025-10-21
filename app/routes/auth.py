


# from flask import Blueprint, request, jsonify
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
# from app.models import User
# from app.extensions import db

# auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# # ---------- LOGIN ----------
# @auth_bp.route("/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     identifier = data.get("identifier")  # username or phone
#     password = data.get("password")
#     role = data.get("role")

#     if not identifier or not password or not role:
#         return jsonify({"error": "Missing credentials"}), 400

#     # Find user by username or phone
#     user = User.query.filter(
#         (User.username == identifier) | (User.phone == identifier)
#     ).first()

#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     if user.role != role:
#         return jsonify({"error": f"Invalid role for {identifier}"}), 403

#     # ✅ Use check_password method (or password_hash column)
#     if not user.check_password(password):
#         return jsonify({"error": "Invalid password"}), 401

#     # Create JWT token
#     token = create_access_token(identity=str(user.id))

#     return jsonify({
#         "token": token,
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "name": user.name,
#             "role": user.role,
#             "phone": user.phone,
#             "bio": user.bio,
#             "profile_pic": user.profile_pic
#         }
#     }), 200


# # ---------- GET CURRENT USER ----------
# @auth_bp.route("/me", methods=["GET"])
# @jwt_required()
# def me():
#     user_id = get_jwt_identity()
    
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     return jsonify({
#         "id": user.id,
#         "username": user.username,
#         "name": user.name,
#         "role": user.role,
#         "phone": user.phone,
#         "bio": user.bio,
#         "profile_pic": user.profile_pic
#     })


# # ---------- CHANGE PASSWORD ----------
# @auth_bp.route("/change-password", methods=["POST"])
# @jwt_required()
# def change_password():
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)

#     data = request.get_json()
#     old_password = data.get("old_password")
#     new_password = data.get("new_password")

#     if not old_password or not new_password:
#         return jsonify({"error": "Both old and new passwords are required"}), 400

#     # ✅ Use check_password method
#     if not user.check_password(old_password):
#         return jsonify({"error": "Old password is incorrect"}), 400

#     user.password = new_password  # will trigger the setter to hash it
#     db.session.commit()

#     return jsonify({"message": "Password updated successfully"})





















from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------- LOGIN ----------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    identifier = data.get("identifier")  # username or phone
    password = data.get("password")
    role = data.get("role")

    if not identifier or not password or not role:
        return jsonify({"error": "Missing credentials"}), 400

    # Find user by username or phone
    user = User.query.filter(
        (User.username == identifier) | (User.phone == identifier)
    ).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role != role:
        return jsonify({"error": f"Invalid role for {identifier}"}), 403

    if not user.check_password(password):
        return jsonify({"error": "Invalid password"}), 401

    # ✅ JWT Token
    token = create_access_token(identity=str(user.id))

    # ✅ Include must_change_password in response
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "bio": user.bio,
            "profile_pic": user.profile_pic,
            "must_change_password": user.must_change_password,  # <---
        }
    }), 200


# ---------- GET CURRENT USER ----------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "phone": user.phone,
        "bio": user.bio,
        "profile_pic": user.profile_pic,
        "must_change_password": user.must_change_password,  # <---
    })


# ---------- CHANGE PASSWORD ----------
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Both old and new passwords are required"}), 400

    if not user.check_password(old_password):
        return jsonify({"error": "Old password is incorrect"}), 400

    # ✅ Update password + mark must_change_password as False
    user.password = new_password  # triggers hashing
    user.must_change_password = False
    db.session.commit()

    return jsonify({"message": "Password updated successfully"})