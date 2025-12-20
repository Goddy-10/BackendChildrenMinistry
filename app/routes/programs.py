import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app.extensions import db
from app.models import Program, ProgramFile

programs_bp = Blueprint("programs", __name__, url_prefix="/api/programs")

# -------------------------------------------
# GET ALL PROGRAMS
# -------------------------------------------
@programs_bp.route("/", methods=["GET"])
def list_programs():
    programs = Program.query.order_by(Program.id.desc()).all()
    return jsonify([p.to_dict() for p in programs]), 200



@programs_bp.route("/", methods=["POST"])
def create_program():
    text = request.form.get("text")
    date = request.form.get("date")
    coordinator = request.form.get("coordinator")

    # Validate required field
    if not text:
        return jsonify({"error": "Description required"}), 400

    # Create Program entry
    program = Program(
        description=text,
        date=date,
        coordinator=coordinator
    )
    db.session.add(program)
    db.session.commit()

    # FILE HANDLING
    files = request.files.getlist("files")

    for file in files:
        if file:
            filename = file.filename
            filepath = os.path.join(current_app.config["BASE_UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Save to database
            pf = ProgramFile(
                filename=filename,
                program_id=program.id
            )
            db.session.add(pf)

    db.session.commit()

    return jsonify({"message": "Program created", "id": program.id}), 201
# -------------------------------------------
# UPDATE PROGRAM (inline save)
# -------------------------------------------
@programs_bp.route("/<int:id>", methods=["PUT"])
def update_program(id):
    program = Program.query.get_or_404(id)

    description = request.form.get("description")
    coordinator = request.form.get("coordinator")
    date = request.form.get("date")

    if description:
        program.description = description
    if coordinator:
        program.coordinator = coordinator
    if date:
        program.date = date

    db.session.commit()

    # If new files uploaded
    if "files" in request.files:
        files = request.files.getlist("files")
        for f in files:
            filename = f.filename
            save_path = os.path.join(current_app.config["BASE_UPLOAD_FOLDER"], filename)
            f.save(save_path)

            pf = ProgramFile(
                program_id=program.id,
                filename=filename,
                file_type=f.content_type
            )
            db.session.add(pf)

        db.session.commit()

    return jsonify(program.to_dict()), 200







# -------------------------------------------
# DELETE PROGRAM
# -------------------------------------------
@programs_bp.route("/<int:id>", methods=["DELETE"])
def delete_program(id):
    program = Program.query.get_or_404(id)
    db.session.delete(program)
    db.session.commit()
    return jsonify({"message": "Program deleted"}), 200


# -------------------------------------------
# DOWNLOAD FILE
# -------------------------------------------
@programs_bp.route("/file/<filename>", methods=["GET"])
def download_program_file(filename):
    directory = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(directory, filename, as_attachment=True)