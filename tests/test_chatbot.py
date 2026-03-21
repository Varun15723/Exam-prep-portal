import pytest
import json
from unittest.mock import MagicMock

def test_chatbot_ask(client, auth_headers, mock_genai):
    # 1. Create a subject and topic with notes
    res = client.post('/api/subjects/', json={'name': 'History', 'description': 'History subject'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    
    res = client.post('/api/subjects/topics', json={
        'name': 'French Revolution', 
        'subject_id': subject_id, 
        'notes_text': 'The French Revolution began in 1789.'
    }, headers=auth_headers)
    topic_id = res.get_json()['id']

    # 2. Ask a question
    mock_response = MagicMock()
    mock_response.text = "The French Revolution started in 1789 due to social and economic inequalities."
    mock_genai.generate_content.return_value = mock_response
    
    response = client.post('/api/chatbot/ask', json={
        "topic_id": topic_id,
        "question": "When did the French Revolution start?"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'answer' in data
    assert "1789" in data['answer']

    # 3. Check History
    history_res = client.get(f'/api/chatbot/history?topic_id={topic_id}', headers=auth_headers)
    assert history_res.status_code == 200
    history = history_res.get_json()
    assert len(history) == 1
    assert history[0]['question'] == "When did the French Revolution start?"
