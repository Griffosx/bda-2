from fastapi import FastAPI

app = FastAPI(
    title="Dice API",
    description="API for Dice",
    version="1.0.0",
)


@app.get("/")
async def ping():
    return "Pong"
