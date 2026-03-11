from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Topic, ChatHistory
import google.generativeai as genai
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

chatbot_bp = Blueprint('chatbot', __name__)

def get_gemini_model():
    genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
    return genai.GenerativeModel('gemini-1.5-flash')

@chatbot_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_tutor():
    data = request.get_json()
    if not data or 'topic_id' not in data or 'question' not in data:
        return jsonify({'error': 'topic_id and question are required'}), 400
    
    topic_id = data['topic_id']
    question = data['question']
    user_id = int(get_jwt_identity())
    
    topic = Topic.query.get_or_404(topic_id)
    
    if not topic.notes_text:
        return jsonify({'error': 'Topic has no notes to provide context'}), 400

    model = get_gemini_model()
    
    prompt = f"""
    You are an AI tutor helping a student with the topic: {topic.name}.
    Use the following notes as context to answer the student's question.
    
    Context Notes:
    {topic.notes_text}
    
    Student's Question:
    {question}
    
    Provide a clear, helpful, and concise answer. If the answer is not in the notes, use your general knowledge but mention it's outside the provided notes.
    """
    
    try:
        response = model.generate_content(prompt)
        answer = response.text
        
        # Save to chat history
        chat_entry = ChatHistory(
            user_id=user_id,
            topic_id=topic_id,
            question=question,
            answer=answer
        )
        db.session.add(chat_entry)
        db.session.commit()
        
        return jsonify({
            'answer': answer,
            'topic_id': topic_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    user_id = int(get_jwt_identity())
    topic_id = request.args.get('topic_id', type=int)
    
    query = ChatHistory.query.filter_by(user_id=user_id)
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    
    history = query.order_by(ChatHistory.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in history]), 200
