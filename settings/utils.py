import os
import logging
import json

def get_username_from_email(email: str) -> str:
    """
    Splits the email at '@' and returns the username part.
    """
    return email.split('@')[0]

def json_cleaner(data):
    """
    Cleans data to make json compatible, removing extra whitespaces and newlines and ' and " from the data
    :param data:
    :return:
    """
    try:
        data = str(data)
        data = data.replace("\n", " ")
        data = data.replace("\r", " ")
        data = data.replace("  ", " ")
        data = data.replace("\\", "")
        data = data.replace("/", "")
        return json.loads(data)
    except Exception as e:
        logger.error(f"Error in cleaning data: {str(e)}")
        return data