from fastapi import FastAPI
from routes.subdomain_router import router as subdomain_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the subdomain processing routes
app.include_router(subdomain_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)