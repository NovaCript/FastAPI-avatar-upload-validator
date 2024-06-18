import os
import shutil
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse

IMAGEDIR = "images/"

app = FastAPI()


# Загрузка изображения
@app.post("/")
async def upload_photo(username: str, file: UploadFile = File(...)):
    user_dir = os.path.join(IMAGEDIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    if file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size is too large")

    if len(os.listdir(user_dir)) >= 3:
        raise HTTPException(status_code=400, detail="Too many files")

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="File type is not image")

    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"file_name": file.filename}


# Удаление изображения
@app.delete("/")
async def delete_photo(username: str, file_name: str):
    file_path = os.path.join(IMAGEDIR, username, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)
    return {"message": "File deleted"}


# Получение списка изображений
@app.get("/photos/{username}", response_model=List[str])
async def get_photos(username: str):
    user_dir = os.path.join(IMAGEDIR, username)

    if not os.path.exists(user_dir):
        raise HTTPException(status_code=404, detail="User not found")

    files = os.listdir(user_dir)
    image_files = [file for file in files if
                   file.lower().endswith(('png', 'jpg', 'jpeg', 'gif'))]

    if not image_files:
        raise HTTPException(status_code=404, detail="No images found")
#   image_paths = [os.path.join(user_dir, file).replace("\\", "/") for file in image_files]
    image_paths = [os.path.join(user_dir, file) for file in image_files]
    return JSONResponse(content=image_paths)


# Получение отдельного изображения
@app.get("/photo/{username}/{file_name}")
async def get_photo(username: str, file_name: str):
    file_path = os.path.join(IMAGEDIR, username, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)
