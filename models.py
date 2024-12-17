from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define the tblTerms model

class TblTerms(db.Model):
    __tablename__ = 'tbl_terms'
    term_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.String(128), nullable=True)
    image = db.Column(db.LargeBinary, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=False)
    
    session = db.relationship('TblSessions', backref='terms')

class TblLessons(db.Model):
    __tablename__ = 'tbl_lessons'
    lesson_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.String(10), db.ForeignKey('tbl_units.unit_id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=False)

    session = db.relationship('TblSessions', backref='lessons')
    unit = db.relationship('TblUnits', backref='lessons')

class TblCards(db.Model):
    __tablename__ = 'tbl_cards'
    card_id = db.Column(db.Integer, primary_key=True)
    term_id = db.Column(db.Integer, db.ForeignKey('tbl_terms.term_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('tbl_lessons.lesson_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'),nullable=False)

    term = db.relationship('TblTerms', backref='cards')
    lesson = db.relationship('TblLessons', backref='cards')
    session = db.relationship('TblSessions', backref='cards')

class TblUnits(db.Model):
    __tablename__ = 'tbl_units'
    unit_id = db.Column(db.String(10), primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.String(64), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('tbl_subjects.subject_id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=True)

    subject = db.relationship('TblSubjects', backref='units')
    session = db.relationship('TblSessions', backref='units')

class TblSubjects(db.Model):
    __tablename__ = 'tbl_subjects'
    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=False)

    session = db.relationship('TblSessions', backref='subjects')

class TblYears(db.Model):
    __tablename__ = 'tbl_years'
    year = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(128), nullable=True)

class TblCardStyles(db.Model):
    __tablename__ = 'tbl_card_styles'
    style_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    height = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    font_size = db.Column(db.Integer, nullable=True)
    font_type = db.Column(db.String(128), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=False)

    session = db.relationship('TblSessions', backref='cardstyles')

class TblUsers(db.Model):
    __tablename__ = 'tbl_users'
    user_id = db.Column(db.String(50), primary_key=True)
    first_name = db.Column(db.String(128), nullable=False)
    last_name = db.Column(db.String(128), nullable=False)
    title_id = db.Column(db.String(4), nullable=True)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=True)
    question = db.Column(db.String(255), nullable=True)
    answer = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('tbl_roles.role_id'), nullable=False)
    created = db.Column(db.Integer, nullable=False)

    role = db.relationship('TblRoles', backref='users')

class TblTitles(db.Model):
    __tablename__ = 'tbl_titles'
    title = db.Column(db.String(4), primary_key=True)
    description = db.Column(db.String(128), nullable=True)

class TblRoles(db.Model):
    __tablename__ = 'tbl_roles'
    role_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(128), nullable=True)

class TblSessions(db.Model):
    __tablename__ = 'tbl_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('tbl_users.user_id'), nullable=False)
    created = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=True)
    terminated = db.Column(db.Integer, nullable=True)

    user = db.relationship('TblUsers', backref='sessions')

class TblSubjectEnrolment(db.Model):
    __tablename__ = 'tbl_subject_enrolment'
    enrolment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('tbl_users.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('tbl_subjects.subject_id'), nullable=True)

    user = db.relationship('TblUsers', backref='subject_enrolment')
    subject = db.relationship('TblSubjects', backref='subject_enrolment')

    
class TblPrintedCards(db.Model):
    __tablename__ = 'tbl_printed_cards'
    print_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('tbl_lessons.lesson_id'), nullable=True)
    created = db.Column(db.Integer, nullable=False)

    session = db.relationship('TblSessions', backref='printed_cards')
    lesson = db.relationship('TblLessons', backref='printed_cards')
