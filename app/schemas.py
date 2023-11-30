from pydantic import BaseModel

class CreateInvite(BaseModel):
    to: str
    game_type: str

