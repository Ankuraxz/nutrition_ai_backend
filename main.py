import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ai_image, s3_crud, mongo_crud_data, ai_gpt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nutrition AI",
    description="APIs for Nutrition AI",
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_image.router, prefix="/ai_image", tags=["ai_image"])
app.include_router(s3_crud.router, prefix="/s3", tags=["s3"])
app.include_router(mongo_crud_data.router, prefix="/mongo", tags=["mongo"])
app.include_router(ai_gpt.router, prefix="/health", tags=["chat"])

