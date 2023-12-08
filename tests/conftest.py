from app import db, models, crud, config
from sqlalchemy.orm import Session
from sqlalchemy import delete
from pytest import fixture

@fixture
def fake_app_secret():
    config.CONFIG.secret = "fake_secret"
    


@fixture
def drop_all_users():
    with Session(db.engine) as session:
        stmt = delete(models.User)
        session.execute(stmt)
        session.commit()
         

@fixture
def fake_user_data():
    return [        
        {"name": "fakeuser1", "password": "fakepswd1", "email": "fakeuser1@fakeemail.com"},
        {"name": "fakeuser2", "password": "fakepswd2", "email": "fakeuser2@fakeemail.com"},
        {"name": "fakeuser3", "password": "fakepswd3", "email": "fakeuser3@fakeemail.com"}
    ]

@fixture
def init_fake_user_data(fake_user_data, drop_all_users, fake_app_secret):
    
    with Session(db.engine) as session:
        for data in fake_user_data:
            pswd = crud.hash_password(data.pop("password"))
            user = models.User(**data, password=pswd)
            session.add(user)
        session.commit()




