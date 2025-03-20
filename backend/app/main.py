import os
import uvicorn
from fastapi import FastAPI
from backend.app.router import EngineRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
