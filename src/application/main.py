from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, auth

app = FastAPI(
    title="AIWA Backend",
    description="AI Workflow Automation Platform API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {
        "message": "Welcome to AIWA Backend!",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
