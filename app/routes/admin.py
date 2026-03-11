from flask import Blueprint, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Quiz, db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def faculty_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        if not user or user.role != 'faculty':
            return jsonify({'message': 'Faculty access required'}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@admin_bp.route('/reports', methods=['GET'])
@faculty_required
def get_reports():
    # Fetch all students and their performance
    students = User.query.filter_by(role='student').all()
    reports = []
    
    for s in students:
        # Get average score and total quizzes
        stats = db.session.query(
            func.avg(Quiz.score).label('avg_score'),
            func.count(Quiz.id).label('total_quizzes')
        ).filter(Quiz.user_id == s.id).first()
        
        reports.append({
            'username': s.username,
            'email': s.email,
            'avg_score': round(float(stats.avg_score or 0), 1),
            'total_quizzes': stats.total_quizzes
        })
    
    return jsonify(reports), 200

# Template route
@admin_bp.route('/')
def admin_page():
    return render_template('admin.html')
