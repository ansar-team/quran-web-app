from fastapi import FastAPI, Request, Depends, Cookie, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.i18n import load_i18n
from app.database import engine
from app.models import Base
from app.api import courses, lessons, words, users, reviews, telegram_auth, i18n
from app.utils.session_store import get_current_user

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
app.include_router(i18n.router, prefix="/api/v1")


async def template_context(
        request: Request,
        user=Depends(get_current_user)
):
    lang = user.language_code or "en"
    i18n = load_i18n(lang)

    return {
        "request": request,
        "user": user,
        "lang": lang,
        "i18n": i18n,
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("start.html", {
        "request": request
    })

@app.get("/home", response_class=HTMLResponse)
async def home(context=Depends(template_context)):
    return templates.TemplateResponse("index.html", context)


@app.get("/courses", response_class=HTMLResponse)
async def courses(context=Depends(template_context)):
    return templates.TemplateResponse("courses.html", context)


@app.get("/courses/create", response_class=HTMLResponse)
async def create_course_page(context=Depends(template_context)):
    return templates.TemplateResponse("create_course.html", context)


@app.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_detail_page(
        course_id: int,
        context=Depends(template_context)
):
    context["course_id"] = course_id
    return templates.TemplateResponse("course_details.html", context)


@app.get("/courses/{course_id}/lessons/create", response_class=HTMLResponse)
async def create_lesson_page(
    course_id: int,
    context=Depends(template_context)
):
    context["course_id"] = course_id
    return templates.TemplateResponse("create_lesson.html", context)


@app.get("/lessons/{lesson_id}", response_class=HTMLResponse)
async def lesson_detail_page(
        lesson_id: int,
        context=Depends(template_context)
):
    context["lesson_id"] = lesson_id
    return templates.TemplateResponse("lesson_details.html", context)


@app.get("/lessons/{lesson_id}/words/create", response_class=HTMLResponse)
async def create_word_page(
    lesson_id: int,
    context=Depends(template_context)
):
    context["lesson_id"] = lesson_id
    return templates.TemplateResponse("create_word.html", context)


@app.get("/study/{lesson_id}", response_class=HTMLResponse)
async def study_page(
    lesson_id: int,
    context=Depends(template_context)
):
    context["lesson_id"] = lesson_id
    return templates.TemplateResponse("study.html", context)


@app.get("/lessons/{lesson_id}/complete", response_class=HTMLResponse)
async def completion_page(
    lesson_id: int,
    context=Depends(template_context)
):
    context["lesson_id"] = lesson_id if lesson_id != 0 else None
    return templates.TemplateResponse("completion.html", context)


@app.get("/review/due", response_class=HTMLResponse)
async def review_due_page(context=Depends(template_context)):
    # Special case for review lesson
    context["lesson_id"] = None
    return templates.TemplateResponse("study.html", context)


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(context=Depends(template_context)):
    return templates.TemplateResponse("stats.html", context)


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(context=Depends(template_context)):
    return templates.TemplateResponse("settings.html", context)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Not found", "detail": "The requested resource was not found"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "An internal error occurred"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
