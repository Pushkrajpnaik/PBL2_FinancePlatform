from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.api.routes import (
    auth,
    users,
    risk_profile,
    portfolio,
    goals,
    retirement,
    tax,
    prediction,
    simulation,
    news,
)
from app.core.database import create_tables

# Create all DB tables on startup
create_tables()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Autonomous Financial Intelligence Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router,         prefix="/api/v1/auth",        tags=["Authentication"])
app.include_router(users.router,        prefix="/api/v1/users",       tags=["Users"])
app.include_router(risk_profile.router, prefix="/api/v1/risk",        tags=["Risk Profiling"])
app.include_router(portfolio.router,    prefix="/api/v1/portfolio",   tags=["Portfolio"])
app.include_router(goals.router,        prefix="/api/v1/goals",       tags=["Goals"])
app.include_router(retirement.router,   prefix="/api/v1/retirement",  tags=["Retirement"])
app.include_router(tax.router,          prefix="/api/v1/tax",         tags=["Tax"])
app.include_router(prediction.router,   prefix="/api/v1/prediction",  tags=["Prediction"])
app.include_router(simulation.router,   prefix="/api/v1/simulation",  tags=["Simulation"])
app.include_router(news.router,         prefix="/api/v1/news",        tags=["News"])

@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

# Custom OpenAPI schema with BearerAuth
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Autonomous Financial Intelligence Platform",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi