from app import db, models
from sqlalchemy.orm import Session
from sqlalchemy import select, insert
from pytest import fixture

@fixture
def fake_user_data():
    return [        
        {"name": "fakeuser1", "password": "fakepswd1", "email": "fakeuser1@fakeemail.com"},
        {"name": "fakeuser2", "password": "fakepswd2", "email": "fakeuser2@fakeemail.com"},
        {"name": "fakeuser3", "password": "fakepswd3", "email": "fakeuser3@fakeemail.com"}
    ]

@fixture
def init_fake_user_data(fake_user_data):
    with Session(db.engine) as session:
        for data in fake_user_data:
            user = models.User(**data)
            session.add(user)
        session.commit()




