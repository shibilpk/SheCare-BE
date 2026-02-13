

import os
from google import genai
from google.genai import errors


class AIService:
    def __init__(self):
        # In Django, it's safer to use os.environ or settings.GEMINI_API_KEY
        self.api_key = "AIzaSyDz-gNZH1Bnv4Fd7kGfoFASq2oTngWwtx4"
        self.client = genai.Client(api_key=self.api_key)

        # Use the stable 2026 model.
        # Use 'gemini-3-flash-preview' only if you need experimental features.
        self.model_id = "gemini-2.5-flash"

    def generate_report_logic(self, user_query):

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_query
            )
            print("AI Response:", response.json())
            return response.text

        except errors.ClientError as e:
            # Matches your 404 error or 400 Bad Request
            if e.code == 404:
                return "Error: The AI model version was not found. Please check model name."
            elif e.code == 401:
                return "Error: Invalid API Key."
            elif e.code == 429:
                return "Error: Rate limit exceeded. Please wait a moment."
            return f"Client Error: {e.message}"

        except errors.ServerError as e:
            # Handles 500/503 errors (Google's servers are down)
            return "The AI service is currently overloaded. Try again later."

        except Exception as e:
            # Catch-all for network or unexpected issues
            return f"An unexpected error occurred: {str(e)}"


def report_view():
    ai = AIService()
    report_data = ai.generate_report_logic("Write python to add two numbers")

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


