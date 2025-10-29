# app/routes/media_routes.py
from flask import Blueprint, request, jsonify
from app.models import HomeMedia
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
import cloudinary.uploader

media_bp = Blueprint("media_bp", __name__, url_prefix="/api/media")

@media_bp.post("/")
@jwt_required()
def upload_media():
    user_id = get_jwt_identity()
    file = request.files.get("file")
    headline = request.form.get("headline")
    description = request.form.get("description")

    if not file:
        return jsonify({"error": "File is required"}), 400

    # Upload directly to Cloudinary
    upload_result = cloudinary.uploader.upload(file, resource_type="auto")

    media_type = "video" if upload_result["resource_type"] == "video" else "image"
    file_url = upload_result["secure_url"]

    media = HomeMedia(
        headline=headline,
        description=description,
        media_type=media_type,
        file_url=file_url,
        uploaded_by=user_id,
    )
    db.session.add(media)
    db.session.commit()

    return jsonify(media.to_dict()), 201


# ✅ Get all media
@media_bp.get("/")
def get_all_media():
    try:
        media_items = HomeMedia.query.order_by(HomeMedia.id.desc()).all()
        return jsonify([m.to_dict() for m in media_items]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

#----------featured media----------#
@media_bp.get("/featured")
def get_featured_media():
    featured = HomeMedia.query.filter_by(is_featured=True).order_by(HomeMedia.created_at.desc()).all()
    return jsonify([m.to_dict() for m in featured]), 200


from flask_jwt_extended import jwt_required, get_jwt_identity
#------toggle featured media-----------#
@media_bp.patch("/<int:id>/toggle-featured")
@jwt_required()
def toggle_featured(id):
    user_id = get_jwt_identity()
    # Optionally verify admin role if you store roles in User
    media = HomeMedia.query.get(id)
    if not media:
        return jsonify({"error": "Media not found"}), 404

    media.is_featured = not media.is_featured
    db.session.commit()

    return jsonify({"message": "Media featured status updated", "is_featured": media.is_featured}), 200
    

#-----------DELETE MEDIA----------#
@media_bp.delete("/<int:id>")
@jwt_required()
def delete_media(id):
    user_id = get_jwt_identity()

    # Find media by ID
    media = HomeMedia.query.get(id)
    if not media:
        return jsonify({"error": "Media not found"}), 404

    # Optional: restrict delete to admin or owner
    # (uncomment if needed)
    # user = User.query.get(user_id)
    # if user.role != "admin" and media.uploaded_by != user_id:
    #     return jsonify({"error": "Not authorized"}), 403

    # Extract Cloudinary public ID from URL before deleting
    try:
        public_id = media.file_url.split("/")[-1].split(".")[0]
        cloudinary.uploader.destroy(public_id, resource_type=media.media_type)
    except Exception as e:
        print(f"Cloudinary delete error: {e}")

    # Delete from database
    db.session.delete(media)
    db.session.commit()

    return jsonify({"message": "Media deleted successfully"}), 200