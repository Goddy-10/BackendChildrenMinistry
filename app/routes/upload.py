


# # app/galleryroutes.py
# from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity
# import cloudinary.uploader
# from app.models import db, MediaItem, User

# gallery_bp = Blueprint("gallery", __name__, url_prefix="/gallery")

# # ---------- GET MEDIA ----------
# @gallery_bp.route("/<string:media_type>", methods=["GET"])
# def get_media(media_type):
#     """Fetch photos or videos"""
#     if media_type not in ["photos", "videos"]:
#         return jsonify({"error": "Invalid media type"}), 400

#     items = MediaItem.query.filter(
#         MediaItem.mimetype.like(f"{'image' if media_type == 'photos' else 'video'}%")
#     ).order_by(MediaItem.uploaded_at.desc()).all()

#     return jsonify([
#         {
#             "id": item.id,
#             "filename": item.filename,
#             "url": item.url,
#             "description": getattr(item, "description", ""),
#         } for item in items
#     ])

# # ---------- UPLOAD MEDIA ----------
# @gallery_bp.route("/upload", methods=["POST"])
# @jwt_required()
# def upload_media():
#     """Upload photo or video (admins only)"""
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#     if not user or user.role != "admin":
#         return jsonify({"error": "Unauthorized"}), 403

#     file = request.files.get("file")
#     description = request.form.get("description", "")
#     media_type = request.form.get("type")  # "photos" or "videos"

#     if not file or not media_type:
#         return jsonify({"error": "File and type are required"}), 400

#     # Determine folder and mimetype
#     folder = "gallery/photos" if media_type == "photos" else "gallery/videos"
#     mimetype = file.mimetype

#     # Upload to Cloudinary
#     try:
#         result = cloudinary.uploader.upload(file, folder=folder, resource_type="auto")
#         url = result.get("secure_url")
#     except Exception as e:
#         return jsonify({"error": "Upload failed", "details": str(e)}), 500

#     # Save in DB
#     media_item = MediaItem(
#         filename=file.filename,
#         url=url,
#         mimetype=mimetype,
#         uploaded_by=user.id,
#         uploaded_at=db.func.now(),
#         description=description
#     )
#     db.session.add(media_item)
#     db.session.commit()

#     return jsonify({
#         "id": media_item.id,
#         "filename": media_item.filename,
#         "url": media_item.url,
#         "description": media_item.description
#     }), 201













# app/galleryroutes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import cloudinary.uploader
from app.models import db, MediaItem, User

gallery_bp = Blueprint("gallery", __name__, url_prefix="/gallery")

# ---------- GET MEDIA ----------
@gallery_bp.route("/<string:media_type>", methods=["GET"])
def get_media(media_type):
    """Fetch photos or videos"""
    if media_type not in ["photos", "videos"]:
        return jsonify({"error": "Invalid media type"}), 400

    items = MediaItem.query.filter(
        MediaItem.mimetype.like(f"{'image' if media_type == 'photos' else 'video'}%")
    ).order_by(MediaItem.uploaded_at.desc()).all()

    return jsonify([
        {
            "id": item.id,
            "filename": item.filename,
            "url": item.url,
            "description": getattr(item, "description", ""),  # keep this optional
        } for item in items
    ])


# ---------- UPLOAD MEDIA ----------
@gallery_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_media():
    """Upload photo or video (admins only)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    file = request.files.get("file")
    description = request.form.get("description", "")
    media_type = request.form.get("type")  # "photos" or "videos"

    if not file or not media_type:
        return jsonify({"error": "File and type are required"}), 400

    # Determine folder and mimetype
    folder = "gallery/photos" if media_type == "photos" else "gallery/videos"
    mimetype = file.mimetype

    # Upload to Cloudinary
    try:
        result = cloudinary.uploader.upload(file, folder=folder, resource_type="auto")
        url = result.get("secure_url")
    except Exception as e:
        return jsonify({"error": "Upload failed", "details": str(e)}), 500

    # Save in DB
    media_item = MediaItem(
        filename=file.filename,
        url=url,
        mimetype=mimetype,
        uploaded_by=user.id,
        uploaded_at=db.func.now(),
    )

    # Add description column if missing in the model
    if hasattr(media_item, "description"):
        media_item.description = description

    db.session.add(media_item)
    db.session.commit()

    return jsonify({
        "id": media_item.id,
        "filename": media_item.filename,
        "url": media_item.url,
        "description": getattr(media_item, "description", "")
    }), 201