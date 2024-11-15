import os
import logging
import json

logger = logging.getLogger(__name__)


def get_username_from_email(email: str) -> str:
    """
    Splits the email at '@' and returns the username part.
    """
    return email.split('@')[0]


import json
import logging

logger = logging.getLogger(__name__)

def json_cleaner(data):
    """
    Cleans data to make it JSON-compatible by removing unnecessary whitespaces and ensuring proper quotation marks.
    :param data: Input data as a string
    :return: JSON-compatible data or original string if parsing fails
    """
    try:
        # Convert data to a string if not already
        data = str(data)

        # Remove extra newlines and whitespace
        data = " ".join(data.split())

        # Ensure JSON-friendly quotes
        data = data.replace("'", '"')  # Convert single quotes to double quotes for JSON compatibility
        data = data.replace("\n", " ")
        data = data.replace("\r", " ")
        data = data.replace("  ", " ")
        data = data.replace("\\", "")
        data = data.replace("/", "")

        # Attempt to parse and load as JSON
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {str(e)}")
        return data  # Return the original data if parsing fails
    except Exception as e:
        logger.error(f"Error in cleaning data: {str(e)}")
        return data



def clean_grocery_list(grocery_list):
    grocery_list["grocery_list"] = grocery_list["grocery_list"].replace('"', '')
    grocery_list["grocery_list"] = grocery_list["grocery_list"].replace("\\", '')
    grocery_list["grocery_list"] = grocery_list["grocery_list"].replace(",", ',  ')
    return grocery_list


def bmi_calculator(weight: float, height: float) -> float:
    """
    Calculate the BMI of a person based on their weight and height.
    :param weight: The weight of the person in pounds
    :param height: The height of the person in feet.inches
    :return: If person is underweight, normal weight, overweight, or obese.
    """
    try:
        # Convert height from feet.inches to inches
        height_inches = height * 12

        # Calculate BMI using the formula: weight (lb) / [height (in)]^2 x 703
        bmi = (weight / (height_inches ** 2)) * 703

        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "normalweight"
        elif 25 <= bmi < 30:
            return "overweight"
        else:
            return "obese"

    except Exception as e:
        logger.error(f"Error in BMI calculation: {str(e)}")
        return None
