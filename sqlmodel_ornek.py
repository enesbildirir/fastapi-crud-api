from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


class HeroBase(SQLModel):
    name: str
    secret_name: str
    age: int | None = Field(default=None, index=True)

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field()

class HeroCreate(HeroBase):
    password: str

class HeroPublic(HeroBase):
    id: int

class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    password: str | None = None

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"


connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_table():
    SQLModel.metadata.create_all(engine)

def hash_password(password: str) -> str:
    return f"not really hashed {password} hehehe"

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_table()

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(*, session: Session = Depends(get_session), hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100)
):
    
    heroes = session.exec(select(Hero)).offset(offset).limit(limit).all()
    return heroes

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(
    *,
    session: Session = Depends(get_session),
    hero_id: int
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.patch("/heroes/{hero_id}", response=HeroUpdate)
def update_hero(
    *,
    session: Session = Depends(get_session),
    hero_id: int,
    hero: HeroUpdate
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in hero_data:
        extra_data["hashed_password"] = hash_password(hero_data["password"])
    db_hero.sqlmodel_update(hero_data, update=extra_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@app.delete("/heroes/{hero_id}")
def delete_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}