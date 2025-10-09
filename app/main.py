from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.database import engine
from app.models import Base
from app.api import courses, lessons, words, users, telegram_auth
from pathlib import Path


# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Telegram Spaced Repetition Mini App",
    description="A Telegram Mini App for learning words using spaced repetition",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(courses.router, prefix="/api/v1")
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(words.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(telegram_auth.router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serves the Telegram Mini App"""
    try:
        # Try to serve the index.html from static directory
        static_dir = Path("app/static")
        index_file = static_dir / "index.html"

        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            # If no static file, return error message
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Spaced Repetition Learning</title>
            </head>
            <body>
                <div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;">
                    <h1>⚠️ Frontend Not Found</h1>
                    <p>The frontend files are missing. Please ensure app/static/index.html exists.</p>
                    <p>API documentation is available at <a href="/docs">/docs</a></p>
                </div>
            </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(content=f"Error loading frontend: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Not found", "detail": "The requested resource was not found"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "An internal error occurred"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)