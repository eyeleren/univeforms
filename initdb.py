from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.sqltypes import Boolean

from gendb import *

class Id():
    def __init__(self, user_id, survey_id, question_id, answer_id):
        self.user_id = user_id
        self.survey_id = survey_id
        self.question_id = question_id
        self.answer_id = answer_id

    def get_user_id(self):
        return self.user_id

    def get_survey_id(self):
        return self.survey_id

    def get_question_id(self):
        return self.question_id 

    def get_answer_id(self):
        return self.answer_id

    def increment_user_id(self):
        self.user_id += 1
        return self.user_id

    def increment_survey_id(self):
        self.survey_id += 1
        return self.survey_id

    def increment_question_id(self):
        self.question_id += 1
        return self.question_id

    def increment_answer_id(self):
        self.answer_id += 1
        return self.answer_id

Session = sessionmaker(bind=engine) #creazione della factory
session = Session()

user_id = session.query(User).count()
survey_id = session.query(Survey).count()
question_id = session.query(Question).count()
answer_id = session.query(Answer).count()

session.commit()

id_management = Id(user_id,survey_id,
                   question_id,answer_id)

def init_db():

    engine = create_engine ('sqlite:///database.db', echo = True)
    Session = sessionmaker(bind=engine)       # factory
    session = Session()

    users = [User(id=id_management.increment_user_id(), fullname='Mickey Mouse', email='Mickey@disney.com', password='pwd', role='base'),
             User(id=id_management.increment_user_id(), fullname='Donald Duck', email='Donald@disney.com', password='pwd', role='base'),
             User(id=id_management.increment_user_id(), fullname='Goofy Goof', email='Goofy@disney.com', password='pwd', role='base'),]

    surveys = [Survey(id=id_management.increment_survey_id(), title='Prova', user_id='1', isactive=False, recipients=[users[1]], respondents=[users[1]] )]

    questions = [Question(id=id_management.increment_question_id(), text='Quanti anni hai?', survey_id='1', type='Multiple'),
                 Question(id=id_management.increment_question_id(), text='Qual è il tuo film Preferito?', survey_id='1', type='Open')]

    multiples = [Multiple_choice_question(id='1', option_a='meno di 20', option_b='meno di 40', option_c='meno di 80', option_d='più di 80')]

    opens = [Open_question(id='2')]

    answers = [Answer(id=id_management.increment_answer_id(), question_id='1', answer='B', user_id='2'),
               Answer(id=id_management.increment_answer_id(), question_id='2', answer='The Suicide Squad - Missione Suicida', user_id='2')]

    session.add_all(users)
    session.add_all(surveys)
    session.add_all(questions)
    session.add_all(multiples)
    session.add_all(opens)
    session.add_all(answers)
    session.commit()