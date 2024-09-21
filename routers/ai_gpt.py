import logging
import json
import os
import requests
from fastapi import APIRouter, Form, HTTPException, Header
from typing import Optional, Annotated, Union
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAIChat
from routers.mongo_crud_data import *
from settings.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
Config = Config()
client = Config.get_mongo_client()
chat_llm = Config.get_openai_chat_connection()


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


@router.post("/chat", tags=["chat_ai"])
def chat(email_id: Annotated[Union[str, None], Header], message: str = Form(...), history: list = Form(...)):
    """
    Chat with AI about meals, nutrition and diet
    :param email_id:
    :param message:
    :param history:
    :return:
    """
    if history is None:
        history = []
    try:
        user_data = get_user_data_from_mongo(email_id)
        meal = load_meal_from_mongo(email_id)
        if meal is None:
            return {"message": "No meal found in user's profile", "history": history, "stop": True}
        grocery_list = load_grocery_list_from_mongo(email_id)
        if grocery_list is None:
            return {"message": "No grocery list found in user's profile", "history": history, "stop": True}

        if "STOP" in message or "Stop" in message or "stop" in message:
            save_chat_to_mongo(email_id, json.dumps(history))
            return {"response": "STOPPING CHAT ", "history": history, "stop": True}

        template = """You are an AI powered Meal & Grocery Planner. Client will be talking to you about their queries 
        regarding meals, groceries, goals. Here is the history of chat {history}, now the customer is saying {
        message}. Please respond to the customer in a polite manner. In case there is no history of chat, 
        just respond to the customer's current message. You will be provided with a user profile  {user_data} 
        containing information of "name", "age", "gender", //male, female, other "height", //in feet "weight", 
        //in lbs "activity_level", //sedentary, light, moderate, active, very_active "exercise_hours", //in hours 
        "job_type", //student, working "work_type", //office, field, home, None "work_hours", "cooking_hours", 
        //time dedicated to cooking "proficiency_in_cooking", //low, medium, high "goals", //healthy, weight_loss, 
        muscle_gain "dietary_restrictions": null, //None, vegetarian, vegan, gluten_free, dairy_free, 
        nut_free "diet_type", //balanced, keto, paleo, vegan, vegetarian "allergies", //None, peanuts, shellfish, 
        soy, dairy, eggs, gluten "cuisine_preference", //american, italian, mexican, chinese, indian, thai, 
        japanese "budget", //0-100 dollars for weekly groceries "grocery_frequency":, //weekly, bi-weekly, monthly

          Following is the meal {meal} and grocery list {grocery_list} for the user: 

        TASK: User can ask questions about the meal and grocery list and can also ask for meal and grocery list generation based on user's preferences. You need to answer queries related to nutritional information details, cooking time, ingredients, recipes, etc, in user preferred language
        ANSWER: You need to answer the queries based on the user's preferences, meal list and grocery list strictly and provide the information in a user friendly manner. 
        SUB_TASK: Address the user like a client needing help and provide the information in a user friendly manner.
        RESPONSE CONSTRAINT: DO NOT OUTPUT HISTORY OF CHAT, JUST OUTPUT RESPONSE TO THE CUSTOMER IN BULLET POINTS.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | chat_llm
        response = chain.invoke(
            {"history": json.dumps(history), "message": message, "user_data": user_data, "meal": meal,
             "grocery_list": grocery_list})
        if "STOP" in response or "Stop" in response or "stop" in response or "STOPPING CHAT" in response or "Stopping Chat" in response or "stopping chat" in response:
            save_chat_to_mongo(email_id, json.dumps(history))
            return {"response": response, "history": history, "stop": True}
        else:
            history.append({"message": message, "response": response})
            save_chat_to_mongo(email_id, json.dumps(history))
            return {"response": response, "history": history, "stop": False}


    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")


@router.get("/meal_generator/{email}", tags=["chat_ai"])
def meal_generator(email_id):
    """
    Generate meals based on user's preferences
    :param email_id:
    :return:
    """
    try:
        user_data = get_user_data_from_mongo(email_id)
        if user_data is None or user_data == {}:
            raise HTTPException(status_code=404, detail="User data not found in mongo db")
        template = """You are an AI powered Meal generator, you will be provided with a user profile  {user_data} 
        containing information of "name", "age", "gender", //male, female, other "height", //in feet "weight", 
        //in lbs "activity_level", //sedentary, light, moderate, active, very_active "exercise_hours", //in hours 
        "job_type", //student, working "work_type", //office, field, home, None "work_hours", "cooking_hours", 
        //time dedicated to cooking "proficiency_in_cooking", //low, medium, high "goals", //healthy, weight_loss, 
        muscle_gain "dietary_restrictions": null, //None, vegetarian, vegan, gluten_free, dairy_free, 
        nut_free "diet_type", //balanced, keto, paleo, vegan, vegetarian "allergies", //None, peanuts, shellfish, 
        soy, dairy, eggs, gluten "cuisine_preference", //american, italian, mexican, chinese, indian, thai, 
        japanese "budget", //0-100 dollars for weekly groceries "grocery_frequency":, //weekly, bi-weekly, monthly

        TASK: You need to generate easy to cook at home meals for entire week, 3 meals per day as breakfast, lunch dinner based on user's preferences keeping in mind cooking hours & cooking proficiency and budget and dietary restrictions and allergy and nutritional goals and provide the information as json 
        Example Response: ['day1':['breakfast':"eggs 19 calorie", 'lunch':"chicken salad 24 calorie", 'dinner':"pasta"], 'day2':['breakfast':"oatmeal", 'lunch':"chicken sandwich", 'dinner':"rice"], 'day3':['breakfast':"pancakes", 'lunch':"chicken soup", 'dinner':"pasta"], 'day4':['breakfast':"eggs", 'lunch':"chicken salad", 'dinner':"pasta"], 'day5':['breakfast':"oatmeal", 'lunch':"chicken sandwich", 'dinner':"rice"], 'day6':['breakfast':"pancakes", 'lunch':"chicken soup", 'dinner':"pasta"], 'day7':['breakfast':"eggs", 'lunch':"chicken salad", 'dinner':"pasta"]]
        REMEMBER: day, breakfast, lunch, dinner are the keys and the values are the meals for the day along with their calorie count per serving
        RESPONSE CONSTRAINT: DO NOT OUTPUT EXTRA CHARACTERS, JUST OUTPUT RESPONSE TO THE CUSTOMER IN PROPER JSON.
        """

        prompt = PromptTemplate.from_template(template)
        chain = prompt | chat_llm
        response = chain.invoke({"user_data": user_data})
        save_meal_to_mongo(email_id, json.dumps(json_cleaner(response)))
        return {"response": json_cleaner(response)}

    except Exception as e:
        logger.error(f"Error in meal generator: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in meal generator: {str(e)}")


@router.get("/grocery_list_generator/{email}", tags=["chat_ai"])
def grocery_list_generator(email_id):
    """
    Generate grocery list based on user's preferences
    :param email_id:
    :return:
    """
    try:
        user_data = get_user_data_from_mongo(email_id)
        if user_data is None or user_data == {}:
            raise HTTPException(status_code=404, detail="User data not found in mongo db")
        budget = user_data['budget']
        grocery_frequency = user_data['grocery_frequency']
        dietary_restrictions = user_data['dietary_restrictions']
        allergies = user_data['allergies']
        diet_type = user_data['diet_type']

        meal = load_meal_from_mongo(email_id)
        if meal is None or meal == {}:
            raise HTTPException(status_code=404, detail="Meal not found in user's profile")

        template = """
        You are an AI powered Grocery list generator, you will be provided with a user's meal list {meal} and user information including budget {budget}, dietary restrictions {dietary_restrictions}, allergies {allergies}, diet type {diet_type}.
        TASK: You need to generate grocery list for 1 grocery frequency {grocery_frequency} along with amount needed for the user based on their meal list and user information and provide the information as comma seperated string
        Example Response: "eggs 1 tray, bread 2 pack, milk 3 litre, chicken 1kg, rice 1kg, pasta, fruits, vegetables, cheese, butter, oil, sugar, salt, spices, herbs, nuts, seeds, flour, grains, legumes, beverages 2 pack, snacks 1 pack, condiments 3 pack, sauces 1 bottle, canned goods 1 can, frozen foods, dairy 1 litre, bakery, deli, meat 1 kg, seafood 1 kg"
        RESPONSE CONSTRAINT: DO NOT OUTPUT EXTRA CHARACTERS, JUST OUTPUT RESPONSE TO THE CUSTOMER IN PROPER STRING WITH QUANTITY. """

        prompt = PromptTemplate.from_template(template)
        chain = prompt | chat_llm
        response = chain.invoke({"meal": meal, "budget": budget, "grocery_frequency": grocery_frequency,
                                 "dietary_restrictions": dietary_restrictions, "allergies": allergies,
                                 "diet_type": diet_type})
        grocery = {"grocery_list": response}
        save_grocery_list_to_mongo(email_id, grocery)
        return {"response": response}

    except Exception as e:
        logger.error(f"Error in grocery list generator: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in grocery list generator: {str(e)}")


@router.get("/show_meal/{email}", tags=["chat_ai"])
def show_meal(email_id):
    """
    Show meal from user's profile
    :param email_id:
    :return:
    """
    try:
        meal = load_meal_from_mongo(email_id)
        if meal is None:
            raise HTTPException(status_code=404, detail="Meal not found in user's profile")
        return meal

    except Exception as e:
        logger.error(f"Error in showing meal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in showing meal: {str(e)}")


def clean_grocery_list(grocery_list):
    grocery_list["grocery_list"] = grocery_list["grocery_list"].replace('"', '')
    grocery_list["grocery_list"] = grocery_list["grocery_list"].replace("\\", '')
    grocery_list["grocery_list"] = grocery_list["grocery_list"].replace(",", ',  ')
    return grocery_list


@router.get("/show_grocery_list/{email}", tags=["chat_ai"])
def show_grocery_list(email_id):
    """
    Show grocery list from user's profile
    :param email_id:
    :return:
    """
    try:
        grocery_list = load_grocery_list_from_mongo(email_id)
        if grocery_list is None:
            raise HTTPException(status_code=404, detail="Grocery list not found in user's profile")
        return clean_grocery_list(grocery_list)

    except Exception as e:
        logger.error(f"Error in showing grocery list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in showing grocery list: {str(e)}")


@router.post("/export_grocery_list", tags=["chat_ai"])
def export_grocery_list(email_id: Annotated[Union[str, None], Header]):
    """
    Export grocery list from user's profile as a PDF
    :param email_id:
    :return:
    """
    try:
        grocery_list = load_grocery_list_from_mongo(email_id)
        if grocery_list is None:
            raise HTTPException(status_code=404, detail="Grocery list not found in user's profile")
        response = requests.post("https://api.html2pdf.app/v1/generate", json={"html": grocery_list})
        return response.content

    except Exception as e:
        logger.error(f"Error in exporting grocery list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in exporting grocery list: {str(e)}")
