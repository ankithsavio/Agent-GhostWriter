import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.router import EngineRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Remove files before shutdown
    """
    yield
    try:
        items = os.listdir("backend/uploads")
        for item in items:
            item_path = os.path.join("backend/uploads", item)
            if os.path.isfile(item_path):
                os.remove(item_path)

    except FileNotFoundError:
        print("Error uploads dir not found")


app = FastAPI(lifespan=lifespan)

app.include_router(EngineRouter().router)

origins = [os.getenv("FRONTEND_URL", "http://localhost:3000")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
