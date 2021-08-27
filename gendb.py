from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Table, Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.sqltypes import Boolean


from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user

engine = create_engine ('sqlite:///database.db', echo = True)
Base = declarative_base()                   

users_surveys = Table('users_surveys', Base.metadata,
                      Column('user_id', ForeignKey('Users.id'), primary_key=True),
                      Column('survey_id', ForeignKey('Surveys.id'), primary_key=True))

recipients_shared_surveys = Table('recipients_shared_surveys', Base.metadata,
                                        Column('recipient_id', ForeignKey('Users.id'), primary_key=True),
                                        Column('shared_survey_id', ForeignKey('Surveys.id'), primary_key=True))

class User(Base, UserMixin):
    __tablename__ = 'Users'
    
    id = Column(Integer, primary_key=True)
    fullname = Column(String)
    email = Column(String, primary_key=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)       #due ruoli possibili base - administrator

    def __repr__(self):
        return "<Users(id='%s', fullname='%s', email='%s', password='%s', role='%s')>" % (self.id, self.fullname, self.email, self.password, self.role)
    
class Survey(Base):
    __tablename__ = 'Surveys'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    user_id = Column(String, ForeignKey(User.id), nullable=False)
    isactive = Column(Boolean, nullable=False)
    
    maker = relationship(User, back_populates='published_surveys') #qui viene sfruttata la Foreign Key
    recipients = relationship(User, secondary=recipients_shared_surveys, back_populates='shared_surveys')
    respondents = relationship(User, secondary=users_surveys, back_populates='completed_surveys') 

    def __repr__(self):
        return "<Survey(id='%s', title='%s', user_id='%s', isactive='%s')>" % (self.id, self.title, self.user_id, self.isactive)
    
User.published_surveys = relationship(Survey, order_by=Survey.id, back_populates='maker', cascade='all, delete, delete-orphan')
User.shared_surveys = relationship(Survey, secondary=recipients_shared_surveys, back_populates='recipients')
User.completed_surveys =  relationship(Survey, secondary=users_surveys, back_populates='respondents')

class Question(Base):
    __tablename__ = 'Questions'
    
    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    survey_id = Column(String, ForeignKey(Survey.id), nullable=False)
    type = Column(String, nullable=False) # Multiple - Open

    survey = relationship(Survey, back_populates='questions') #qui viene sfruttata la Foreign Key
    
Survey.questions = relationship(Question, order_by=Question.id, back_populates='survey', cascade='all, delete, delete-orphan')

class Multiple_choice_question(Base):
    __tablename__ = 'Multiple_choice_questions'
    id = Column(String, ForeignKey(Question.id), primary_key=True)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    
    question = relationship(Question,uselist=False)

class Open_question(Base):
    __tablename__ = 'Open_questions'
    id = Column(String, ForeignKey(Question.id), primary_key=True)

    question = relationship(Question,uselist=False)

class Report(Base):
    __tablename__ = 'Reports'
    id = Column(Integer, primary_key=True)
    survey_id = Column(String, ForeignKey(Survey.id), nullable=False)

    survey = relationship(Survey, back_populates='report')

Survey.report = relationship(Report, back_populates='survey')

class Answer(Base):
    __tablename__ = 'Answers'
    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey(Question.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    report_id = Column(Integer, ForeignKey(Report.id), nullable=False)
    answer = Column(String, nullable=False)
    
    report = relationship(Report, back_populates='answers')
    question = relationship(Question, back_populates='answers') #qui viene sfruttata la Foreign Key
    user = relationship(User, back_populates='answers') #qui viene sfruttata la Foreign Key

User.answers = relationship(Answer, order_by=Answer.id, back_populates='user', cascade='all, delete, delete-orphan')
Question.answers = relationship(Answer, order_by=Answer.id, back_populates='question', cascade='all, delete, delete-orphan')
Report.answers = relationship(Answer, order_by=Answer.id, back_populates='report')

Base.metadata.create_all(engine)



