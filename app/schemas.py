from pydantic import BaseModel

class Reservation(BaseModel):
    name: str
    date: str
    time: str
    type: str
