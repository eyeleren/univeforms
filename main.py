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

if id_management.get_user_id() == 0:
    init_db()

app.config['SECRET_KEY'] = 'bazinga'
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader #attenzione a questo
def load_user(user_id):

    Session = sessionmaker(bind=engine) #creazione della factory
    session = Session()

    user = session.query(User).filter_by(id=user_id).one()

    return user

@app.route('/')
def home():
    #current_user identifica l'utente attuale
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
    
        Session = sessionmaker(bind=engine) #creazione della factory
        session = Session()

        if session.query(User).filter_by(email=request.form['inputEmail']).count() != 0:
            return render_template('signup.html')
        elif request.form['inputPassword'] != request.form['ripetiPassword']:
            return render_template('signup.html')
        else:
            user_id = id_management.increment_user_id()
            print(user_id)
            new_user = User(id=user_id,fullname=request.form['inputFullname'],email=request.form['inputEmail'], 
                            password=request.form['inputPassword'],role='base')
            session.add(new_user)
            session.commit()
            return render_template('LoginPage.html')

@app.route('/login_page')
def login_page():
    return render_template('LoginPage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        Session = sessionmaker(bind=engine) #creazione della factory
        session = Session()

        user = session.query(User).filter_by(email=request.form['inputEmail']).one()
        real_pwd = user.password

        if (real_pwd is not None):
            if request.form['inputPassword'] == real_pwd:
                login_user(user) #chiamata a Flask-Login
                return redirect(url_for('private'))
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/private')
@login_required #richiede autenticazione
def private():
    Session = sessionmaker(bind=engine) #creazione della factory
    session = Session()

    active_surveys = session.query(Survey).filter_by(user_id=current_user.id).filter_by(isactive=True)
    surveys_concluded = session.query(Survey).filter_by(user_id=current_user.id).filter_by(isactive=False)
    shared_surveys = session.query(Survey).filter(Survey.recipients.any(id=current_user.id)).all()
    session.commit()

    
    resp = make_response(render_template('UserPage.html',fullname=current_user.fullname, active_surveys=active_surveys, 
                                         surveys_concluded=surveys_concluded, shared_surveys=shared_surveys))
    return resp

@app.route('/survey_page/<survey_id>', methods=['GET', 'POST'])
def show_survey(survey_id):
    Session = sessionmaker(bind=engine) #creazione della factory
    session = Session()

    Open_Q = []
    Multiple_Q = []

    survey = session.query(Survey).filter_by(id=survey_id).first()
    questions = session.query(Question).filter_by(survey_id=survey_id)
    for q in questions:
        if q.type == 'Open':
            Open_Q.append(q)
        else:
            answers = session.query(Multiple_choice_question).filter_by(id=q.id).first()
            Multiple_Q.append([q, answers])

    respondent = session.query(User).filter(User.id==current_user.id).filter(User.completed_surveys.any(id=survey_id)).count() == 0
    report = session.query(Survey).filter(Survey.report.any(survey_id=survey_id)).first()
    report_id = report.id
    if int(current_user.id) == int(survey.user_id):
        return render_template('SurveyReportPage.html', title=survey.title, report_id=report_id)
    elif respondent:
        return render_template('SurveyCompilationPage.html', title=survey.title, report_id=report_id, Open_Q=Open_Q, 
                           Multiple_Q=Multiple_Q)
    else:
        Open_Q_A = []
        Multiple_Q_A = []
        for q in Open_Q:
            answer = session.query(Answer).filter_by(question_id=q.id).filter_by(user_id=current_user.id).first()
            Open_Q_A.append([q, answer])
        for q in Multiple_Q:
            answer = session.query(Answer).filter_by(question_id=q[0].id).filter_by(user_id=current_user.id).first()
            Multiple_Q_A.append([q, answer])
    
        return render_template('SurveyViewingPage.html', title=survey.title, Open_Q_A=Open_Q_A , 
                           Multiple_Q_A=Multiple_Q_A)

@app.route('/show_report/<report_id>', methods=['POST'])
@login_required
def show_report(report_id):

    class Filter():
        def __init__(self):
            self.user_id = True
            self.type = True
            self.keyword = True

        def is_accepted(self):
            return self.user_id & self.type & self.keyword

    report = session.query(Report).filter_by(id=report_id).one()
    statistics = {'n_answer': 0, 'n_O_A': 0, 'n_M_A': 0}
    result = []
    for answer in report.answers:
        answers_filter = Filter()
        for elem in request.form:
            if request.form[elem] != '':
                if 'user_email' in elem:
                    user_id = session.query(User).filter_by(email=request.form[elem]).one().id
                    answers_filter.user_id = (answer.user_id == user_id)
                elif 'user_fullname' in elem:
                    user_id = session.query(User.id).filter_by(fullname=request.form[elem]).one().id
                    answers_filter.user_id = (answer.user_id == user_id)
                elif 'type' in elem:
                    answers_filter.type = ((request.form[elem] == 'all') | (answer.question.type == request.form[elem]))
                elif 'Keyword' in elem:
                    answers_filter.keyword = (request.form[elem] in answer.answer)

        if answers_filter.is_accepted():
            statistics['n_answer']+=1
            if answer.question.type == 'Open':
                statistics['n_O_A']+=1
            else:
                statistics['n_M_A']+=1
            result.append(answer)

    title = report.survey.title
    return render_template('ResultsPage.html', title=title, result=result, statistics=statistics)

@app.route('/answer/<report_id>', methods=['POST'])
@login_required
def answer(report_id):
    answers = []
    for elem in request.form:
        val = ''
        for c in elem:
            if (ord(c)>=48) & (ord(c)<= 57):
                val += c
        question_id = int(val)
        answer = Answer(id=id_management.increment_answer_id(), question_id=question_id, answer=request.form[elem], user_id=current_user.id, report_id=report_id)
        answers.append(answer)

    session.add_all(answers)
    session.commit()

    return redirect(url_for('private'))

@app.route('/newsurvey_page', methods=['POST'])
@login_required
def show_newsurvey():
    Num_Open_Q = int(request.form['Num_Open_Q'])
    Num_Multiple_Q = int(request.form['Num_Multiple_Q'])

    return render_template('NewSurvey.html',Num_Open_Q=Num_Open_Q,
                            Num_Multiple_Q=Num_Multiple_Q)
    
@app.route('/newsurvey', methods=['POST'])
@login_required
def newsurvey():

    Session = sessionmaker(bind=engine) #creazione della factory
    session = Session()

    survey = Survey(id=id_management.increment_survey_id(), title=request.form['survey_title'], 
               user_id=current_user.id, isactive=True)

    report = Report(id=id_management.increment_report_id(), survey_id=id_management.get_survey_id())

    new_questions = []
    multiple_answers = []

    for elem in request.form:
        if request.form[elem] != '':
            if 'Open_Q-' in elem:
                new_question = Question(id=id_management.increment_question_id(), text=request.form[elem], survey_id=id_management.get_survey_id(), type='Open')
                new_questions.append(new_question)
                new_questions.append(Open_question(id=id_management.get_question_id()))
            elif 'Multiple_Q-' in elem:
                new_question = Question(id=id_management.increment_question_id(), text=request.form[elem], survey_id=id_management.get_survey_id(), type='Multiple')
                new_questions.append(new_question)
            elif 'Answer-' in elem:
                multiple_answers.append(request.form[elem])
                if 'Answer-D' in elem:
                    new_question = Multiple_choice_question(id=id_management.get_question_id(), option_a=multiple_answers[0], 
                    option_b=multiple_answers[1], option_c=multiple_answers[2], option_d=multiple_answers[3])
                    new_questions.append(new_question)
                    multiple_answers = []
            else:
                recipient = session.query(User).filter_by(email=request.form[elem]).first()
                survey.recipients = [recipient]

    session.add(survey)
    session.add(report)
    session.add_all(new_questions)
    session.commit()

    return redirect(url_for('private'))

@app.route('/logout')
@login_required # richiede autenticazione
def logout():
    logout_user() #chiamata a Flask-Login
    return redirect(url_for('home'))
