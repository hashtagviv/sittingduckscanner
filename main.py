from fastapi import FastAPI
from routes.subdomain_router import router as subdomain_router
import uvicorn

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
]

# Include the subdomain processing routes
app.include_router(subdomain_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)