import pytest

def test_create_subject(client, auth_headers):
    response = client.post('/api/subjects/', json={
        'name': 'Math',
        'description': 'Mathematics subject'
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()['name'] == 'Math'

def test_get_subjects(client, auth_headers):
    client.post('/api/subjects/', json={'name': 'Math'}, headers=auth_headers)
    response = client.get('/api/subjects/', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.get_json()) >= 1

def test_get_subject(client, auth_headers):
    res = client.post('/api/subjects/', json={'name': 'Physics'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    
    response = client.get(f'/api/subjects/{subject_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == 'Physics'

def test_update_subject(client, auth_headers):
    res = client.post('/api/subjects/', json={'name': 'Old Name'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    
    response = client.put(f'/api/subjects/{subject_id}', json={'name': 'New Name'}, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == 'New Name'

def test_delete_subject(client, auth_headers):
    res = client.post('/api/subjects/', json={'name': 'To Delete'}, headers=auth_headers)
    subject_id = res.get_json()['id']
    
    response = client.delete(f'/api/subjects/{subject_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Subject deleted'
