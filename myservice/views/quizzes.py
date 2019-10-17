from flakon import JsonBlueprint
from flask import request, jsonify, abort
from myservice.classes.quiz import Quiz, Question, Answer, NonExistingAnswerError, LostQuizError, CompletedQuizError

quizzes = JsonBlueprint('quizzes', __name__)

_LOADED_QUIZZES = {}  # list of available quizzes
_QUIZNUMBER = 0  # index of the last created quizzes

_WIN_MESSAGE = "you won 1 million clams!"
_COMPLETED_MESSAGE = "completed quiz"
_LOSE_MESSAGE = "you lost!"
_UNKNOWN_ANSWER_MESSAGE = "non-existing answer!"


@quizzes.route("/quizzes", methods=['GET', 'POST'])
def all_quizzes():
    if 'POST' == request.method:
        result = create_quiz(request)
    elif 'GET' == request.method:
        result = get_all_quizzes(request)
    return result


@quizzes.route("/quizzes/loaded", methods=['GET'])
def loaded_quizzes():  # returns the number of quizzes currently loaded in the system
    global _LOADED_QUIZZES

    return jsonify({"loaded_quizzes": len(_LOADED_QUIZZES)})


@quizzes.route("/quiz/<int:id>", methods=['GET', 'DELETE'])
def single_quiz(id):
    global _LOADED_QUIZZES
    id = str(id)

    exists_quiz(id)

    if 'GET' == request.method:
        result = _LOADED_QUIZZES[id].serialize()
    elif 'DELETE' == request.method:
        quiz = _LOADED_QUIZZES[id]
        del _LOADED_QUIZZES[id]
        result = {
            "answered_questions": quiz.currentQuestion,
            "total_questions": len(quiz.questions)
        }

    return jsonify(result)


@quizzes.route("/quiz/<int:id>/question", methods=['GET'])
def play_quiz(id):
    global _LOADED_QUIZZES, _COMPLETED_MESSAGE, _LOSE_MESSAGE
    id = str(id)

    exists_quiz(id)

    if 'GET' == request.method:  
        try:
            result = _LOADED_QUIZZES[id].getQuestion()
        except CompletedQuizError:
            result = {"msg": _COMPLETED_MESSAGE}
        except LostQuizError:
            result = {"msg": _LOSE_MESSAGE}

    return jsonify(result)


@quizzes.route("/quiz/<int:id>/question/<string:answer>", methods=['PUT'])
def answer_question(id, answer):
    global _LOADED_QUIZZES, _COMPLETED_MESSAGE, _LOSE_MESSAGE, _UNKNOWN_ANSWER_MESSAGE
    id = str(id)
    result = ""

    exists_quiz(id)
    quiz = _LOADED_QUIZZES[id]

    try:
        quiz.isOpen()
    except CompletedQuizError:
        result = _COMPLETED_MESSAGE
    except LostQuizError:
        result = _LOSE_MESSAGE

    if not result and 'PUT' == request.method:  
        # TODO: Check answers and handle exceptions
        try:
            result = quiz.checkAnswer(answer)
        except CompletedQuizError:
            result = _WIN_MESSAGE
        except LostQuizError:
            result = _LOSE_MESSAGE
        except NonExistingAnswerError:
            result = _UNKNOWN_ANSWER_MESSAGE

    return jsonify({'msg': result})

############################################
# USEFUL FUNCTIONS BELOW (use them, don't change them)
############################################

def create_quiz(request):
    global _LOADED_QUIZZES, _QUIZNUMBER

    json_data = request.get_json()
    qs = json_data['questions']
    questions = []
    for q in qs:
        question = q['question']
        answers = []
        for a in q['answers']:
            answers.append(Answer(a['answer'], a['correct']))
        question = Question(question, answers)
        questions.append(question)

    _LOADED_QUIZZES[str(_QUIZNUMBER)] = Quiz(_QUIZNUMBER, questions)
    _QUIZNUMBER += 1

    return jsonify({'quiznumber': _QUIZNUMBER - 1})


def get_all_quizzes(request):
    global _LOADED_QUIZZES

    return jsonify(loadedquizzes=[e.serialize() for e in _LOADED_QUIZZES.values()])


def exists_quiz(id):
    if int(id) > _QUIZNUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(id in _LOADED_QUIZZES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
