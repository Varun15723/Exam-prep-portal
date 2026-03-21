import pytest
import json

def test_quiz_lifecycle(client, auth_headers, mock_genai):
    # 1. Create a subject and topic
    res = client.post('/api/subjects/', json={'name': 'Science', 'description': 'Science subject'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    
    res = client.post('/api/subjects/topics', json={
        'name': 'Photosynthesis', 
        'subject_id': subject_id, 
        'notes_text': 'Plants use sunlight to make food.'
    }, headers=auth_headers)
    topic_id = res.get_json()['id']

    # 2. Generate Quiz
    # Note: mock_genai in conftest.py will provide a response
    # However, let's override the return value for this specific test if needed, 
    # but the default mock response in conftest should suffice for basic flow.
    # We need to make sure the mock returns some questions.
    
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "questions": [
            {
                "question": "What do plants use to make food?",
                "options": ["Sunlight", "Pizza", "Rocks", "Music"],
                "answer": "Sunlight",
                "explanation": "Photosynthesis process."
            }
        ]
    })
    mock_genai.generate_content.return_value = mock_response
    
    response = client.post('/api/quiz/generate', json={"topic_id": topic_id}, headers=auth_headers)
    assert response.status_code == 200
    quiz_data = response.get_json()
    assert 'questions' in quiz_data
    assert len(quiz_data['questions']) > 0

    # 3. Submit Quiz
    questions = quiz_data['questions']
    for q in questions:
        q['user_answer'] = q['answer'] # Correct answer
        
    submit_res = client.post('/api/quiz/submit', json={
        "topic_id": topic_id,
        "questions": questions
    }, headers=auth_headers)
    
    assert submit_res.status_code == 201
    assert submit_res.get_json()['score'] == 1
    
    # 4. Check History
    history_res = client.get('/api/quiz/history', headers=auth_headers)
    assert history_res.status_code == 200
    assert len(history_res.get_json()) >= 1
