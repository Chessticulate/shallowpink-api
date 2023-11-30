from app import db, schemas, models
from fastapi import FastAPI

chess_app = FastAPI()


@chess_app.post("/invite")
def create_invite(invite: schemas.CreateInvite):
    return {"message": "OK"}

