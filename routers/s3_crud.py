import json
import os
import logging
from typing import Union, Annotated
from fastapi import APIRouter, status
from fastapi import Form, Header
from starlette.responses import JSONResponse
from settings.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
Config = Config()
s3_client = Config.get_s3_client()

#Helper functions

def upload_to_s3(image_path, bucket_name, folder_name):
    try:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"The file {image_path} does not exist.")
        file_name = os.path.basename(image_path)
        s3_client.upload_file(image_path, bucket_name, f"{folder_name}/{file_name}")
        logger.info(f"Uploaded {file_name} to S3 bucket {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Error in uploading file to S3: {str(e)}")
        return False

def download_from_s3(bucket_name, folder_name, file_name):
    try:
        s3_client.download_file(bucket_name, f"{folder_name}/{file_name}", file_name)
        logger.info(f"Downloaded {file_name} from S3 bucket {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Error in downloading file from S3: {str(e)}")
        return False

def delete_from_s3(bucket_name, folder_name, file_name):
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=f"{folder_name}/{file_name}")
        logger.info(f"Deleted {file_name} from S3 bucket {bucket_name}")
        return True
    except Exception as e:
        logger.error(f"Error in deleting file from S3: {str(e)}")
        return False


@router.post("/upload_to_s3", tags=["s3"])
async def upload_to_s3_api(image_path: str = Form(...),
                           bucket_name: str = Form(...),
                           folder_name: str = Form(...)) -> JSONResponse:
    """
    Upload file to S3 bucket
    :param image_path:
    :param bucket_name:
    :param folder_name:
    :return: JSONResponse
    """
    try:
        if upload_to_s3(image_path, bucket_name, folder_name):
            return JSONResponse(content={"message": "File uploaded successfully"}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"message": "Error in uploading file"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in uploading file to S3: {str(e)}")
        return JSONResponse(content={"message": "Error in uploading file"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/download_from_s3", tags=["s3"])
async def download_from_s3_api(bucket_name: str = Header(...),
                               folder_name: str = Header(...),
                               file_name: str = Header(...)) -> JSONResponse:
    """
    Download file from S3 bucket
    :param bucket_name:
    :param folder_name:
    :param file_name:
    :return: JSONResponse
    """
    try:
        if download_from_s3(bucket_name, folder_name, file_name):
            return JSONResponse(content={"message": "File downloaded successfully"}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"message": "Error in downloading file"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in downloading file from S3: {str(e)}")
        return JSONResponse(content={"message": "Error in downloading file"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/all_images_from_s3", tags=["s3"])
async def all_images_from_s3_api(bucket_name: str = Header(...),
                               folder_name: str = Header(...)) -> JSONResponse:
    """
    Get all images from S3 bucket
    :param bucket_name:
    :param folder_name:
    :return: JSONResponse
    """
    try:
        images = s3_client.list_objects(Bucket=bucket_name, Prefix=folder_name)
        logger.info(f"Images fetched from S3 bucket {bucket_name}")
        return JSONResponse(content={"images": images}, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in getting images from S3: {str(e)}")
        return JSONResponse(content={"message": "Error in getting images"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/delete_from_s3", tags=["s3"])
async def delete_from_s3_api(bucket_name: str = Header(...),
                             folder_name: str = Header(...),
                             file_name: str = Header(...)) -> JSONResponse:
    """
    Delete file from S3 bucket
    :param bucket_name:
    :param folder_name:
    :param file_name:
    :return: JSONResponse
    """
    try:
        if delete_from_s3(bucket_name, folder_name, file_name):
            return JSONResponse(content={"message": "File deleted successfully"}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"message": "Error in deleting file"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in deleting file from S3: {str(e)}")
        return JSONResponse(content={"message": "Error in deleting file"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

