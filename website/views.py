from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file, abort
from flask_login import login_required, current_user, logout_user
from .models import *
from . import db
from .resumes.resume_classic import generate_classic_resume
from .resumes.resume_modern import generate_modern_resume
import os, io, json
import datetime

views = Blueprint('views', __name__)

@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    # If user has no resumes, redirect to profile page
    resume_count = Resume.query.filter_by(user_id=current_user.id).count()
    if resume_count == 0:
        return redirect(url_for('views.profile'))
    
    search_query = request.args.get('search', '').strip() if 'search' in request.args else ''
    sort_order = request.args.get('sort', 'newest').strip()
    
    resumes = Resume.query.filter_by(user_id=current_user.id)
    
    # Apply sorting
    if sort_order == 'oldest':
        resumes = resumes.order_by(Resume.created_at.asc())
    else:  # default to newest
        resumes = resumes.order_by(Resume.created_at.desc())
    
    if search_query:
        resumes = resumes.filter(Resume.name.ilike(f"%{search_query}%"))
    
    resumes = resumes.all()
    return render_template("home.html", user=current_user, resumes=resumes, search_query=search_query, sort_order=sort_order)

@views.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'bio' in request.form:
            return add_bio(
                request.form.get('bio')
            )
        if 'uni' in request.form:
            return add_education(
                request.form.get('uni'),
                request.form.get('location'),
                request.form.get('degree'),
                request.form.get('start_year'),
                request.form.get('end_year')
            )
        if 'role' in request.form:
            return add_experience(
                request.form.get('role'),
                request.form.get('comp'),
                request.form.get('desc'),
                request.form.get('start_date'),
                request.form.get('end_date'),
                request.form.get('ongoing')
            )
        if 'proj' in request.form:
            return add_project(
                request.form.get('proj'),
                request.form.get('tool'),
                request.form.get('desc'),
                request.form.get('link')
            )
        elif 'skill' in request.form:
            return add_skill(request.form.get('skill'))
    
    skill_group_options = sorted({(skill.group or '').strip() for skill in current_user.skills if (skill.group or '').strip()})
    return render_template(
        "profile.html",
        user=current_user,
        calculate_duration=calculate_duration,
        skill_group_options=skill_group_options
    )

@views.route('/update-personal-info', methods=['POST'])
@login_required
def update_personal_info():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    linkedin = request.form.get('linkedin')
    github = request.form.get('github')
    website = request.form.get('website')

    personal_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
    if not personal_info:
        personal_info = PersonalInfo(user_id=current_user.id)
        db.session.add(personal_info)

    personal_info.full_name = full_name
    personal_info.email = email
    personal_info.phone = phone
    personal_info.address = address
    personal_info.linkedin = linkedin
    personal_info.github = github
    personal_info.website = website
    # Handle profile image upload
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and file.filename:
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            personal_info.image_path = filename
    db.session.commit()
    flash('Personal information updated!', category='success')
    return redirect(url_for('views.profile'))

@views.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@views.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    confirmation = (request.form.get('delete_confirmation') or '').strip().upper()
    if confirmation != 'DELETE':
        flash("Type DELETE to confirm account deletion.", category='error')
        return redirect(url_for('views.settings'))

    user = current_user

    try:
        personal_info = PersonalInfo.query.filter_by(user_id=user.id).first()
        if personal_info and personal_info.image_path:
            image_path = os.path.join(os.path.dirname(__file__), 'static', 'uploads', personal_info.image_path)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass

        resumes = Resume.query.filter_by(user_id=user.id).all()
        for resume in resumes:
            resume.bios = []
            resume.educations = []
            resume.experiences = []
            resume.projects = []
            resume.skills = []

        db.session.flush()

        for resume in resumes:
            db.session.delete(resume)

        Bios.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Educations.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Experiences.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Projects.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Skills.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        PersonalInfo.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        user_id = user.id
        user_record = User.query.get(user_id)
        if user_record:
            db.session.delete(user_record)

        db.session.commit()
        logout_user()
        flash('Your account and all related data were deleted.', category='success')
        return redirect(url_for('auth.sign_in'))
    except Exception:
        db.session.rollback()
        flash('Could not delete account right now. Please try again.', category='error')
        return redirect(url_for('views.settings'))

