from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.pages import router as pages_router

app = FastAPI(title="Smart Campus Market")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages_router)
