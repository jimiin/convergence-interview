from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def get_application() -> FastAPI:
    app = FastAPI()
    print("FastAPI application initalised successfully.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    return app


application = get_application()
