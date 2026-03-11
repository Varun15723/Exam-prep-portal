import pytest
import io

def test_create_topic(client, auth_headers):
    # Create subject first
    res = client.post('/api/subjects/', json={'name': 'Math'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    
    response = client.post('/api/subjects/topics', json={
        'name': 'Calculus',
        'subject_id': subject_id,
        'notes_text': 'Introduction to derivatives'
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()['name'] == 'Calculus'

def test_get_topics(client, auth_headers):
    res = client.post('/api/subjects/', json={'name': 'Math'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    client.post('/api/subjects/topics', json={'name': 'Calculus', 'subject_id': subject_id}, headers=auth_headers)
    
    response = client.get(f'/api/subjects/{subject_id}/topics', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()) >= 1

def test_upload_notes(client, auth_headers):
    res = client.post('/api/subjects/', json={'name': 'Math'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    res = client.post('/api/subjects/topics', json={'name': 'Calculus', 'subject_id': subject_id}, headers=auth_headers)
    topic_id = res.get_json()['id']
    
    data = {
        'file': (io.BytesIO(b"dummy pdf content"), 'test.pdf')
    }
    response = client.post(f'/api/subjects/topics/{topic_id}/upload', 
                           data=data, content_type='multipart/form-data', headers=auth_headers)
    
    assert response.status_code == 200
    assert 'notes_url' in response.get_json()
    assert response.get_json()['notes_url'].endswith('.pdf')

def test_delete_topic(client, auth_headers):
    res = client.post('/api/subjects/', json={'name': 'Math'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    res = client.post('/api/subjects/topics', json={'name': 'To Delete', 'subject_id': subject_id}, headers=auth_headers)
    topic_id = res.get_json()['id']
    
    response = client.delete(f'/api/subjects/topics/{topic_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Topic deleted'
