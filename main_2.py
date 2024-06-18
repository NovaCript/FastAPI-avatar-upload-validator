import aiofiles
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import List


IMAGEDIR = Path("images")

app = FastAPI()


@app.post("/")
async def upload_photo(username: str, file: UploadFile = File(...)):
    user_dir = IMAGEDIR / username
    user_dir.mkdir(parents=True, exist_ok=True)

    if file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size is too large")

    if len(list(user_dir.iterdir())) >= 3:
        raise HTTPException(status_code=400, detail="Too many files")

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="File type is not image")

    file_path = user_dir / file.filename
    async with aiofiles.open(file_path, "wb") as buffer:
        while content := await file.read(1024):
            await buffer.write(content)

    return {"file_name": file.filename}


@app.delete("/")
async def delete_photo(username: str, file_name: str):
    file_path = IMAGEDIR / username / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_path.unlink()
    return {"message": "File deleted"}


@app.get("/photos/{username}", response_model=List[str])
async def get_photos(username: str):
    user_dir = IMAGEDIR / username

    if not user_dir.exists():
        raise HTTPException(status_code=404, detail="User not found")

    image_files = [str(file) for file in user_dir.iterdir() if
                   file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']]

    if not image_files:
        raise HTTPException(status_code=404, detail="No images found")

    image_paths = [file.replace("\\", "/") for file in image_files]
    return JSONResponse(content=image_paths)


@app.get("/photo/{username}/{file_name}")
async def get_photo(username: str, file_name: str):
    file_path = IMAGEDIR / username / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(str(file_path))
