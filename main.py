from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# class Item(BaseModel):
#     name: str
#     description: str
#     price: float
#     tax: float

# @app.post("/items/")
# def create_item(item: Item) -> Item:
#     return item