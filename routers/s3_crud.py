import os
import logging
import uuid
from fastapi import APIRouter, status, UploadFile, Form, Header
from typing import Union
from starlette.responses import JSONResponse
from settings.config import Config
from typing import Annotated

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize S3 client from configuration
Config = Config()
s3_client = Config.get_s3_client()

# S3 bucket name constant
BUCKET_NAME = "food-calorie-estimation"


# Helper functions

def upload_to_s3(image_path, username):
    """
    Uploads a file to the specified S3 bucket and folder (username as folder).
    """
    try:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"The file {image_path} does not exist.")

        image_name = os.path.basename(image_path)
        s3_client.upload_file(image_path, BUCKET_NAME, f"{username}/{image_name}")
        logger.info(f"Uploaded {image_name} to S3 bucket {BUCKET_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error in uploading file to S3: {str(e)}")
        return False


def download_from_s3(username, image_name):
    """
    Downloads a file from the specified S3 bucket and folder (username as folder).
    """
    try:
        s3_client.download_file(BUCKET_NAME, f"{username}/{image_name}", image_name)
        logger.info(f"Downloaded {image_name} from S3 bucket {BUCKET_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error in downloading file from S3: {str(e)}")
        return False


def delete_from_s3(username, image_name):
    """
    Deletes a file from the specified S3 bucket and folder (username as folder).
    """
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=f"{username}/{image_name}")
        logger.info(f"Deleted {image_name} from S3 bucket {BUCKET_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error in deleting file from S3: {str(e)}")
        return False


# Extract username from email
def get_username_from_email(email: str) -> str:
    """
    Splits the email at '@' and returns the username part.
    """
    return email.split('@')[0]


@router.post("/upload_to_s3", tags=["s3"])
async def upload_to_s3_api(email_id: Annotated[Union[str, None], Header()],
                           image_file: UploadFile = Form(...),

                           ) -> JSONResponse:
    """
    Uploads an image file to S3 using username (derived from email) as folder.
    """
    try:
        # Extract username from email
        username = get_username_from_email(email_id)

        # Validate image type
        if image_file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
            return JSONResponse(content={"message": "Only .jpg/.jpeg/.png images are allowed"},
                                status_code=status.HTTP_400_BAD_REQUEST)

        # Save the image locally
        random_num = uuid.uuid4()
        image_name = f"image_{random_num}.jpg"
        image_path = f"/tmp/{image_name}"

        with open(image_path, "wb") as f:
            f.write(await image_file.read())

        # Upload the file to S3
        if upload_to_s3(image_path, username):
            os.remove(image_path)
            path_uploaded = f"s3://{BUCKET_NAME}/{username}/{image_name}"
            return JSONResponse(
                content={"message": "File uploaded successfully", "image_name": image_name, "s3_path": path_uploaded},
                status_code=status.HTTP_200_OK)
        else:
            os.remove(image_path)
            return JSONResponse(content={"message": "Error in uploading file"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in uploading file to S3: {str(e)}")
        return JSONResponse(content={"message": f"Error in uploading file: {str(e)}"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/all_images_from_s3/{email}", tags=["s3"])
async def all_images_from_s3_api(email) -> JSONResponse:
    """
    Retrieves all images from a folder in the S3 bucket (username as folder).
    """
    try:
        username = get_username_from_email(email)
        images = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=username)
        image_list = [item['Key'] for item in images.get('Contents', [])]
        logger.info(f"Fetched images from S3 bucket {BUCKET_NAME}")
        return JSONResponse(content={"images": image_list}, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in fetching images from S3: {str(e)}")
        return JSONResponse(content={"message": f"Error in fetching images: {str(e)}"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/delete_from_s3", tags=["s3"])
async def delete_from_s3_api(
        email_id: Annotated[Union[str, None], Header()],
        image_name: str = Header(...)
) -> JSONResponse:
    """
    Deletes a file from S3 using username (derived from email) as folder.
    """
    try:
        username = get_username_from_email(email_id)

        if delete_from_s3(username, image_name):
            return JSONResponse(content={"message": "File deleted successfully"}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"message": "Error in deleting file"},
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in deleting file from S3: {str(e)}")
        return JSONResponse(content={"message": f"Error in deleting file: {str(e)}"},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
