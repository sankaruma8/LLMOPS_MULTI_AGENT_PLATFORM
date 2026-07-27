import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("APP_PORT", "8000")))
    workers = int(os.getenv("APP_WORKERS", "1"))

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers
    )
