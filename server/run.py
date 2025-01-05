from api.server import settings


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.server:app", host="0.0.0.0", port=8000, reload=settings.ENV == "dev"
    )
