from fastapi import HTTPException
from fastapi import HTTPException, Path
from sqlalchemy import Column, Integer, String, DateTime, func, LargeBinary ,Numeric, Float
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from databases import Database
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import os
from fastapi import File, UploadFile
import base64
import uuid
from datetime import datetime
from jose import JWTError, jwt
import re
import json
from fastapi.middleware.cors import CORSMiddleware
import requests


logging.basicConfig(level=logging.INFO)

DATABASE_URL = "postgresql://postgres:1234@localhost/Project"

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

    Account_id = Column(Integer, primary_key=True,index=True, autoincrement=True)
    Username = Column(String, index=True)
    Password = Column(String)
    Registed = Column(DateTime, server_default=func.now())


class shop(Base):
    __tablename__ = "shops"

    shop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shop_open_close = Column(String, index=True)
    shop_maplink = Column(String, index=True)
    shop_name = Column(String, index=True)
    shop_dis = Column(String, index=True)
    shop_pic = Column(String, index=True)


class food(Base):
    __tablename__ = "Food_Info"

    food_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    food_name = Column(String, index=True)
    food_pic = Column(String, index=True)
    food_price = Column(Numeric)


class Meat_Data(Base):
    __tablename__ = "Meat_Data"

    meat_id = Column(Integer, primary_key=True, index=True)
    meat_name = Column(String, index=True)


class Veget_data(Base):
    __tablename__ = "Veget_data"
    veget_id = Column(Integer, primary_key=True, index=True)
    veget_name = Column(String, index=True)


class seasoning(Base):
    __tablename__ = "seasoning"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
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


