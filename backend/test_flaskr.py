import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    # This class represents the trivia test case

    def setUp(self):
        # Define test variables and initialize app.
        self.app = create_app()
        self.client = self.app.test_client
        self.database_path = "postgresql://postgres:123456@localhost:5432/trivia"  # noqa
        setup_db(self.app, self.database_path)

        self.new_question = {
            'question': 'What is my name?',
            'answer': 'John',
            'category': 1,
            'difficulty': 1
        }

        self.quiz_data = {
            'previous_questions': [],
            'quiz_category': {
                'type': 'Art',
                'id': '2'
            }
        }

        self.quiz_data_missing_values = {
            'previous_questions': []
            # missing quiz_category
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        # Executed after reach test
        pass

    # Tests

    def test_get_categories(self):
        response = self.client().get('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertEqual(data['total_categories'], 6)

    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))

    def test_404_sent_request_beyond_valid_page(self):
        res = self.client().get('/questions?page=1000', json={'difficulty': 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

# DELETE Questions
    def test_delete_question(self):
        res = self.client().delete('/questions/1')
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == 1).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], 1)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertEqual(question, None)

    def test_delete_question_id_does_not_exist(self):
        res = self.client().delete('/questions/99999')
        data = json.loads(res.data)
        question = Question.query.filter(Question.id == 99999).one_or_none()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(
            data['message'], 'The server did not understand the request.')

    # POST new question
    def test_create_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])
        self.assertTrue(len(data['questions']))

    def test_405_if_question_creation_not_allowed(self):
        res = self.client().post('/questions/44', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(
            data['message'],
            'The method specified in the request is not allowed.')

    # SEARCH Questions with results
    def test_get_question_search_with_results(self):
        res = self.client().post('/questions/search',
                                 json={'searchTerm': 'artist'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['total_questions_in_search'])
        self.assertEqual(len(data['questions']), 2)

    # SEARCH Questions without results
    def test_get_question_search_without_results(self):
        res = self.client().post('/questions/search',
                                 json={'searchTerm': 'PotterHead'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['total_questions_in_search'], 0)
        self.assertEqual(len(data['questions']), 0)

    def test_get_questions_by_catgeory(self):
        res = self.client().get('/categories/2/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['category'])
        self.assertEqual(data['total_questions'], 4)

    def test_get_questions_by_invalid_catgeory(self):
        res = self.client().get('/categories/invalidId/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_quiz_question(self):

        res = self.client().post('/quizzes', json=self.quiz_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])

    def test_quiz_question_missing_data(self):

        res = self.client().post('/questions',
                                 json=self.quiz_data_missing_values)
        data = json.loads(res.data)

        # missing data is handled with default data so will not return error
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
