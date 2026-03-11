import os
import sys
import unittest
import json
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Subject, Topic, Quiz
from config import Config

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    JWT_SECRET_KEY = 'test-secret'

class AnalyticsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create a test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()

        # Generate JWT token
        self.token = create_access_token(identity=str(self.user.id))
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_overview_no_data(self):
        response = self.client.get('/api/analytics/overview', headers=self.headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['avg_score'], 0)
        self.assertEqual(data['best_subject'], 'N/A')

    def test_overview_with_data(self):
        # Create subject, topic and quizzes
        subj = Subject(name='Math')
        db.session.add(subj)
        db.session.commit()
        
        topic = Topic(name='Algebra', subject_id=subj.id)
        db.session.add(topic)
        db.session.commit()
        
        q1 = Quiz(user_id=self.user.id, topic_id=topic.id, score=8, total_questions=10, quiz_data={})
        q2 = Quiz(user_id=self.user.id, topic_id=topic.id, score=9, total_questions=10, quiz_data={})
        db.session.add_all([q1, q2])
        db.session.commit()
        
        response = self.client.get('/api/analytics/overview', headers=self.headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['avg_score'], 85.0)
        self.assertEqual(data['best_subject'], 'Math')

    def test_timeline(self):
        subj = Subject(name='Math')
        db.session.add(subj)
        db.session.commit()
        
        topic = Topic(name='Algebra', subject_id=subj.id)
        db.session.add(topic)
        db.session.commit()
        
        # Quiz today
        q1 = Quiz(user_id=self.user.id, topic_id=topic.id, score=8, total_questions=10, quiz_data={}, created_at=datetime.now())
        # Quiz yesterday
        yesterday = datetime.now() - timedelta(days=1)
        q2 = Quiz(user_id=self.user.id, topic_id=topic.id, score=6, total_questions=10, quiz_data={}, created_at=yesterday)
        
        db.session.add_all([q1, q2])
        db.session.commit()
        
        response = self.client.get('/api/analytics/timeline', headers=self.headers)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        
        # Verify dates are in order (query uses order_by)
        self.assertTrue(data[0]['date'] <= data[1]['date'])

if __name__ == '__main__':
    unittest.main()
