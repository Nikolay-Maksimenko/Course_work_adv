from sqlalchemy import Integer, String, Column, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import settings
Base = declarative_base()

engine = create_engine(settings.db_setting)
Session = sessionmaker(bind=engine)
session = Session()

class VKinderUser(Base):
    __tablename__ = 'vkinder_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vk_id = Column(Integer, nullable=False, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    age = Column(String)
    city_id = Column(Integer)
    city_title = Column(String)

class DatingUser(Base):
    __tablename__ = 'dating_user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vk_id = Column(Integer, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(String)
    user_id = Column(Integer, ForeignKey('vkinder_user.vk_id'), nullable=False)

class Photos(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, nullable=False)
    photo_id = Column(Integer, nullable=False)
    url = Column(String, nullable=False)

class BlackList(Base):
    __tablename__ = 'black_list'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vkinder_id = Column(Integer, nullable=False)
    couple_id = Column(Integer, nullable=False)

class WhiteList(Base):
    __tablename__ = 'white_list'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vkinder_id = Column(Integer, nullable=False)
    couple_id = Column(Integer, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    url = Column(String, nullable=False)

def create_tables():
    engine.connect().execute("""drop table dating_user, vkinder_user, photos;""")
    Base.metadata.create_all(engine)
