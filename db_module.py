from sqlalchemy import Integer, String, Date, Boolean, Column, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import os
Base = declarative_base()
s = os.getenv('BD_USER')
engine = create_engine(f'postgresql://{os.getenv("BD_USER")}:{os.getenv("BD_PWD")}@localhost:5432/vkinder')
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
    url = Column(String, nullable=False, unique=True)

def create_tables():
    engine.connect().execute("""drop table dating_user, vkinder_user, photos;""")
    Base.metadata.create_all(engine)

create_tables()