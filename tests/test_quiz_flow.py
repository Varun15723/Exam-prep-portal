import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_quiz_flow():
    # 1. Register/Login
    username = "testuser_quiz"
    email = "testquiz@example.com"
    password = "password123"
    
    # Try login first, if fails register
    login_data = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        register_data = {"username": username, "email": email, "password": password}
        requests.post(f"{BASE_URL}/auth/register", json=register_data)
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
    token = response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in, token received.")

    # 2. Get a topic ID (assuming at least one exists)
    # If not, create one
    subjects_res = requests.get(f"{BASE_URL}/subjects/")
    subjects = subjects_res.json()
    
    if not subjects:
        # Create a subject and topic for testing if none exist
        subj_res = requests.post(f"{BASE_URL}/subjects/", json={"name": "Test Science", "description": "Test Subj"})
        subj_id = subj_res.json().get('id')
        topic_res = requests.post(f"{BASE_URL}/subjects/topics", json={"name": "Photosynthesis", "subject_id": subj_id, "notes_text": "Plants use sunlight to make food. This is photosynthesis."})
        topic_id = topic_res.json().get('id')
    else:
        topic_id = None
        for s in subjects:
            # Find the first topic
            t_res = requests.get(f"{BASE_URL}/subjects/{s['id']}/topics")
            topics = t_res.json()
            if topics:
                topic_id = topics[0]['id']
                break
        
        if not topic_id:
            subj_id = subjects[0]['id']
            topic_res = requests.post(f"{BASE_URL}/subjects/topics", json={"name": "Photosynthesis", "subject_id": subj_id, "notes_text": "Plants use sunlight to make food. This is photosynthesis."})
            topic_id = topic_res.json().get('id')

    print(f"Using Topic ID: {topic_id}")

    # 3. Generate Quiz
    print("Generating quiz...")
    gen_res = requests.post(f"{BASE_URL}/quiz/generate", json={"topic_id": topic_id})
    if gen_res.status_code != 200:
        print(f"Failed to generate quiz: {gen_res.text}")
        return
    
    quiz_questions = gen_res.json().get('questions', [])
    print(f"Generated {len(quiz_questions)} questions.")
    if quiz_questions:
        print(f"Sample explanation from first question: {quiz_questions[0].get('explanation')}")

    # 4. Submit Quiz
    # Simulate user answers
    for q in quiz_questions:
        q['user_answer'] = q['answer'] # Cheat to get full score
    
    print("Submitting quiz...")
    submit_res = requests.post(f"{BASE_URL}/quiz/submit", json={
        "topic_id": topic_id,
        "questions": quiz_questions
    }, headers=headers)
    
    print(f"Submit Response: {submit_res.status_code}")
    print(f"Score: {submit_res.json().get('score')}/{submit_res.json().get('total_questions')}")

    # 5. Check History
    print("Fetching history...")
    his_res = requests.get(f"{BASE_URL}/quiz/history", headers=headers)
    history = his_res.json()
    print(f"History count: {len(history)}")
    if history:
        print(f"Latest quiz score: {history[0]['score']}")

if __name__ == "__main__":
    test_quiz_flow()