def add_bio(bio):
    bio = request.form.get('bio')
    
    new_bio = Bios(
        bio = bio,
        user_id=current_user.id
    )
    
    db.session.add(new_bio)
    db.session.commit()
    flash("Bio added!", category='success')
    return redirect(url_for('views.profile'))

def add_education(uni, location, degree, start_year, end_year):
    uni = request.form.get('uni')
    location = request.form.get('location')
    degree = request.form.get('degree')
    start_year = request.form.get('start_year')
    end_year = request.form.get('end_year')

    new_education = Educations(
        uni=uni,
        location=location,
        degree = degree,
        start_year = start_year,
        end_year = end_year,
        user_id=current_user.id
    )
    
    db.session.add(new_education)
    db.session.commit()
    flash("Education added!", category='success')
    return redirect(url_for('views.profile'))

def is_ongoing_experience(start_date_str, end_date_str):
    import datetime
    def parse_date(s):
        if not s:
            return None
        for fmt in ('%Y-%m-%d', '%Y-%m', '%Y'):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None
    end = parse_date(end_date_str)
    today = datetime.date.today()
    # Ongoing if end date is missing or in the future
    return not end_date_str or (end and end > today)

def calculate_duration(start_date_str, end_date_str=None):
    """
    Calculate the duration between two dates in years and months.
    If end_date_str is missing, use today as the end date (ongoing).
    """
    import datetime
    def parse_date(s):
        if not s:
            return None
        for fmt in ('%Y-%m-%d', '%Y-%m', '%Y'):
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None
    start = parse_date(start_date_str)
    # If end_date_str is missing or empty, treat as ongoing and use today
    if not end_date_str or end_date_str.strip() == '':
        end = datetime.date.today()
    else:
        end = parse_date(end_date_str)
    if not start or not end:
        return ''
    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day
    if days < 0:
        months -= 1
        prev_month = (end.month - 1) if end.month > 1 else 12
        prev_year = end.year if end.month > 1 else end.year - 1
        days_in_prev_month = (datetime.date(prev_year, prev_month % 12 + 1, 1) - datetime.timedelta(days=1)).day
        days += days_in_prev_month
    if months < 0:
        years -= 1
        months += 12
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    return ', '.join(parts) if parts else 'Less than a month'

def add_experience(role, comp, desc, start_date, end_date, ongoing):
    import datetime
    role = request.form.get('role')
    comp = request.form.get('comp')
    desc = request.form.get('desc')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    # If end_date is in the future, force ongoing
    ongoing = request.form.get('ongoing') == 'on'
    end_date_obj = None
    if end_date:
        try:
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except Exception:
            try:
                end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m').date()
            except Exception:
                try:
                    end_date_obj = datetime.datetime.strptime(end_date, '%Y').date()
                except Exception:
                    end_date_obj = None
    # If end_date is missing or in the future, set ongoing True and end_date to None
    if not end_date or (end_date_obj and end_date_obj > datetime.date.today()):
        ongoing = True
        end_date = None
    duration = calculate_duration(start_date, end_date)
    new_experience = Experiences(
        role=role,
        comp=comp,
        desc=desc,
        start_date=start_date,
        end_date=end_date if not ongoing else None,
        ongoing=ongoing,
        user_id=current_user.id
    )
    new_experience.duration = duration
    db.session.add(new_experience)
    db.session.commit()
    flash("Experience added!", category='success')
    return redirect(url_for('views.profile'))

def add_project(proj, tool, desc, link=None):
    new_project = Projects(
        proj=proj,
        tool=tool,
        desc=desc,
        link=link,
        user_id=current_user.id
    )

    db.session.add(new_project)
    db.session.commit()
    flash("Project added!", category='success')
    return redirect(url_for('views.profile'))

