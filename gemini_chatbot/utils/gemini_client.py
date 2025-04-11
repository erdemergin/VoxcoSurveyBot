"""
Client for interacting with Google's Gemini API.
"""
from typing import List, Dict, Any, Optional, Callable, Union
import google.genai as genai
from google.genai import types
import logging
import requests
import json
from .. import config

# ANSI escape codes for gray color and italic text
GRAY_ITALIC = "\033[3;90m"  # 3 for italic, 90 for gray
RESET = "\033[0m"  # Reset formatting

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format=f'{GRAY_ITALIC}%(asctime)s - %(name)s - %(levelname)s - %(message)s{RESET}'
)

def authenticate_voxco(username: str, password: str):
    """
    Authenticate with Voxco API and get an authentication token.
    
    Args:
        username: Voxco account username
        password: Voxco account password
        
    Returns:
        The authentication token if successful, None otherwise
    """
    logging.info(f"Authenticating with Voxco API for user: {username}")
    url = f"https://beta7.voxco.com/api/authentication/user?userInfo.username={username}&userInfo.password={password}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        logging.info(f"Authentication successful. Token: {data.get('Token')}")
        return data.get("Token")
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Authentication error: {str(e)}")
        return None


def load_survey(token: str, survey_id: int) -> Optional[Dict[str, Any]]:
    """
    Load survey data in JSON format from Voxco API.
    
    Args:
        token: The authentication token for Voxco API
        survey_id: The ID of the survey to export
        
    Returns:
        The survey data as a JSON object if successful, None otherwise
    """
    logging.info(f"Exporting survey data for survey ID: {survey_id}")
    if not token:
        logging.error("No authentication token provided")
        return None
        
    url = f"https://beta7.voxco.com/api/survey/export/json/{survey_id}?deployed=false&modality=Master"
    headers = {"Authorization": f"Client {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        logging.info(f"Survey export successful. Response: {response.json()}")
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Survey export error: {str(e)}")
        return None


def save_survey(token: str, survey_id: int, survey_data: str) -> bool:
    """
    Save survey data in JSON format to Voxco API.
    
    Args:
        token: The authentication token for Voxco API
        survey_id: The ID of the survey to import to
        survey_data: The JSON survey data to import
        
    Returns:
        True if successful, False otherwise
    """
    logging.info(f"Importing survey data for survey ID: {survey_id} survey Data: {survey_data}")
    return True
    if not token:
        logging.error("No authentication token provided")
        return False
        
    url = f"https://beta7.voxco.com/api/survey/import/json/{survey_id}"
    headers = {
        "Authorization": f"Client {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=survey_data)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        logging.info(f"Survey import successful for survey ID: {survey_id}")
        return True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Survey import error: {str(e)}")
        return False


ai_functions = [authenticate_voxco, load_survey, save_survey]


class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, system_prompt: Optional[str] = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key. If None, uses the key from config.
            system_prompt: System prompt to set the AI's behavior. If None, uses value from config.
        """

        self.logger = logging.getLogger("GeminiChat")
        
        self.api_key = api_key or config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set it in .env file or pass it to the constructor.")
        

        self.system_prompt = system_prompt or config.SYSTEM_PROMPT
        self.client = genai.Client(api_key=self.api_key)
                            
        self.chat = self.client.chats.create(
            model=config.GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                tools=ai_functions,
                automatic_function_calling={"disable": False}
            )
        )
        
        self.voxco_token = None
    
    def authenticate_with_voxco(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate with Voxco API and store the token.
        
        Args:
            username: Voxco account username
            password: Voxco account password
            
        Returns:
            The authentication token if successful, None otherwise
        """
        token = authenticate_voxco(username, password)
        if token:
            self.voxco_token = token
            self.logger.info("Successfully authenticated with Voxco API")
        else:
            self.logger.error("Failed to authenticate with Voxco API")
        return token
    
    def send_message(self, message: str) -> str:
        """
        Send a message to the Gemini model and get a response.
        
        Args:
            message: The user's message to send
            
        Returns:
            The model's response text
        """
        try:
            # Log the user's message
            self.logger.info(f"USER: {message}")
            
            # Send the message and get the response using the chat session
            response = self.chat.send_message(message)
           
            # Return the final response text
            self.logger.info(f"AI: {response.text}")
            return response.text
            
        except Exception as e:
            error_msg = f"Error in processing: {str(e)}"
            self.logger.error(error_msg)
            return error_msg