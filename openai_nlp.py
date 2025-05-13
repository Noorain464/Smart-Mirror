import openai
import os
from dotenv import load_dotenv
from openai import OpenAIError 
import requests
import base64
class NLPProcessor:
    def __init__(self):
        
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            raise ValueError("Missing OpenAI API Key. Set it in .env file.")

        self.client = openai.OpenAI(api_key=self.OPENAI_API_KEY) 
    def encode_image(self, image_path):
        """Encode image to base64 for OpenAI API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    def detect_intent(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze the user's request and respond with ONLY the relevant categories:
                        - "outfit" if clothing is mentioned
                        - "makeup" if cosmetics are mentioned
                        - "jewelry" if accessories are mentioned
                        Return only the relevant keywords separated by commas, or "general" if none apply."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            return response.choices[0].message.content.lower()
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "general"

    def fetch_wardrobe_items(self):
        FASTAPI_URL = "http://localhost:8000"
        try:
            response = requests.get(f"{FASTAPI_URL}/wardrobe")
            response.raise_for_status()
            categories = response.json()
            # print(categories)
            category_names = [c["name"].strip() for c in categories]
            # print(category_names)
            all_image_urls = []
            for category in category_names:
                response = requests.get(f"{FASTAPI_URL}/wardrobe/{category}")
                response.raise_for_status()
                items = response.json()
                for item in items:
                    url = item.get("image_url", "").strip()
                    if url.startswith("http"):
                        all_image_urls.append(url)

            return all_image_urls

        except requests.exceptions.RequestException as e:
            print(f"Error fetching wardrobe items: {e}")
            return None
    def generate_response(self, prompt):
        """General purpose response generation"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful smart mirror assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            return f"⚠️ OpenAI API Error: {e}"
        except Exception as e:
            return f"⚠️ Unexpected Error: {e}"
        
    def generate_fashion_response(self, transcript, image_path, wardrobe_urls, requested_categories):
        """Generate fashion response focused on requested categories"""
        base64_image = self.encode_image(image_path)
        
        # Build system prompt based on what was requested
        category_descriptions = {
            "outfit": "clothing suggestions that would look good on the user",
            "jewelry": "accessories that would complement the look",
            "makeup": "makeup recommendations suitable for the user"
        }
        
        requested = [category_descriptions[cat] for cat in requested_categories.split(",") if cat in category_descriptions]
        system_prompt = f"You are a fashion expert. Provide {' and '.join(requested)} based on the user's appearance."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": transcript},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        # Add wardrobe items if available
        if wardrobe_urls:
            for url in wardrobe_urls:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": url}
                })
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000,
        )
        
        return response.choices[0].message.content
