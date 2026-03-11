from flask import Blueprint, request, jsonify
from app import db
from app.models import Topic, Quiz
import google.generativeai as genai
from flask import current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

quiz_bp = Blueprint('quiz', __name__)

def get_gemini_model():
    genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
    return genai.GenerativeModel('gemini-1.5-flash')

@quiz_bp.route('/generate', methods=['POST'])
def generate_quiz():
    data = request.get_json()
    if not data or 'topic_id' not in data:
        return jsonify({'error': 'topic_id is required'}), 400
    
    topic = Topic.query.get_or_404(data['topic_id'])
    
    if not topic.notes_text:
        return jsonify({'error': 'Topic has no notes to generate quiz from'}), 400

    model = get_gemini_model()
    
    prompt = f"""
    Generate 10 multiple-choice questions (MCQs) based on the following text:
    
    {topic.notes_text}
    
    Return the response ONLY as a JSON object with a key "questions" which is a list of objects.
    Each object should have:
    - "question": The question text
    - "options": A list of 4 possible answers
    - "answer": The correct answer (must be one of the options)
    - "explanation": A brief explanation of why the answer is correct
    
    Format:
    {{
        "questions": [
            {{
                "question": "...",
                "options": ["...", "...", "...", "..."],
                "answer": "...",
                "explanation": "..."
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
        
        quiz_data = json.loads(response.text)
        return jsonify(quiz_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quiz_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_quiz():
    data = request.get_json()
    if not data or 'topic_id' not in data or 'questions' not in data:
        return jsonify({'error': 'topic_id and questions are required'}), 400
    
    user_id = int(get_jwt_identity())
    topic_id = data['topic_id']
    questions = data['questions'] # List of {question, options, answer, user_answer, explanation}
    
    score = 0
    total_questions = len(questions)
    
    for q in questions:
        if q.get('user_answer') == q.get('answer'):
            score += 1
            
    quiz_attempt = Quiz(
        user_id=user_id,
        topic_id=topic_id,
        score=score,
        total_questions=total_questions,
        quiz_data=questions
    )
    
    db.session.add(quiz_attempt)
    db.session.commit()
    
    return jsonify({
        'message': 'Quiz submitted successfully',
        'score': score,
        'total_questions': total_questions,
        'results': questions
    }), 201

@quiz_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    quizzes = Quiz.query.filter_by(user_id=user_id).order_by(Quiz.created_at.desc()).all()
    return jsonify([q.to_dict() for q in quizzes])