def add_skill(skill_data=None):
    skill_data = skill_data or request.form.get('skill')
    group = request.form.get('group')
    new_group = request.form.get('new_group')
    group = new_group if new_group else group
    if len(skill_data) > 50:
        flash("Skill must be smaller than 50 characters!", category='error')
    else:
        new_skill = Skills(data=skill_data, group=group, user_id=current_user.id)
        db.session.add(new_skill)
        db.session.commit()
        flash("Skill added!", category='success')
    return redirect(url_for('views.profile'))

@views.route('/delete-bio', methods=['POST'])
@login_required
def delete_bio():
    bio_data = json.loads(request.data)
    bio_id = bio_data['bioId']
    bio = Bios.query.get(bio_id)
    if bio and bio.user_id == current_user.id:
        db.session.delete(bio)
        db.session.commit()
    return jsonify({})

@views.route('/edit-bio', methods=['POST'])
@login_required
def edit_bio():
    data = json.loads(request.data or '{}')
    bio_id = data.get('bioId')
    bio_text = (data.get('bio') or '').strip()
    if not bio_id or not bio_text:
        return jsonify({'error': 'Invalid bio data'}), 400
    bio = Bios.query.get(bio_id)
    if not bio or bio.user_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404
    bio.bio = bio_text[:160]
    db.session.commit()
    return jsonify({'success': True})

@views.route('/delete-education', methods=['POST'])
@login_required
def delete_education():
    education_data = json.loads(request.data)
    education_id = education_data['educationId']
    education = Educations.query.get(education_id)
    if education and education.user_id == current_user.id:
        db.session.delete(education)
        db.session.commit()
    return jsonify({})

@views.route('/edit-education', methods=['POST'])
@login_required
def edit_education():
    data = json.loads(request.data or '{}')
    education_id = data.get('educationId')
    education = Educations.query.get(education_id)
    if not education or education.user_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404
    education.uni = (data.get('uni') or '').strip()
    education.location = (data.get('location') or '').strip()
    education.degree = (data.get('degree') or '').strip()
    education.start_year = (data.get('start_year') or '').strip()
    education.end_year = (data.get('end_year') or '').strip()
    db.session.commit()
    return jsonify({'success': True})

@views.route('/delete-experience', methods=['POST'])
@login_required
def delete_experience():
    experience_data = json.loads(request.data)
    experience_id = experience_data['experienceId']
    experience = Experiences.query.get(experience_id)
    if experience and experience.user_id == current_user.id:
        db.session.delete(experience)
        db.session.commit()
    return jsonify({})

@views.route('/edit-experience', methods=['POST'])
@login_required
def edit_experience():
    data = json.loads(request.data or '{}')
    experience_id = data.get('experienceId')
    experience = Experiences.query.get(experience_id)
    if not experience or experience.user_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404

    role = (data.get('role') or '').strip()
    comp = (data.get('comp') or '').strip()
    desc = (data.get('desc') or '').strip()
    start_date = (data.get('start_date') or '').strip()
    end_date = (data.get('end_date') or '').strip()

    ongoing = is_ongoing_experience(start_date, end_date)
    experience.role = role
    experience.comp = comp
    experience.desc = desc
    experience.start_date = start_date
    experience.end_date = None if ongoing else end_date
    experience.ongoing = ongoing
    db.session.commit()
    return jsonify({'success': True})

@views.route('/delete-project', methods=['POST'])
@login_required
def delete_project():
    project_data = json.loads(request.data)
    project_id = project_data['projectId']
    project = Projects.query.get(project_id)
    if project and project.user_id == current_user.id:
        db.session.delete(project)
        db.session.commit()
    return jsonify({})

@views.route('/edit-project', methods=['POST'])
@login_required
def edit_project():
    data = json.loads(request.data or '{}')
    project_id = data.get('projectId')
    project = Projects.query.get(project_id)
    if not project or project.user_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404
    project.proj = (data.get('proj') or '').strip()
    project.tool = (data.get('tool') or '').strip()
    project.desc = (data.get('desc') or '').strip()
    project.link = (data.get('link') or '').strip() or None
    db.session.commit()
    return jsonify({'success': True})

