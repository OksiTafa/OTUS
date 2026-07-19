from fastapi import FastAPI
import uvicorn
from fastapi.staticfiles import StaticFiles
from routers.main_page import router as main_page_router
from routers.catalog_story import router as stories_router
from routers.story_detail import router as story_detail


app = FastAPI()
app.include_router(main_page_router, tags=["Main page"])
app.include_router(stories_router, tags=["catalog"], prefix="/catalog")
app.include_router(story_detail, tags=["story"], prefix="/story")

# Подключение статических файлов
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/src", StaticFiles(directory="src"), name="src")
app.mount("/scripts", StaticFiles(directory="scripts"), name="scripts")

if __name__ == '__main__':
    uvicorn.run('app:app', host='127.0.0.1', port=8000, reload=True)
