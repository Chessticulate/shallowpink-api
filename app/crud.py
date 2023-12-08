from app.models import db, User, Invitation
from app.config import CONFIG
from sqlalchemy.orm import Session
from sqlalchemy import select, insert
import bcrypt
import jwt

def hash_password(pswd: str) -> str:
    return bcrypt.hashpw(pswd, bcrypt.gensalt())
    
def check_password(pswd: str, pswd_hash: str) -> bool: 
     return bcrypt.checkpw(pswd, pswd_hash)

def get_user_by_name(name: str) -> User:    
    with Session(db.engine) as session:
        stmt = select(User).where(User.name == name)
        
        row = session.execute(stmt).first()
        return row if row is None else row[0]

def create_user(name: str, email: str, pswd: str): 
    hashed_pswd = hash_password(pswd) 
    with Session(db.engine) as session:
        stmt = insert(User).values(name=name, email=email, password=hashed_pswd)
        session.execute(stmt)
        session.commit()

def login(name: str, pswd: str) -> str:
    user = get_user_by_name(name)
    if user is None: 
        return None
    if not check_password(pswd, user.password):
        return None
    return jwt.encode({"user": name}, CONFIG.secret)

def invite(from_: str, to: str, game_type: str ="chess") -> str:
    from_user = get_user_by_name(from_)
    to_user = get_user_by_name(to)
    if from_user is None:
        return None
    if to_user is None: 
        return None
    with Session(db.engine) as session:
        invitation = Invitation(from_=from_user.id, to=to_user.id, game_type=game_type)
        session.add(invitation)
        session.commit()
        session.refresh(invitation)
        return invitation.id
 
def validate_token(token: str) -> bool:
    return jwt.decode(token, CONFIG.secret, CONFIG.algorithm)
      
