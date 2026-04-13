# run_api.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from app.api.endpoints.router import router
from app.api.endpoints.upload import task_queue
from app.core.sqlite_db import init_db
from app.core.chroma_db import init_chroma, close_chroma

# from app.api.endpoints.analysis import (
#     router as analysis_router,
# )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------------------------
    # STARTUP
    # ----------------------------
    try:
        init_db()
        print("SQLite initialized")

        init_chroma()
        print("ChromaDB initialized")

        yield

    finally:
        # ----------------------------
        # SHUTDOWN
        # ----------------------------
        try:
            # Signal queue worker to stop gracefully
            task_queue.put(None)
            task_queue.join()
            print("Queue worker stopped")

        except Exception as e:
            print(f"Queue shutdown error: {e}")

        try:
            close_chroma()
            print("ChromaDB closed")

        except Exception as e:
            print(f"Chroma shutdown error: {e}")

        print("Application shutdown complete")


app = FastAPI(title="Wealth Advisor AI", lifespan=lifespan)

# router.include_router(analysis_router, prefix="/v1")

app.include_router(router, prefix="/v1")


def main():
    config = uvicorn.Config(
        "run_api:app", host="127.0.0.1", port=8081, reload=True, log_level="info"
    )

    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("Server stopped gracefully.")
