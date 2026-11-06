from fastapi import FastAPI

app = FastAPI(
    title="AWS Cloud Engineering Lab",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "service": "aws-cloud-lab-api",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