@views.route('/delete-skill', methods=['POST'])
@login_required
def delete_skill():
    skill = json.loads(request.data)
    skillId = skill['skillId']
    skill = Skills.query.get(skillId)
    if skill:
        if skill.user_id == current_user.id:
            db.session.delete(skill)
            db.session.commit()
    return jsonify({})

@views.route('/edit-skill', methods=['POST'])
@login_required
def edit_skill():
    data = json.loads(request.data or '{}')
    skill_id = data.get('skillId')
    skill = Skills.query.get(skill_id)
    if not skill or skill.user_id != current_user.id:
        return jsonify({'error': 'Not found'}), 404
    skill_text = (data.get('data') or '').strip()
    skill_group = (data.get('group') or '').strip()
    if not skill_text:
        return jsonify({'error': 'Skill cannot be empty'}), 400
    skill.data = skill_text[:50]
    skill.group = skill_group[:50] if skill_group else None
    db.session.commit()
    return jsonify({'success': True})

# Create a new resume (GET: show form, POST: save selections)
@views.route('/resume/create', methods=['GET', 'POST'])
@login_required
def create_resume():
    if request.method == 'POST':
        name = request.form.get('name')
        bio_ids = request.form.getlist('bios')
        education_ids = request.form.getlist('educations')
        experience_ids = request.form.getlist('experiences')
        project_ids = request.form.getlist('projects')
        selected_skill_groups = request.form.getlist('skill_groups')
        format = request.form.get('format', 'classic')
        resume = Resume(name=name, user_id=current_user.id, format=format)
        resume.bios = Bios.query.filter(Bios.id.in_(bio_ids)).all() if bio_ids else []
        resume.educations = Educations.query.filter(Educations.id.in_(education_ids)).all() if education_ids else []
        resume.experiences = Experiences.query.filter(Experiences.id.in_(experience_ids)).all() if experience_ids else []
        resume.projects = Projects.query.filter(Projects.id.in_(project_ids)).all() if project_ids else []
        # Select all skills from the selected groups
        resume.skills = Skills.query.filter(Skills.user_id == current_user.id, Skills.group.in_(selected_skill_groups)).all() if selected_skill_groups else []
        db.session.add(resume)
        db.session.commit()
        flash('Resume created!', category='success')
        return redirect(url_for('views.home'))
    # GET: show selection form - organize skills by group
    skills_by_group = {}
    for skill in current_user.skills:
        group = (skill.group or 'Other').strip()
        if group not in skills_by_group:
            skills_by_group[group] = []
        skills_by_group[group].append(skill)
    skills_by_group = dict(sorted(skills_by_group.items()))
    
    return render_template('resume_form.html',
        user=current_user,
        bios=current_user.bios,
        educations=current_user.educations,
        experiences=current_user.experiences,
        projects=current_user.projects,
        skills_by_group=skills_by_group,
        resume=None,
        selected_bio_ids=set(),
        selected_education_ids=set(),
        selected_experience_ids=set(),
        selected_project_ids=set(),
        selected_skill_groups=set(),
        selected_format_options=['classic']
    )

