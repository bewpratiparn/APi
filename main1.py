from sqlalchemy import Column, Integer, String, DateTime, func, LargeBinary
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from databases import Database
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import FastAPI, File, UploadFile
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from . import crud, models, schemas


logging.basicConfig(level=logging.INFO)

DATABASE_URL = "postgresql://postgres:12345@localhost/Project"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

Base = declarative_base()


class User_info(Base):
    __tablename__ = "User_info"

    id = Column(Integer, primary_key=True, index=True)
    Fristname = Column(String, index=True)
    Lastname = Column(String, index=True)
    Phone = Column(String, index=True)


class Account(Base):
    __tablename__ = "Account"

    Account_id = Column(Integer, primary_key=True,
                        index=True, autoincrement=True)
    Username = Column(String, index=True)
    Password = Column(String)
    Registed = Column(DateTime, server_default=func.now())


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    shop_open_close = Column(String)
    shop_maplink = Column(String)
    shop_name = Column(String, index=True)
    shop_dis = Column(String)


class Food(Base):
    __tablename__ = "Food_info"

    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String, index=True)
    food_pic = Column(String)
    food_price = Column(String)


class Meat_Data(Base):
    __tablename__ = "Meat_Data"

    id = Column(Integer, primary_key=True, index=True)
    meat_name = Column(String, index=True)


Base.metadata.create_all(bind=engine)

app = FastAPI()

database = Database(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# OAuth2 password bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User registration


@app.post("/register/")
async def register(
    Fristname: str, Lastname: str, Phone: str,
    Username: str, Password: str, db: Session = Depends(get_db)
):
    hashed_password = pwd_context.hash(Password)
    db_user = User_info(
        Fristname=Fristname, Lastname=Lastname, Phone=Phone,
    )

    db_account = Account(
        Username=Username, Password=hashed_password,
    )
    db.add(db_user)
    db.add(db_account)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "username": db_account.Username}


@app.get("/User_info/{user_id}")
async def read_item(User_info_id: int, db: Session = Depends(get_db)):
    item = db.query(User_info).filter(User_info.id == User_info_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/user/delete/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User_info).filter(User_info.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

# User login


@app.post("/Login/")
async def login(Username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(Account).filter(Account.Username == Username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": Username, "token_type": "bearer"}


@app.post("/shops/register/")
async def register_shop(
    shop_name: str, shop_dis: str, shop_open_close: str, shop_maplink: str, db: Session = Depends(get_db)
):
    db_shop = Shop(
        shop_name=shop_name,
        shop_dis=shop_dis,
        shop_open_close=shop_open_close,
        shop_maplink=shop_maplink
    )
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    return {"id": db_shop.id, "shop_name": db_shop.shop_name}


@app.get("/shops/{shop_id}")
async def read_item(Shop_id: int, db: Session = Depends(get_db)):
    item = db.query(Shop_id).filter(Shop.id == Shop_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/food/")
async def create_food(food_name: str, food_pic: str, food_price: str, db: Database = Depends(get_db)):
    query = Food.insert().values(food_name=food_name,
                                 food_pic=food_pic, food_price=food_price)
    last_record_id = await db.execute(query)
    return {"food_id": last_record_id}


@app.get("/food/{food_id}")
async def read_food(food_id: int, db: Database = Depends(get_db)):
    query = Food.select().where(Food.c.id == food_id)
    result = await db.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Food not found")
    return result


@app.post("/meat_data/")
def create_meat_data(meat_name: str, db: Session = Depends(get_db)):
    db_meat = Meat_Data(meat_name=meat_name)
    db.add(db_meat)
    db.commit()
    db.refresh(db_meat)
    return db_meat


@app.get("/protected/")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "This is a protected route"}


@app.on_event("startup")
async def startup_event():
    logging.info("Connecting to the database...")
    await database.connect()
    logging.info("Connected to the database.")

# Print information about closing the database connection during shutdown


@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Closing the database connection.")
    await database.disconnect()
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
