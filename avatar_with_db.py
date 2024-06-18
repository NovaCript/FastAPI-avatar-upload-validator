import aiofiles
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, \
    select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

DATABASE_URL = "sqlite:///./test.db"  # Замените на URL вашей базы данных
IMAGEDIR = Path("images")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    avatars = relationship("Avatar", back_populates="user")


class Avatar(Base):
    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="avatars")


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/create-user/")
async def create_user(username: str, db: Session = Depends(get_db)):
    user = User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Создание директории для аватарок пользователя
    user_dir = IMAGEDIR / username
    user_dir.mkdir(parents=True, exist_ok=True)

    return {"message": "User created", "user_id": user.id}


@app.post("/upload-avatar/")
async def upload_avatar(username: str, file: UploadFile = File(...),
                        db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dir = IMAGEDIR / username

    if file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size is too large")

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="File type is not image")

    if len(list(user_dir.iterdir())) >= 3:
        raise HTTPException(status_code=400, detail="Too many files")


    file_path = user_dir / file.filename
    async with aiofiles.open(file_path, "wb") as buffer:
        while content := await file.read(1024):
            await buffer.write(content)

    avatar = Avatar(filename=str(file_path), user_id=user.id)
    db.add(avatar)
    db.commit()

    return {"file_name": file.filename}


@app.delete("/delete-avatar/")
async def delete_avatar(username: str, file_name: str,
                        db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    avatar = db.execute(select(Avatar).where(Avatar.user_id == user.id,
                                             Avatar.filename == file_name)).scalar_one_or_none()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    file_path = Path(avatar.filename)
    if file_path.exists():
        file_path.unlink()

    db.delete(avatar)
    db.commit()

    return {"message": "Avatar deleted"}


@app.get("/photos/{username}", response_model=List[str])
async def get_photos(username: str, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    avatars = db.execute(
        select(Avatar).where(Avatar.user_id == user.id)).scalars().all()
    image_paths = [avatar.filename.replace("\\", "/") for avatar in avatars]

    if not image_paths:
        raise HTTPException(status_code=404, detail="No images found")

    return JSONResponse(content=image_paths)


@app.get("/photo/{username}/{file_name}")
async def get_photo(username: str, file_name: str):
    file_path = IMAGEDIR / username / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(str(file_path))
