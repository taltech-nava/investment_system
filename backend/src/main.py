from fastapi import FastAPI
from routes.fetch import router as fetch_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(fetch_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)