@app.put("/user/update/{user_id}")
async def update_user(
    user_id: int,
    Fristname: str = None,
    Lastname: str = None,
    Phone: str = None,
    Username: str = None,
    Password: str = None,
    db: Session = Depends(get_db)
):
    # ดึงข้อมูลผู้ใช้จากฐานข้อมูล
    db_user = db.query(User_info).filter(User_info.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # อัปเดตข้อมูลผู้ใช้หากมีค่าใหม่ที่กำหนด
    if Fristname is not None:
        db_user.Fristname = Fristname
    if Lastname is not None:
        db_user.Lastname = Lastname
    if Phone is not None:
        db_user.Phone = Phone

    # อัปเดตข้อมูลบัญชีผู้ใช้หากมีค่าใหม่ที่กำหนด
    if Username is not None:
        db_account = db.query(Account).filter(Account.Account_id == db_user.id).first()
        if not db_account:
            raise HTTPException(status_code=404, detail="Account not found")
        db_account.Username = Username
    if Password is not None:
        hashed_password = pwd_context.hash(Password)
        db_account.Password = hashed_password

    # ยืนยันการเปลี่ยนแปลงกับฐานข้อมูล
    db.commit()
    db.refresh(db_user)

    return {"id": db_user.id, "Fristname": db_user.Fristname, "Username": db_account.Username}


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
async def login(Username: str, Password: str, db: Session = Depends(get_db)):

    user = db.query(Account).filter(Account.Username == Username).first()
    if not user or not pwd_context.verify(Password, user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": Username, "token_type": "bearer"}


@app.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    # In a real application, you might want to add some additional logic here,
    # like blacklisting the token or logging the user out from the application.
    return {"message": "Logout successful"}


@app.post("/shops/register/")
async def register_shop(
    shop_name: str, shop_dis: str, shop_open_close: str,
    shop_maplink: str, shop_picture: UploadFile = File(...), db: Session = Depends(get_db)
):
    # ให้ใช้ UUID สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
    file_name = f"{str(uuid.uuid4())}_{shop_picture.filename}"
    file_path = f"uploads/{file_name}"
    os.makedirs("uploads", exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(await shop_picture.read())

    db_shop = shop(
        shop_name=shop_name,
        shop_dis=shop_dis,
        shop_open_close=shop_open_close,
        shop_maplink=shop_maplink,
        shop_pic=file_path
    )

    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    return {"id": db_shop.shop_id, "shop_name": db_shop.shop_name}


@app.put("/shops/update/{shop_id}")
async def update_shop(
    shop_id: int,
    shop_name: str = None,
    shop_dis: str = None,
    shop_open_close: str = None,
    shop_maplink: str = None,
    shop_picture: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Retrieve the shop from the database
    db_shop = db.query(shop).filter(shop.shop_id == shop_id).first()

    if not db_shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Update the shop data if new values are provided
    if shop_name is not None:
        db_shop.shop_name = shop_name
    if shop_dis is not None:
        db_shop.shop_dis = shop_dis
    if shop_open_close is not None:
        db_shop.shop_open_close = shop_open_close
    if shop_maplink is not None:
        db_shop.shop_maplink = shop_maplink

    # Update the shop picture if a new file is provided
    if shop_picture:
        file_name = f"{str(uuid.uuid4())}_{shop_picture.filename}"
        file_path = f"uploads/{file_name}"
        os.makedirs("uploads", exist_ok=True)

        with open(file_path, "wb") as file:
            file.write(await shop_picture.read())

        db_shop.shop_pic = file_path

    # Commit the changes to the database
    db.commit()
    db.refresh(db_shop)

    return {"id": db_shop.shop_id, "shop_name": db_shop.shop_name}

@app.get("/shops/{shop_id}")
async def read_item(shop_id: int, db: Session = Depends(get_db)):
    item = db.query(shop).filter(shop.shop_id == shop_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.delete("/shop/delete/{shop_id}")
async def delete_shop(shop_id: int, db: Session = Depends(get_db)):
    db_shop = db.query(shop).filter(shop.shop_id == shop_id).first()
    if not db_shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(db_shop)
    db.commit()
    return {"message": "User deleted successfully"}

@app.post("/food/")
async def create_food(
    food_name: str, food_price: str ,food_pic: UploadFile = File(...), db: Session = Depends(get_db)
):
    # Save the uploaded file to a folder (e.g., 'uploads')
    file_name = f"{str(uuid.uuid4())}_{food_pic.filename}"
    file_path = f"uploads/{file_name}"
    os.makedirs("uploads", exist_ok=True)

    with open(file_path, "wb") as file:
        file.write(await food_pic.read())

    # Create a new Food instance and add it to the database
    db_food = food(
        food_name=food_name,
        food_price=food_price,
        food_pic=file_path
    )

    db.add(db_food)
    db.commit()
    db.refresh(db_food)

    return {"id": db_food.food_id, "food_name": db_food.food_name}


@app.put("/foods/update/{food_id}")
async def update_food(
    food_id: int,
    food_name: str = None,
    food_price: float = None,
    food_picture: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Retrieve the food from the database
    db_food = db.query(food).filter(food.food_id == food_id).first()

    if not db_food:
        raise HTTPException(status_code=404, detail="Food not found")

    # Update the food data if new values are provided
    if food_name is not None:
        db_food.food_name = food_name
    if food_price is not None:
        db_food.food_price = food_price

    # Update the food picture if a new file is provided
    if food_picture:
        file_name = f"{str(uuid.uuid4())}_{food_picture.filename}"
        file_path = f"uploads/{file_name}"
        os.makedirs("uploads", exist_ok=True)

        with open(file_path, "wb") as file:
            file.write(await food_picture.read())

        db_food.food_pic = file_path

    # Commit the changes to the database
    try:
        db.commit()
        db.refresh(db_food)
        return {"id": db_food.food_id, "food_name": db_food.food_name}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update food: {str(e)}")


@app.get("/food/{food_id}")
async def read_item(food_id: int, db: Session = Depends(get_db)):
    item = db.query(food).filter(food.food_id == food_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/foods/delete/{food_id}")
async def delete_food(food_id: int, db: Session = Depends(get_db)):
 
    # Retrieve the food from the database
    db_food = db.query(food).filter(food.food_id == food_id).first()

    if not db_food:
        raise HTTPException(status_code=404, detail="Food not found")

    try:
        # Delete the food from the database
        db.delete(db_food)
        db.commit()
        return {"message": "Food deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete food: {str(e)}")


@app.post("/meat_data/")
def create_meat_data(meat_name: str, db: Session = Depends(get_db)):
    db_meat = Meat_Data(meat_name=meat_name)
    db.add(db_meat)
    db.commit()
    db.refresh(db_meat)
    return db_meat




@app.put("/meat/update/{meat_id}")
async def update_meat(
    meat_id: int,
    meat_name: str = None,
    db: Session = Depends(get_db)
):
    # Retrieve the meat from the database
    db_meat = db.query(Meat_Data).filter(Meat_Data.meat_id == meat_id).first()
    if not db_meat:
        raise HTTPException(status_code=404, detail="Meat not found")

    # Update the meat data if new values are provided
    if meat_name is not None:
        db_meat.meat_name = meat_name

    # Commit the changes to the database
    db.commit()
    db.refresh(db_meat)

    return {"id": db_meat.meat_id, "meat_name": db_meat.meat_name}


@app.delete("/meat_data/delete/{meat_id}")
async def delete_meat(meat_id: int, db: Session = Depends(get_db)):
    db_meat = db.query(Meat_Data).filter(Meat_Data.meat_id == meat_id).first()
    if not db_meat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(db_meat)
    db.commit()
    return {"message": "User deleted successfully"}

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
    


