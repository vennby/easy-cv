from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    first_name = db.Column(db.Text)
    personal_info = db.relationship('PersonalInfo', uselist=False, backref='user')
    bios = db.relationship('Bios')
    educations = db.relationship('Educations')
    experiences = db.relationship('Experiences')
    projects = db.relationship('Projects')
    skills = db.relationship('Skills')
    resumes = db.relationship('Resume', backref='user', lazy=True)

# Association tables for selections
resume_bios = db.Table('resume_bios',
    db.Column('resume_id', db.Integer, db.ForeignKey('resume.id'), primary_key=True),
    db.Column('bio_id', db.Integer, db.ForeignKey('bios.id'), primary_key=True)
)
resume_educations = db.Table('resume_educations',
    db.Column('resume_id', db.Integer, db.ForeignKey('resume.id'), primary_key=True),
    db.Column('education_id', db.Integer, db.ForeignKey('educations.id'), primary_key=True)
)
resume_experiences = db.Table('resume_experiences',
    db.Column('resume_id', db.Integer, db.ForeignKey('resume.id'), primary_key=True),
    db.Column('experience_id', db.Integer, db.ForeignKey('experiences.id'), primary_key=True)
)
resume_projects = db.Table('resume_projects',
    db.Column('resume_id', db.Integer, db.ForeignKey('resume.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True)
)
resume_skills = db.Table('resume_skills',
    db.Column('resume_id', db.Integer, db.ForeignKey('resume.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True)
)

class PersonalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.Text)
    email = db.Column(db.Text)
    phone = db.Column(db.Text)
    address = db.Column(db.Text)
    linkedin = db.Column(db.Text)
    github = db.Column(db.Text)
    website = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    image_path = db.Column(db.String(200), nullable=True)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bios = db.relationship('Bios', secondary=resume_bios, lazy='subquery')
    educations = db.relationship('Educations', secondary=resume_educations, lazy='subquery')
    experiences = db.relationship('Experiences', secondary=resume_experiences, lazy='subquery')
    projects = db.relationship('Projects', secondary=resume_projects, lazy='subquery')
    skills = db.relationship('Skills', secondary=resume_skills, lazy='subquery')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    format = db.Column(db.String(50), nullable=False, default='classic')

class Bios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bio = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Educations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uni = db.Column(db.Text)
    location = db.Column(db.Text)
    degree = db.Column(db.Text)
    start_year = db.Column(db.Text)
    end_year = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Experiences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Text)
    comp = db.Column(db.Text)
    desc = db.Column(db.Text)
    start_date = db.Column(db.Text, nullable=False)
    end_date = db.Column(db.Text, nullable=True)
    ongoing = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class Projects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proj = db.Column(db.Text)
    tool = db.Column(db.Text)
    desc = db.Column(db.Text)
    link = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class Skills(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text)
    group = db.Column(db.Text, nullable=True)  # New: group name for skill grouping
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))