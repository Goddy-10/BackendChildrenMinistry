# app/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from sqlalchemy import event


# Association table for many-to-many: Event <-> Media (optional)
event_media = db.Table(
    "event_media",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id"), primary_key=True),
    db.Column("media_id", db.Integer, db.ForeignKey("media_items.id"), primary_key=True),
)

class User(db.Model):
    """
    Users: admin and teachers. Fields designed for auth and profile.
    - role: 'admin' or 'teacher'
    - must_change_password: when true, user must change pw on first login
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # used for login (or phone/email)
    name = db.Column(db.String(120))
    phone = db.Column(db.String(40), index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(30), nullable=False, default="teacher")  # 'admin' or 'teacher'
    password_hash = db.Column(db.String(255), nullable=False)
    must_change_password = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(300), nullable=True)  # URL or path to file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   

    @property
    def password(self):
        raise AttributeError("Password cannot be read directly.")

    @password.setter
    def password(self, plain_password):
        if isinstance(plain_password,tuple):
            plain_password=plain_password[0]
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        return check_password_hash(self.password_hash, plain_password)
    
    def __repr__(self):
        return f"<User {self.username}({self.role})"


    # relationships
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id",name="fk_user_department_id"), nullable=True)
    # if teacher, they may be assigned timetable entries or reports etc.
    timetable_entries = db.relationship("TimetableEntry", backref="teacher", lazy="dynamic")
    reports = db.relationship("Report", back_populates="teacher")  # define Report later if needed

#password management
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "bio": self.bio,
            "profile_pic": self.profile_pic,
            "must_change_password": self.must_change_password,
            "is_active": self.is_active,
        }

class SundayClass(db.Model):
    """
    Sunday classes (Gifted Brains, Beginners, etc.)
    This is the class metadata. Children are linked to a class by age (or backend logic).
    """
    __tablename__ = "sunday_classes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    min_age = db.Column(db.Integer, nullable=True)
    max_age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    children = db.relationship("Child", backref="sunday_class", lazy="dynamic")
    timetable_entries = db.relationship("TimetableEntry", backref="sunday_class", lazy="dynamic")

    def __repr__(self):
        return f"<SundayClass {self.name}>"
    

    def to_dict(self):
        return {
        "id": self.id,
        "name": self.name,
        "min_age": self.min_age,
        "max_age": self.max_age,
        "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None
    }

class Child(db.Model):
    """
    Children records for Sunday school.
    - parent_name, parent_contact stored here for quick access
    - class_id optional (backend may auto-assign based on age)
    """
    __tablename__ = "children"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    parent_name = db.Column(db.String(150))
    parent_contact = db.Column(db.String(60))
    added_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # admin/teacher who added
    class_id = db.Column(db.Integer, db.ForeignKey("sunday_classes.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    attendance_records = db.relationship("Attendance", backref="child", lazy=True, cascade="all,delete-orphan",passive_deletes=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "parent_name": self.parent_name,
            "parent_contact": self.parent_contact,
            "class_id": self.class_id,
            "created_at": self.created_at.isoformat(),
        }




AGE_RANGES = {
    "Gifted Brains": (0, 3),
    "Beginners": (3, 6),
    "Shinners": (6, 9),
    "Conquerors": (9, 13),
    "Teens": (13, 18),
}

def assign_class(target):
    if target.age is None:
        return
    try:
        age = int(target.age)
    except (ValueError, TypeError):
        return
    for class_name, (min_age, max_age) in AGE_RANGES.items():
        if min_age <= age < max_age:
            cls = db.session.query(SundayClass).filter_by(name=class_name).first()
            if cls:
                target.class_id = cls.id
            break

@event.listens_for(Child, "before_insert")
def auto_assign_class_insert(mapper, connection, target):
    assign_class(target)

@event.listens_for(Child, "before_update")
def auto_assign_class_update(mapper, connection, target):
    assign_class(target)

    

class Attendance(db.Model):
    """
    Attendance per child per date, tied to a SundayClass (or class assigned).
    - present: boolean
    - recorded_by: user id (teacher)
    """
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey("children.id",ondelete="CASCADE"), nullable=False)
    present = db.Column(db.Boolean, default=False)
    class_id = db.Column(db.Integer, db.ForeignKey("sunday_classes.id"), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    recorder = db.relationship("User", foreign_keys=[recorded_by])

class Offering(db.Model):
    """
    Offerings per class per date (totals).
    - class_id: which class gave this offering
    - amount: integer/float in smallest currency unit or float
    - recorded_by: user who recorded the offering
    - note: optional
    """
    __tablename__ = "offerings"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("sunday_classes.id"), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recorder = db.relationship("User", foreign_keys=[recorded_by])
    sunday_class = db.relationship("SundayClass", foreign_keys=[class_id])

class TimetableEntry(db.Model):
    """
    Timetable entry for a specific date. Each entry lists the teacher on duty and the class.
    - date: the date of class (not necessarily Sunday)
    - class_id: class assignment
    - teacher_id: who will take it
    - notes: topic taught / resources / remarks (to be filled after class)
    """
    __tablename__ = "timetable_entries"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("sunday_classes.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    topic = db.Column(db.String(255), nullable=True)
    bible_reference = db.Column(db.String(255), nullable=True)
    resources = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



    @property
    def class_name(self):
        if not self.class_id:
            return None
        cls = SundayClass.query.get(self.class_id)
        return cls.name if cls else None

    @property
    def teacher_name(self):
        if not self.teacher_id:
            return None
        teacher = User.query.get(self.teacher_id)
        return teacher.username if teacher else None
    # Relationships


    def to_dict(self):
        cls = SundayClass.query.get(self.class_id) if self.class_id else None
        teacher = User.query.get(self.teacher_id) if self.teacher_id else None

        return {
        "id": self.id,
        "date": self.date.strftime("%Y-%m-%d"),
        "class_id": self.class_id,
        "class_name": cls.name if cls else None,
        "teacher_id": self.teacher_id,
        "teacher_name": teacher.username if teacher else None,
        "topic": self.topic,
        "bible_reference": self.bible_reference,
        "resources": self.resources,
        "remarks": self.remarks,
        "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
    }
    
    
    

class Event(db.Model):
    """
    Events (camps, conferences, etc). Each event can have many media files attached.
    """
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])
    media = db.relationship("MediaItem", secondary=event_media, backref="events")

class MediaItem(db.Model):
    """
    Media files: images, videos, docs (stored as URLs/paths)
    - type: mimetype or category e.g. 'image', 'video', 'document', 'audio'
    - url: location (e.g. S3 URL or file path)
    """
    __tablename__ = "media_items"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    url = db.Column(db.String(1024), nullable=False)
    mimetype = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_featured=db.Column(db.Boolean,default=False)

    uploader = db.relationship("User", foreign_keys=[uploaded_by])

# ==================== REPLACE MY OLD FinanceEntry ====================
class FinanceEntry(db.Model):
    __tablename__ = "finance_entries"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    
    # Income-specific fields
    service_type = db.Column(db.String(120), nullable=True)  # Sunday, Midweek, etc.
    main_church = db.Column(db.Numeric(12, 2), default=0.0)
    children_ministry = db.Column(db.Numeric(12, 2), default=0.0)
    
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": self.id,
            "type": "income",
            "date": self.date.strftime("%Y-%m-%d"),
            "service_type": self.service_type,
            "main_church": float(self.main_church),
            "children_ministry": float(self.children_ministry),
            "amount": 0,           # kept for compatibility
            "details": None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ==================== NEW Expenditure MODEL ====================
class Expenditure(db.Model):
    __tablename__ = "expenditures"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    details = db.Column(db.String(255), nullable=False)  # e.g. "Rent – Main Hall"

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": self.id,
            "type": "expenditure",
            "date": self.date.strftime("%Y-%m-%d"),
            "service_type": None,
            "main_church": 0,
            "children_ministry": 0,
            "amount": float(self.amount),
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }






class Project(db.Model):
    """
    Development projects (development tab). Keep title, description, status, deadline.
    """
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="planned")  # planned|current|completed
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])


    def to_dict(self):
        return {
        "id": self.id,
        "title": self.title,
        "description": self.description,
        "status": self.status,
        "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else None,
        "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
        "created_by": self.created_by,
        "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        "creator": {
            "id": self.creator.id,
            "username": self.creator.username
        } if self.creator else None
    }





# Optional: a Report model used by teachers (lesson reports, topic, bible reference, resources, remarks)
class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("sunday_classes.id"), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    topic = db.Column(db.String(255), nullable=True)
    bible_reference = db.Column(db.String(255), nullable=True)
    resources = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("User", back_populates="reports")
    sunday_class = db.relationship("SundayClass", foreign_keys=[class_id])



    # app/models.py (additions)



class Mission(db.Model):
    __tablename__ = "missions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)  # activity name
    date = db.Column(db.Date, nullable=True)           # single mission date
    location = db.Column(db.String(200), nullable=True)
    souls_won=db.Column(db.Integer,default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one mission has many partners
    partners = db.relationship("MissionPartner", backref="mission", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "souls_won":self.souls_won,
            "partners": [p.to_dict() for p in self.partners]  # include all partners
        }


class MissionPartner(db.Model):
    __tablename__ = "mission_partners"

    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(db.Integer, db.ForeignKey("missions.id"), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    support = db.Column(db.Float, nullable=True)  # numeric support (optional)
    contact = db.Column(db.String(120), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "partner_name": self.name,
            "support": self.support,
            "contact": self.contact
        }


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # contact info
    contact_person = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)

    # optional: many-to-many with users (teachers, admins, members)
    members = db.relationship("User", backref="department", lazy=True)


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            # optionally include member count
            "member_count": len(self.members) if self.members else 0
        }


class NewMember(db.Model):
    __tablename__ = "new_members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True, unique=True)
    join_date = db.Column(db.Date, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    residence = db.Column(db.Text, nullable=True)

    # optional: link to Sunday class or department if relevant
    sunday_class_id = db.Column(db.Integer, db.ForeignKey("sunday_classes.id"), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)


    def to_dict(self):
        return {
        "id": self.id,
        "name": self.name,
        "phone": self.phone,
        "email": self.email,
        "join_date": self.join_date.strftime("%Y-%m-%d") if self.join_date else None,
        "notes": self.notes,
        "residence":self.residence,
        "sunday_class_id": self.sunday_class_id,
        "department_id": self.department_id,

        # Optional: include related objects if needed
       
    }




class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    position = db.Column(db.String(120), nullable=True)
    residence = db.Column(db.String(120), nullable=True)
    date_joined = db.Column(db.Date, default=datetime.utcnow)

    # optional: link to department or home church
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    home_church_id = db.Column(db.Integer, db.ForeignKey("home_churches.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship("Department", backref="members_list", lazy=True)
    home_church = db.relationship("HomeChurch", backref="members_list", lazy=True)


    def to_dict(self):
        return {
        "id": self.id,
        "full_name": self.full_name,
        "phone": self.phone,
        "residence": self.residence,
        
        
        "department_id": self.department_id
    }





class Visitor(db.Model):
    __tablename__ = "visitors"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    residence = db.Column(db.String(120), nullable=True)
    date_of_visit = db.Column(db.Date, default=datetime.utcnow)
    prayer_request = db.Column(db.Text, nullable=True)
    follow_up_status = db.Column(db.String(50), default="pending")  # pending | contacted | joined

    # for QR code tracking
    qr_code = db.Column(db.String(255), nullable=True)  # optional URL or identifier

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "name": self.full_name,  # keep 'name' if frontend expects it
            "phone": self.phone,
            "email": self.email,
            "residence": self.residence,
            "prayer_request": self.prayer_request,
            "visit_date": self.date_of_visit.isoformat() if self.date_of_visit else None,
            "follow_up_status": self.follow_up_status
    }





class HomeChurch(db.Model):
    __tablename__ = "home_churches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    contact_person = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(120), nullable=True)

    # optional: weekly attendance
    attendance_records = db.relationship("HomeChurchAttendance", backref="home_church", lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # In HomeChurch
    def to_dict(self):
        return {
        "id": self.id,
        "name": self.name,
        "contact": self.contact,
    }







class HomeChurchAttendance(db.Model):
    __tablename__ = "home_church_attendance"

    id = db.Column(db.Integer, primary_key=True)
    home_church_id = db.Column(db.Integer, db.ForeignKey("home_churches.id"), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow, index=True)
    present_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)


    def to_dict(self):
        return {
        "id": self.id,
        "home_church_id": self.home_church_id,
        "date": self.date.isoformat(),
        "attendees": self.attendees,
    }






# app/models.py
class HomeMedia(db.Model):
    _tablename_ = "home_media"

    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=True)
    media_type = db.Column(db.String(20), nullable=False)  # "image" or "video"
    file_url = db.Column(db.String(255), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "headline": self.headline,
            "description": self.description,
            "media_type": self.media_type,
            "file_url": self.file_url,
            "uploaded_by": self.uploaded_by,
            "is_featured":self.is_featured,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }









# -------------------------------
# PROGRAM MATERIAL MODELS
# -------------------------------

class Program(db.Model):
    __tablename__ = "programs"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    coordinator = db.Column(db.String(120))
    date = db.Column(db.String(20))

    files = db.relationship(
        "ProgramFile",
        backref="program",
        cascade="all, delete-orphan",
        lazy=True
    )

    def to_dict(self):
        return {
        "id": self.id,
        "description": self.description,
        "coordinator": self.coordinator,
        "date": self.date,
        "files": [file.to_dict() for file in self.files]   # ← FIX
    }


class ProgramFile(db.Model):
    __tablename__ = "program_files"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programs.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20))

    def to_dict(self):
        return {
        "id": self.id,
        "filename": self.filename,
        "file_type": self.file_type,
        "url": f"/uploads/{self.filename}"   # ← VERY IMPORTANT
    }





class DepartmentMember(db.Model):
    __tablename__ = "department_members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id"), nullable=True
    )

    department = db.relationship("Department", backref="department_members", lazy=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


