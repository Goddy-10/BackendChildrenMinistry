# app/routes/events.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Event, MediaItem, User
from datetime import datetime
import os
from werkzeug.utils import secure_filename

events_bp = Blueprint("events", __name__)

# Configuration
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "avi", "pdf", "doc", "docx"}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== GET ALL EVENTS ====================
@events_bp.route("/events", methods=["GET", "OPTIONS"])
def get_events():
    """Fetch all events (public endpoint)"""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        events = Event.query.all()
        return jsonify([event.to_dict() for event in events]), 200
    except Exception as e:
        print(f"❌ Error fetching events: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== CREATE EVENT ====================
@events_bp.route("/events", methods=["POST", "OPTIONS"])
@jwt_required()
def create_event():
    """Create a new event with media files"""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Only admins can create events
        if not user or user.role != "admin":
            return jsonify({"error": "Only admins can create events"}), 403
        
        # Get form data
        headline = request.form.get("headline")
        message = request.form.get("message")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        
        # Validate required fields
        if not headline or not start_date_str:
            return jsonify({"error": "Headline and start_date are required"}), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')) if end_date_str else start_date
        except (ValueError, AttributeError) as e:
            print(f"❌ Date parsing error: {str(e)}")
            return jsonify({"error": f"Invalid date format. Use ISO format (YYYY-MM-DD): {str(e)}"}), 400
        
        # Create event
        event = Event(
            headline=headline,
            message=message or "",
            start_date=start_date,
            end_date=end_date,
            created_by=current_user_id
        )
        
        # Handle file uploads
        if "files" in request.files:
            files = request.files.getlist("files")
            upload_folder = current_app.config.get("BASE_UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
            
            for file in files:
                if file and allowed_file(file.filename):
                    try:
                        filename = secure_filename(file.filename)
                        # Add timestamp to avoid duplicates
                        timestamp = str(int(datetime.now().timestamp() * 1000))
                        filename = f"{timestamp}_{filename}"
                        
                        # Create uploads folder if it doesn't exist
                        os.makedirs(upload_folder, exist_ok=True)
                        filepath = os.path.join(upload_folder, filename)
                        file.save(filepath)
                        
                        # Create media item
                        media = MediaItem(
                            filename=file.filename,
                            url=f"/uploads/{filename}",
                            mimetype=file.mimetype,
                            uploaded_by=current_user_id
                        )
                        db.session.add(media)
                        event.media.append(media)
                        print(f"✅ File uploaded: {filename}")
                    except Exception as file_err:
                        print(f"❌ Error uploading file {file.filename}: {str(file_err)}")
                        continue
        
        db.session.add(event)
        db.session.commit()
        
        print(f"✅ Event created: {event.id} - {headline}")
        return jsonify(event.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating event: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==================== GET SINGLE EVENT ====================
@events_bp.route("/events/<int:event_id>", methods=["GET", "OPTIONS"])
def get_event(event_id):
    """Fetch a single event by ID"""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        event = Event.query.get_or_404(event_id)
        return jsonify(event.to_dict()), 200
    except Exception as e:
        print(f"❌ Error fetching event {event_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== UPDATE EVENT ====================
@events_bp.route("/events/<int:event_id>", methods=["PUT", "OPTIONS"])
@jwt_required()
def update_event(event_id):
    """Update an event"""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Only admin or creator can update
        if user.role != "admin" and event.created_by != current_user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update fields
        if "headline" in request.form:
            event.headline = request.form.get("headline")
        if "message" in request.form:
            event.message = request.form.get("message")
        if "start_date" in request.form:
            event.start_date = datetime.fromisoformat(request.form.get("start_date"))
        if "end_date" in request.form:
            event.end_date = datetime.fromisoformat(request.form.get("end_date"))
        
        db.session.commit()
        print(f"✅ Event updated: {event_id}")
        return jsonify(event.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating event: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== DELETE EVENT ====================
# ==================== DELETE EVENT ====================
@events_bp.route("/events/<int:event_id>", methods=["DELETE", "OPTIONS"])
@jwt_required()
def delete_event(event_id):
    """Delete an event"""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        current_user_id = get_jwt_identity()
        event = Event.query.get_or_404(event_id)
        user = User.query.get(current_user_id)
        
        # Only admin or creator can delete
        if user.role != "admin" and event.created_by != current_user_id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Delete associated media files
        upload_folder = current_app.config.get("BASE_UPLOAD_FOLDER")
        
        for media in event.media:
            try:
                # Extract filename from URL (e.g., "1234567890_image.jpg")
                filename = media.url.split("/")[-1]  # ✅ Better extraction
                filepath = os.path.join(upload_folder, filename)
                
                print(f"🗑️  Attempting to delete: {filepath}")
                
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"✅ File deleted: {filepath}")
                else:
                    print(f"⚠️  File not found: {filepath}")
                    
            except Exception as file_err:
                print(f"⚠️  Warning: Could not delete file {media.url}: {str(file_err)}")
        
        db.session.delete(event)
        db.session.commit()
        
        print(f"✅ Event deleted: {event_id}")
        return jsonify({"message": "Event deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting event: {str(e)}")
        return jsonify({"error": str(e)}), 500