# Edit a resume
@views.route('/resume/<int:resume_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        resume.name = request.form.get('name')
        resume.format = request.form.get('format', 'classic')

        for bio in current_user.bios:
            bio_text = request.form.get(f'bio_text_{bio.id}')
            if bio_text is not None:
                bio.bio = bio_text.strip()

        for edu in current_user.educations:
            edu.uni = (request.form.get(f'edu_uni_{edu.id}') or edu.uni).strip()
            edu.degree = (request.form.get(f'edu_degree_{edu.id}') or edu.degree).strip()
            edu.location = (request.form.get(f'edu_location_{edu.id}') or edu.location).strip()
            edu.start_year = (request.form.get(f'edu_start_{edu.id}') or edu.start_year).strip()
            edu.end_year = (request.form.get(f'edu_end_{edu.id}') or edu.end_year).strip()

        for exp in current_user.experiences:
            exp.role = (request.form.get(f'exp_role_{exp.id}') or exp.role).strip()
            exp.comp = (request.form.get(f'exp_comp_{exp.id}') or exp.comp).strip()
            exp.desc = (request.form.get(f'exp_desc_{exp.id}') or exp.desc).strip()
            start_date = (request.form.get(f'exp_start_{exp.id}') or '').strip()
            end_date = (request.form.get(f'exp_end_{exp.id}') or '').strip()
            if start_date:
                exp.start_date = start_date
            exp.ongoing = is_ongoing_experience(start_date or exp.start_date, end_date)
            exp.end_date = None if exp.ongoing else (end_date if end_date else exp.end_date)

        for proj in current_user.projects:
            proj.proj = (request.form.get(f'proj_title_{proj.id}') or proj.proj).strip()
            proj.tool = (request.form.get(f'proj_tool_{proj.id}') or proj.tool).strip()
            proj.desc = (request.form.get(f'proj_desc_{proj.id}') or proj.desc).strip()
            proj.link = (request.form.get(f'proj_link_{proj.id}') or proj.link or '').strip() or None

        bio_ids = request.form.getlist('bios')
        education_ids = request.form.getlist('educations')
        experience_ids = request.form.getlist('experiences')
        project_ids = request.form.getlist('projects')
        selected_skill_groups = request.form.getlist('skill_groups')
        resume.bios = Bios.query.filter(Bios.id.in_(bio_ids)).all() if bio_ids else []
        resume.educations = Educations.query.filter(Educations.id.in_(education_ids)).all() if education_ids else []
        resume.experiences = Experiences.query.filter(Experiences.id.in_(experience_ids)).all() if experience_ids else []
        resume.projects = Projects.query.filter(Projects.id.in_(project_ids)).all() if project_ids else []
        # Select all skills from the selected groups
        resume.skills = Skills.query.filter(Skills.user_id == current_user.id, Skills.group.in_(selected_skill_groups)).all() if selected_skill_groups else []
        db.session.commit()
        flash('Resume updated!', category='success')
        return redirect(url_for('views.home'))
    # Organize skills by group
    skills_by_group = {}
    for skill in current_user.skills:
        group = (skill.group or 'Other').strip()
        if group not in skills_by_group:
            skills_by_group[group] = []
        skills_by_group[group].append(skill)
    skills_by_group = dict(sorted(skills_by_group.items()))
    
    # Determine which groups are selected in the current resume
    selected_skill_groups = {(item.group or 'Other').strip() for item in resume.skills}
    
    return render_template('resume_form.html',
        user=current_user,
        bios=current_user.bios,
        educations=current_user.educations,
        experiences=current_user.experiences,
        projects=current_user.projects,
        skills_by_group=skills_by_group,
        resume=resume,
        selected_bio_ids={item.id for item in resume.bios},
        selected_education_ids={item.id for item in resume.educations},
        selected_experience_ids={item.id for item in resume.experiences},
        selected_project_ids={item.id for item in resume.projects},
        selected_skill_groups=selected_skill_groups,
        selected_format_options=[resume.format] if resume.format else ['classic']
    )

# Delete a resume
@views.route('/resume/<int:resume_id>/delete', methods=['POST'])
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    db.session.delete(resume)
    db.session.commit()
    flash('Resume deleted!', category='success')
    return redirect(url_for('views.home'))

@views.route('/resume/<int:resume_id>/preview_pdf')
@login_required
def preview_resume_pdf(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    match getattr(resume, 'format', 'classic'):
        case 'modern':
            buffer = generate_modern_resume(resume)
        case 'classic' | _:
            buffer = generate_classic_resume(resume)
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, download_name=f"{resume.name}.pdf", mimetype='application/pdf')

@views.route('/resume/<int:resume_id>/download')
@login_required
def download_specific_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        abort(403)
    match getattr(resume, 'format', 'classic'):
        case 'modern':
            buffer = generate_modern_resume(resume)
        case 'classic' | _:
            buffer = generate_classic_resume(resume)
    return send_file(buffer, as_attachment=True, download_name=f"{resume.name}.pdf", mimetype='application/pdf')