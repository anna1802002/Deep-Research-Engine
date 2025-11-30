# api/main.py (updated for docs)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import yaml
import os
import sys
from contextlib import asynccontextmanager

# Import routes
from api.routes import query, reports

# Import middleware
from api.middleware import (
    RequestLoggingMiddleware, 
    RateLimitMiddleware,
    ErrorHandlingMiddleware,
    ValidationErrorMiddleware,
    APIKeyMiddleware
)

# Setup logging
logger = logging.getLogger("deep_research")

# Configure logging if not already configured
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join("logs", "api.log"))
        ]
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the application.
    Handles startup and shutdown events.
    """
    # Startup: Load configuration, initialize connections, etc.
    logger.info("Starting Deep Research Engine API")
    
    # Setup database connections, etc. here
    
    yield
    
    # Shutdown: Close connections, cleanup, etc.
    logger.info("Shutting down Deep Research Engine API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI app with custom documentation settings
    app = FastAPI(
        title="Deep Research Engine API",
        description="""
        # Deep Research Engine API
        
        The Deep Research Engine API provides access to advanced research capabilities,
        allowing you to retrieve, rank, and extract relevant data from multiple sources.
        
        ## Features
        
        - **Query Processing**: Clean and expand research queries
        - **Multi-Source Research**: Search ArXiv, PubMed, Google Scholar, and the web
        - **Content Ranking**: Rank content by relevance, authority, and recency
        - **Report Generation**: Create formatted reports from research results
        
        ## Authentication
        
        Most endpoints require an API key. Include your API key in the `X-API-Key` header.
        
        ## Rate Limits
        
        The API has a rate limit of 100 requests per minute. If you exceed this limit,
        you will receive a 429 response with a `Retry-After` header.
        """,
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,  # We'll create custom docs route
        redoc_url=None  # We'll create custom redoc route
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Customize for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(ValidationErrorMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    
    # Optional API key middleware - enable in production
    # Load API keys from config
    """
    api_keys = set()
    try:
        with open("config/api_keys.yaml", "r") as f:
            config = yaml.safe_load(f)
            api_keys = set(config.get("api_keys", []))
    except Exception as e:
        logger.error(f"Error loading API keys: {e}")
    
    if api_keys:
        app.add_middleware(
            APIKeyMiddleware, 
            api_keys=api_keys,
            exclude_paths={"/", "/health", "/docs", "/redoc", "/openapi.json"}
        )
    """
    
    # Include routers
    app.include_router(query.router)
    app.include_router(reports.router)
    
    # Basic API routes
    @app.get("/")
    def read_root():
        """Return a welcome message for the API."""
        return {"message": "Welcome to the Deep Research Engine API!"}

    @app.get("/health")
    def health_check():
        """Check if the API is running."""
        return {"status": "API is running successfully"}
    
    # Custom API Documentation routes
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Return custom Swagger UI."""
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """Return custom ReDoc."""
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )
    
    # Custom OpenAPI schema
    @app.get("/openapi.json", include_in_schema=False)
    async def get_open_api_endpoint():
        """Return custom OpenAPI schema."""
        return get_custom_openapi(app)
    
    # Return app
    return app


def get_custom_openapi(app):
    """Generate custom OpenAPI schema with examples and additional information."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add API key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    # Add custom examples to schema
    add_examples_to_schema(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def add_examples_to_schema(schema):
    """Add custom examples to OpenAPI schema."""
    # Find paths and add examples
    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete"]:
                # Add example responses if not present
                if "responses" in operation:
                    for status, response in operation["responses"].items():
                        if status == "200" and "content" in response:
                            for content_type, media_type in response["content"].items():
                                if "example" not in media_type:
                                    # Add example based on the path
                                    if path == "/api/query" and method == "post":
                                        media_type["example"] = {
                                            "original_query": "quantum computing cryptography",
                                            "cleaned_query": "quantum computing cryptography",
                                            "expanded_query": "quantum computing, cryptography, qubits, encryption, post-quantum, Shor's algorithm, quantum key distribution, RSA",
                                            "related_terms": [
                                                "quantum computing", "cryptography", "qubits", "encryption", 
                                                "post-quantum", "Shor's algorithm", "quantum key distribution", "RSA"
                                            ]
                                        }
                                    elif path == "/api/research" and method == "post":
                                        media_type["example"] = {
                                            "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                                            "status": "pending",
                                            "created_at": "2024-03-21T10:30:00Z",
                                            "estimated_completion": "2024-03-21T10:32:00Z"
                                        }


app = create_app()