from fastapi.openapi.utils import status_code_ranges
import os
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Header
from sqlmodel import Field, Session, SQLModel, create_engine, select
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    age: int | None = Field(default=None)

class UserCreate(SQLModel):
    name: str
    email: str
    age: int | None = None

class Soru(SQLModel):
    metin: str

def get_session():
    with Session(engine) as session:
        yield session

def api_key_dogrula(api_key: str = Header()):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Geçersiz API key")

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

def create_db_and_table():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_table()

@app.post("/kullanici", response_model=User)
def create_user(*, session: Session = Depends(get_session), dep = Depends(api_key_dogrula), user: UserCreate):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/kullanici", response_model=list[User])
def listele(*, session: Session = Depends(get_session), dep = Depends(api_key_dogrula), offset: int = 0, limit: int = Query(default=100, le=100)):
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users

@app.get("/kullanici/{id}")
def getir(*, session: Session = Depends(get_session), id: int, dep = Depends(api_key_dogrula)):
    user = session.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/kullanici/{id}")
def sil(*, session: Session = Depends(get_session), id: int, dep = Depends(api_key_dogrula)):
    user = session.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    hatalar = []
    for hata in exc.errors():
        alan = str(hata["loc"][-1])
        mesaj = hata["msg"]
        hatalar.append(f"{alan}: {mesaj}")
    return JSONResponse(
        status_code=400,
        content={"hatalar": hatalar}
    )

@app.post("/soru")
def soru(soru: Soru, dep = Depends(api_key_dogrula)):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Sen bir finansal analistsin. Kullanıcının sorularını borsa ve finans perspektifinden yanıtla. "},
            {"role": "user", "content": soru.metin}
        ]
    )
    cevap = response.choices[0].message.content
    return {"cevap": cevap}