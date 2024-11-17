from fastapi import FastAPI

app = FastAPI()


@app.post("/test")
async def root():
    return {"message": "Hello World"}


