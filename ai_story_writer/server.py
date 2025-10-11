from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_story_writer.setup import setup
from ai_story_writer.routes import chapters_router, stories_router, models_router


setup()
app = FastAPI()
app.include_router(chapters_router)
app.include_router(models_router)
app.include_router(stories_router)

origins = ['http://localhost:4000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
