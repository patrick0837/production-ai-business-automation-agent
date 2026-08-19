from fastapi import FastAPI

app = FastAPI(
    title="Production-Ready AI Business Automation Agent",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}