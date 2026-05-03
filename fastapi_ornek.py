from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Kullanici(BaseModel):
    name: str

kisiler = []

@app.post("/kullanici")
async def ekle(kisi: Kullanici):
    kisiler.append(kisi)
    return kisiler

@app.get("/kullanici")
async def listele():
    return kisiler

@app.get("/kullanici/{id}")
async def kisi_getir(id):
    return kisiler[int(id)]

@app.delete("/kullanici/{id}")
async def sil(id):
    return kisiler.pop(int(id))