from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Quiz, Topic, StudyPlan
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
import google.generativeai as genai
import json
from datetime import datetime

planner_bp = Blueprint('planner', __name__)

def get_gemini_model():
    genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
    return genai.GenerativeModel('gemini-1.5-flash')

@planner_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_plan():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'exam_date' not in data:
        return jsonify({'error': 'exam_date is required'}), 400
    
    exam_date_str = data['exam_date']
    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # 1. Identify weak topics (< 60% average score)
    weak_topics_query = db.session.query(
        Topic.name,
        func.sum(Quiz.score).label('total_correct'),
        func.sum(Quiz.total_questions).label('total_qs')
    ).join(Quiz, Quiz.topic_id == Topic.id)\
     .filter(Quiz.user_id == user_id)\
     .group_by(Topic.id)\
     .all()
    
    weak_topics = []
    for topic_name, total_correct, total_qs in weak_topics_query:
        if total_qs > 0:
            percentage = (total_correct / total_qs) * 100
            if percentage < 60:
                weak_topics.append(topic_name)
    
    if not weak_topics:
        # If no weak topics identified (maybe no quizzes taken or user is doing well), 
        # just use all topics associated with the user's subjects (or just random ones)
        # For now, let's just say we need some data.
        return jsonify({'message': 'No weak topics identified. Take more quizzes to generate a personalized plan!'}), 200

    # 2. Integrate Gemini API for plan generation
    model = get_gemini_model()
    
    prompt = f"""
    Create a personalized 7-day study plan for a student who has an upcoming exam on {exam_date_str}.
    The student is struggling with the following topics: {', '.join(weak_topics)}.
    
    The plan should be structured day-by-day (Day 1 to Day 7).
    Each day should include:
    - "focus": The main topic(s) to study
    - "activities": A list of specific study activities (e.g., "Review notes on X", "Practice 20 MCQs on Y")
    - "duration": Estimated Prep time (e.g., "3 hours")
    
    Return the response ONLY as a JSON object with a key "plan" which is a list of 7 objects.
    
    Format:
    {{
        "plan": [
            {{
                "day": 1,
                "focus": "...",
                "activities": ["...", "..."],
                "duration": "..."
            }},
            ...
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        plan_data = json.loads(response.text)
        
        # 3. Store in study_plans table
        new_plan = StudyPlan(
            user_id=user_id,
            plan_data=plan_data,
            exam_date=exam_date
        )
        db.session.add(new_plan)
        db.session.commit()
        
        return jsonify(new_plan.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@planner_bp.route('/latest', methods=['GET'])
@jwt_required()
def get_latest_plan():
    user_id = int(get_jwt_identity())
    plan = StudyPlan.query.filter_by(user_id=user_id).order_by(StudyPlan.created_at.desc()).first()
    if not plan:
        return jsonify({'message': 'No study plan found'}), 404
    return jsonify(plan.to_dict())
