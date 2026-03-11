

import os
import requests


class AIService:
    def __init__(self, provider='groq'):
        """
        Initialize AI Service with a provider.

        Args:
            provider (str): 'groq' or 'gemini'
        """
        self.provider = provider

    def get_groq_api_key(self):
        return os.getenv('GROQ_API_KEY', '')

    def get_gemini_api_key(self):
        return os.getenv('GEMINI_API_KEY', '')

    def generate_with_groq(self, user_query):
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_groq_api_key()}"
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "user",
                    "content": user_query
                }
            ]
        }

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            print("Groq AI Response:", data)

            return data['choices'][0]['message']['content']

        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                return "Error: The AI model version was not found. Please check model name."
            elif response.status_code == 401:
                return "Error: Invalid API Key."
            elif response.status_code == 429:
                return "Error: Rate limit exceeded. Please wait a moment."
            elif response.status_code >= 500:
                return "The AI service is currently overloaded. Try again later."
            return f"HTTP Error: {e}"

        except requests.exceptions.RequestException as e:
            return f"Request Error: {str(e)}"

        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def generate_with_gemini(self, user_query):
        """Generate response using Google Gemini API"""
        from google.genai import errors

        try:
            from google import genai
            api_key = self.get_gemini_api_key()
            client = genai.Client(api_key=api_key)

            model_id = "gemini-2.5-flash"
            response = client.models.generate_content(
                model=model_id,
                contents=user_query
            )
            print("Gemini AI Response:", response.json())
            return response.text

        except errors.ClientError as e:
            if e.code == 404:
                return "Error: The AI model version was not found. Please check model name."
            elif e.code == 401:
                return "Error: Invalid API Key."
            elif e.code == 429:
                return "Error: Rate limit exceeded. Please wait a moment."
            return f"Client Error: {e.message}"

        except errors.ServerError as e:
            print(f"Server Error: {e.message}")
            return "The AI service is currently overloaded. Try again later."

        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

    def generate_report_logic(self, user_query, provider=None):
        """
        Generate AI response using the specified provider.

        Args:
            user_query (str): The user's question/prompt
            provider (str, optional): Override the default provider ('groq' or 'gemini')

        Returns:
            str: AI generated response
        """
        provider = provider or self.provider

        if provider == 'groq':
            return self.generate_with_groq(user_query)
        elif provider == 'gemini':
            return self.generate_with_gemini(user_query)
        else:
            return f"Error: Unknown provider '{provider}'. Use 'groq' or 'gemini'."


def report_view():
    # Example 1: Use Groq (default)
    ai = AIService(provider='groq')
    report_data = ai.generate_report_logic("Write python to add two numbers")

    # Example 2: Use Gemini
    # ai = AIService(provider='gemini')
    # report_data = ai.generate_report_logic("Write python to add two numbers")

    # Example 3: Switch provider on-the-fly
    # ai = AIService(provider='groq')
    # groq_response = ai.generate_report_logic("Question 1", provider='groq')
    # gemini_response = ai.generate_report_logic("Question 2", provider='gemini')

    # 1. Get the directory where views.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Define the filename (e.g., latest_report.txt)
    file_path = os.path.join(current_dir, 'latest_report.md')

    # 3. Write the data to the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_data)
        print(f"Report saved successfully at {file_path}")
    except Exception as e:
        print(f"Failed to write file: {e}")
