import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}:{}@{}/{}".format('postgres', '1234','localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {
            'question': 'How are you ?',
            'answer': 'fine thank you',
            'category': 'Science',
            'difficulty': 1
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
    
    def test_get_questions(self):
        res = self.client().get('/questions/')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['categories'])
    
    def test_404_errorhandler_if_page_does_not_exist(self):
        res = self.client().get('/questions/?page=10000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'],"resource not found")

    def test_delete_questions(self):

        new_question = Question(question="How are you ?",
        answer="fine thank you",
        category="Science",
        difficulty=1)

        new_question.insert()
        id = new_question.id

        res = self.client().delete('/questions/'+str(id))
        data = json.loads(res.data)

        question = Question.query.filter(Question.id == id).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['deleted'], id)
        self.assertEqual(question, None)
    
    def test_delete_not_exist_question(self):
        res = self.client().delete('/questions/10000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'],"unprocessable")

    def test_add_question(self):
        res = self.client().post('/questions' , json=self.new_question)
        data = json.loads(res.data)

        self.client().delete('/questions'+str(data['created_id']))

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_search_exist_term(self):
        res = self.client().post('/search', json={'searchTerm': "what"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])

    def test_search_not_exist_term(self):
        res = self.client().post('/search', json={'searchTerm': "##"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertFalse(data['questions'])
        self.assertFalse(data['total_questions'])
    
    def test_get_questions_by_category(self):
        res = self.client().get('/categories/1/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['total_questions'])
        self.assertEqual(data['current_category'], 1)
    
    def test_get_questions_by_not_exist_category(self):
        res = self.client().get('/categories/1000/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertFalse(data['questions'])
        self.assertFalse(data['total_questions'])
        self.assertEqual(data['current_category'], 1000)



# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()