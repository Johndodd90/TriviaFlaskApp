import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# Function to paginate questions


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions

# create and configure the app and CORS


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # Use the after_request decorator to set Access-Control-Allow
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    # Get Categories
    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        category = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'categories': category,
            'total_categories': len(categories)
        })

    # Get Questions
    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        category = {category.id: category.type for category in categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': category,
            'current_category': None
        })

    # DELETE Questions
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(selection)
            })
        except Exception:
            abort(400)

    # POST new question
    @app.route('/questions', methods=["POST"])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        print("new_question: " + str(new_question))
        print("new_answer: " + str(new_answer))
        print("new_category: " + str(new_category))
        print("new_difficulty: " + str(new_difficulty))

        try:
            question = Question(question=new_question, answer=new_answer,
                                category=new_category, difficulty=new_difficulty)  # noqa
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(selection)
            })
        except Exception:
            abort(422)

    # SEARCH Questions

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        try:
            body = request.get_json()
            keyword = body.get('searchTerm', None)
            search_term = '%{0}%'.format(keyword)
            selection = Question.query.order_by(Question.id).filter(
                Question.question.ilike(search_term))
            searched_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': searched_questions,
                'total_questions_in_search': len(searched_questions)
            })

        except Exception:
            abort(422)

    # GET questions by Category
    @app.route('/categories/<int:category_id>/questions')
    def retrieve_questions_from_category(category_id):
        try:
            questions = Question.query.filter(
                Question.category == category_id).all()

            if questions is None:
                abort(404)

            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions],
                'category': category_id,
                'total_questions': len(questions)
            })
        except Exception:
            abort(422)

    # Play the Quiz Game
    @app.route('/quizzes', methods=["POST"])
    def post_quizzes():
        try:
            data = request.get_json()
            category_id = int(data["quiz_category"]["id"])
            category = Category.query.get(category_id)
            previous_questions = data["previous_questions"]
            if not category == None:  # noqa
                if "previous_questions" in data and len(previous_questions) > 0:  # noqa
                    questions = Question.query.filter(
                        Question.id.notin_(previous_questions),
                        Question.category == category.id
                    ).all()
                else:
                    questions = Question.query.filter(
                        Question.category == category.id).all()
            else:
                if "previous_questions" in data and len(previous_questions) > 0:  # noqa
                    questions = Question.query.filter(
                        Question.id.notin_(previous_questions)
                    ).all()
                else:
                    questions = Question.query.all()
            max = len(questions) - 1
            if max > 0:
                question = questions[random.randint(0, max)].format()
            else:
                question = False
            return jsonify({
                "success": True,
                "question": question
            })
        except Exception:
            abort(500, "An error occured while trying to load the next question")  # noqa

    # ERROR HANDLERS

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "The server did not understand the request."
        }), 400

    @app.errorhandler(403)
    def Forbidden(error):
        return jsonify({
            "success": False,
            "error": 403,
            "message": "Access is forbidden to the requested page."
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(405)
    def Method_Not_Allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "The method specified in the request is not allowed."
        }), 405

    @app.errorhandler(408)
    def Request_Timeout(error):
        return jsonify({
            "success": False,
            "error": 408,
            "message": "The request took longer than the server was prepared to wait."  # noqa
        }), 408

    @app.errorhandler(410)
    def Gone(error):
        return jsonify({
            "success": False,
            "error": 410,
            "message": "The requested page is no longer available."  # noqa
        }), 410

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def Internal_Server_Error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "The request was not completed. The server met an unexpected condition."  # noqa
        }), 500

    return app
