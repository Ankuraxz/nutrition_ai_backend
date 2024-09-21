import logging
import json
import os
import requests
from fastapi import APIRouter, Form, HTTPException, Header
from typing import Optional, Annotated, Union
from routers.mongo_crud_data import *
from routers.s3_crud import *
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from settings.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
Config = Config()
vision_llm = Config.get_openai_vision_connection()


@router.get("/get_calorie_value/{s3_image_path}", tags=["ai_image"])
async def get_calorie_value(s3_image_path) -> dict:
    """
    Get calorie value of food item from image
    :param s3_image_path:
    :return: dict
    """
    try:
        response = client.chat.completions.create(model="gpt-4o-mini",
                                                  messages=[
                                                      {
                                                          "role": "user",
                                                          "content": [
                                                              {"type": "text",
                                                               "text": "Guess the Calorie value of this food item in this image, and respnd with the number of calories."},
                                                              {
                                                                  "type": "image_url",
                                                                  "image_url": {
                                                                      "url": s3_image_path,
                                                                  },
                                                              },
                                                          ],
                                                      }
                                                  ],
                                                  max_tokens=300,
                                                  )
        return {"calories": response.choices[0] }
    except Exception as e:
        logger.error(f"Error in getting calorie value from image: {str(e)}")
        return {}
