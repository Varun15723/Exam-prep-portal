from flask import Blueprint, jsonify
from app import db
from app.models import Quiz, Topic, Subject
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    user_id = int(get_jwt_identity())
    
    # 1. Average Score
    # Formula: (sum of scores / sum of total_questions) * 100
    stats = db.session.query(
        func.sum(Quiz.score).label('total_score'),
        func.sum(Quiz.total_questions).label('total_questions')
    ).filter(Quiz.user_id == user_id).first()
    
    avg_score = 0
    if stats and stats.total_questions and stats.total_questions > 0:
        avg_score = round((stats.total_score / stats.total_questions) * 100, 2)
    
    # 2. Best Subject
    # Join Quiz -> Topic -> Subject, group by Subject name, calculate avg percentage
    best_subject_query = db.session.query(
        Subject.name,
        func.sum(Quiz.score).label('subject_score'),
        func.sum(Quiz.total_questions).label('subject_total')
    ).join(Topic, Quiz.topic_id == Topic.id)\
     .join(Subject, Topic.subject_id == Subject.id)\
     .filter(Quiz.user_id == user_id)\
     .group_by(Subject.name)\
     .all()
    
    best_subject = "N/A"
    max_avg = -1
    
    for row in best_subject_query:
        if row.subject_total > 0:
            avg = (row.subject_score / row.subject_total) * 100
            if avg > max_avg:
                max_avg = avg
                best_subject = row.name
                
    return jsonify({
        'avg_score': avg_score,
        'best_subject': best_subject
    })

@analytics_bp.route('/timeline', methods=['GET'])
@jwt_required()
def get_timeline():
    user_id = int(get_jwt_identity())
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Group by date(created_at) and calculate avg percentage per day
    timeline_query = db.session.query(
        func.date(Quiz.created_at).label('quiz_date'),
        func.sum(Quiz.score).label('daily_score'),
        func.sum(Quiz.total_questions).label('daily_total')
    ).filter(Quiz.user_id == user_id, Quiz.created_at >= thirty_days_ago)\
     .group_by(func.date(Quiz.created_at))\
     .order_by(func.date(Quiz.created_at))\
     .all()
    
    timeline = []
    for row in timeline_query:
        if row.daily_total > 0:
            timeline.append({
                'date': str(row.quiz_date),
                'score': round((row.daily_score / row.daily_total) * 100, 2)
            })
            
    return jsonify(timeline)

@analytics_bp.route('/subject-performance', methods=['GET'])
@jwt_required()
def get_subject_performance():
    user_id = int(get_jwt_identity())
    
    # Group by Subject name and calculate avg percentage
    perf_query = db.session.query(
        Subject.name,
        func.sum(Quiz.score).label('subject_score'),
        func.sum(Quiz.total_questions).label('subject_total')
    ).join(Topic, Quiz.topic_id == Topic.id)\
     .join(Subject, Topic.subject_id == Subject.id)\
     .filter(Quiz.user_id == user_id)\
     .group_by(Subject.name)\
     .all()
    
    performance = []
    for row in perf_query:
        if row.subject_total > 0:
            performance.append({
                'subject': row.name,
                'score': round((row.subject_score / row.subject_total) * 100, 2)
            })
            
    return jsonify(performance)
