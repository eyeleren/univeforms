from flask import Flask
from flask import render_template, request, redirect, url_for, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from gendb import *
from initdb import *

app = Flask(__name__)
engine = create_engine('sqlite:///database.db', echo=True)

Session = sessionmaker(bind=engine)  # creazione della factory
session = Session()

current_user_id = session.query(User).count()

if current_user_id == 0:
    init_db()

app.config['SECRET_KEY'] = 'bazinga'
login_manager = LoginManager()
login_manager.init_app(app)


def get_current_user_id():
    return current_user_id


def get_current_survey_id():
    return current_survey_id


def get_current_question_id():
    return current_question_id


@login_manager.user_loader  # attenzione a questo
def load_user(user_id):

    Session = sessionmaker(bind=engine)  # creazione della factory
    session = Session()

    user = session.query(User).filter_by(id=user_id).first()

    return user


@app.route('/')
def home():
    # current_user identifica l'utente attuale
    # utente anonimo prima dell'autenticazione
    if current_user.is_authenticated:
        return redirect(url_for('private'))
    return render_template('index.html')


@app.route('/signup_page')
def signup_page():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':

        Session = sessionmaker(bind=engine)  # creazione della factory
        session = Session()

        if session.query(User).filter_by(email=request.form['inputEmail']).count() != 0:
            return render_template('signup.html')
        elif request.form['inputPassword'] != request.form['ripetiPassword']:
            return render_template('signup.html')
        else:
            user_id = id_management.increment_user_id()
            new_user = User(id=user_id, fullname=request.form['inputFullname'], email=request.form['inputEmail'],
                            password=request.form['inputPassword'], role='base')
            session.add(new_user)
            session.commit()
            return render_template('LoginPage.html')


@app.route('/login_page')
def login_page():
    return render_template('LoginPage.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        Session = sessionmaker(bind=engine)  # creazione della factory
        session = Session()

        user = session.query(User).filter_by(
            email=request.form['inputEmail']).first()
        real_pwd = user.password

        if (real_pwd is not None):
            if request.form['inputPassword'] == real_pwd:
                login_user(user)  # chiamata a Flask-Login
                return redirect(url_for('private'))
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/private')
@login_required  # richiede autenticazione
def private():
    Session = sessionmaker(bind=engine)  # creazione della factory
    session = Session()

    active_surveys = session.query(Survey).filter_by(
        user_id=current_user.id).filter_by(isactive=True)
    surveys_concluded = session.query(Survey).filter_by(
        user_id=current_user.id).filter_by(isactive=False)
    session.commit()

    resp = make_response(render_template('UserPage.html', fullname=current_user.fullname, active_surveys=active_surveys,
                                         surveys_concluded=surveys_concluded))
    return resp


@app.route('/survey_page/<survey_id>')
def show_survey(survey_id):
    Session = sessionmaker(bind=engine)  # creazione della factory
    session = Session()

    Open_Q = []
    Multiple_Q = []

    survey = session.query(Survey).filter_by(id=survey_id).first()
    questions = session.query(Question).filter_by(survey_id=survey_id)
    for q in questions:
        if q.type == 'Open':
            Open_Q.append(q)
        else:
            answers = session.query(
                Multiple_choice_question).filter_by(id=q.id).first()
            Multiple_Q.append([q, answers])

    return render_template('SurveyPage.html', title=survey.title, Open_Q=Open_Q,
                           Multiple_Q=Multiple_Q)


@app.route('/newsurvey_page', methods=['POST'])
@login_required
def show_newsurvey():
    Num_Open_Q = int(request.form['Num_Open_Q'])
    Num_Multiple_Q = int(request.form['Num_Multiple_Q'])

    return render_template('NewSurvey.html', Num_Open_Q=Num_Open_Q,
                           Num_Multiple_Q=Num_Multiple_Q)


@app.route('/newsurvey', methods=['POST'])
@login_required
def newsurvey():

    Session = sessionmaker(bind=engine)  # creazione della factory
    session = Session()

    surveys = Survey(id=id_management.increment_survey_id(), title=request.form['survey_title'],
                     user_id=current_user.id, isactive=True)

    new_questions = []
    multiple_answers = []

    for elem in request.form:
        if 'Open_Q-' in elem:
            new_question = Question(id=id_management.increment_question_id(
            ), text=request.form[elem], survey_id=id_management.get_survey_id(), type='Open')
            new_questions.append(new_question)
            new_questions.append(Open_question(
                id=id_management.get_question_id()))
        elif 'Multiple_Q-' in elem:
            new_question = Question(id=id_management.increment_question_id(
            ), text=request.form[elem], survey_id=id_management.get_survey_id(), type='Multiple')
            new_questions.append(new_question)
        else:
            multiple_answers.append(request.form[elem])
            if 'Answer-D' in elem:
                new_question = Multiple_choice_question(id=id_management.get_question_id(), option_a=multiple_answers[0],
                                                        option_b=multiple_answers[1], option_c=multiple_answers[2], option_d=multiple_answers[3])
                new_questions.append(new_question)
                multiple_answers = []

    session.add(surveys)
    session.add_all(new_questions)
    session.commit()

    return redirect(url_for('private'))


@app.route('/logout')
@login_required  # richiede autenticazione
def logout():
    logout_user()  # chiamata a Flask-Login
    return redirect(url_for('home'))
