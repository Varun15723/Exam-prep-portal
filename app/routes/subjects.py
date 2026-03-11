import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Subject, Topic

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

subjects_bp = Blueprint('subjects', __name__)

# --- Subject Routes ---

@subjects_bp.route('/', methods=['GET'])
def get_subjects():
    subjects = Subject.query.all()
    return jsonify([s.to_dict() for s in subjects])

@subjects_bp.route('/', methods=['POST'])
def create_subject():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    subject = Subject(name=data['name'], description=data.get('description', ''))
    db.session.add(subject)
    db.session.commit()
    return jsonify(subject.to_dict()), 201

@subjects_bp.route('/<int:id>', methods=['GET'])
def get_subject(id):
    subject = Subject.query.get_or_404(id)
    return jsonify(subject.to_dict())

@subjects_bp.route('/<int:id>', methods=['PUT'])
def update_subject(id):
    subject = Subject.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        subject.name = data['name']
    if 'description' in data:
        subject.description = data['description']
        
    db.session.commit()
    return jsonify(subject.to_dict())

@subjects_bp.route('/<int:id>', methods=['DELETE'])
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    return jsonify({'message': 'Subject deleted'})

# --- Topic Routes ---

@subjects_bp.route('/<int:subject_id>/topics', methods=['GET'])
def get_topics(subject_id):
    topics = Topic.query.filter_by(subject_id=subject_id).all()
    return jsonify([t.to_dict() for t in topics])

@subjects_bp.route('/topics', methods=['POST'])
def create_topic():
    data = request.get_json()
    if not data or 'name' not in data or 'subject_id' not in data:
        return jsonify({'error': 'Name and subject_id are required'}), 400
    
    topic = Topic(
        name=data['name'], 
        subject_id=data['subject_id'], 
        notes_text=data.get('notes_text', '')
    )
    db.session.add(topic)
    db.session.commit()
    return jsonify(topic.to_dict()), 201

@subjects_bp.route('/topics/<int:id>', methods=['PUT'])
def update_topic(id):
    topic = Topic.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        topic.name = data['name']
    if 'notes_text' in data:
        topic.notes_text = data['notes_text']
    if 'subject_id' in data:
        topic.subject_id = data['subject_id']
        
    db.session.commit()
    return jsonify(topic.to_dict())

@subjects_bp.route('/topics/<int:id>', methods=['DELETE'])
def delete_topic(id):
    topic = Topic.query.get_or_404(id)
    db.session.delete(topic)
    db.session.commit()
    return jsonify({'message': 'Topic deleted'})
@subjects_bp.route('/topics/<int:id>/upload', methods=['POST'])
def upload_topic_notes(id):
    topic = Topic.query.get_or_404(id)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"topic_{id}_{file.filename}")
        
        # Ensure the subfolder exists
        notes_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'notes')
        if not os.path.exists(notes_dir):
            os.makedirs(notes_dir)
            
        file_path = os.path.join(notes_dir, filename)
        file.save(file_path)
        
        # Update topic in database
        topic.notes_url = f"/static/uploads/notes/{filename}"
        db.session.commit()
        
        return jsonify(topic.to_dict())
    
    return jsonify({'error': 'File type not allowed'}), 400
