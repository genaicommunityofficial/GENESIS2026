
from fastapi import FastAPI

app = FastAPI(title="GENESIS 2026 API")


@app.get("/")
def health_check():
    return {"status": "GENESIS backend running"}
