from fastapi import FastAPI
from backend.app.router import EngineRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()

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
