from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import engine
from app.models import Base
from app.api import courses, lessons, words, users, reviews, telegram_auth


# Create database tables
Base.metadata.create_all(bind=engine)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

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
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(telegram_auth.router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - Welcome page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request):
    """Courses list page - authentication happens via JavaScript"""
    return templates.TemplateResponse("courses.html", {
        "request": request,
        "courses": []
    })


@app.get("/courses/create", response_class=HTMLResponse)
async def create_course_page(
    request: Request
):
    """Create course page"""
    return templates.TemplateResponse("create_course.html", {
        "request": request
    })


@app.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_detail_page(course_id: int, request: Request):
    """Course detail page with lessons - data loaded via JavaScript"""
    return templates.TemplateResponse("course_details.html", {
        "request": request,
        "course_id": course_id
    })


@app.get("/courses/{course_id}/lessons/create", response_class=HTMLResponse)
async def create_lesson_page(
    course_id: int,
    request: Request
):
    """Create lesson page"""
    return templates.TemplateResponse("create_lesson.html", {
        "request": request,
        "course_id": course_id
    })


@app.get("/lessons/{lesson_id}", response_class=HTMLResponse)
async def lesson_detail_page(lesson_id: int, request: Request):
    """Lesson detail page with words - data loaded via JavaScript"""
    return templates.TemplateResponse("lesson_details.html", {
        "request": request,
        "lesson_id": lesson_id
    })


@app.get("/lessons/{lesson_id}/words/create", response_class=HTMLResponse)
async def create_word_page(
    lesson_id: int,
    request: Request
):
    """Create word page"""
    return templates.TemplateResponse("create_word.html", {
        "request": request,
        "lesson_id": lesson_id
    })


@app.get("/study/{lesson_id}", response_class=HTMLResponse)
async def study_page(
    lesson_id: int,
    request: Request
):
    """Study session page - data loaded via JavaScript"""
    return templates.TemplateResponse("study.html", {
        "request": request,
        "lesson_id": lesson_id
    })


@app.get("/lessons/{lesson_id}/complete", response_class=HTMLResponse)
async def completion_page(
    lesson_id: int,
    request: Request
):
    """Lesson completion page - data loaded via JavaScript"""
    return templates.TemplateResponse("completion.html", {
        "request": request,
        "lesson_id": lesson_id
    })


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(
    request: Request
):
    """Stats page - data loaded via JavaScript"""
    return templates.TemplateResponse("stats.html", {
        "request": request
    })


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
