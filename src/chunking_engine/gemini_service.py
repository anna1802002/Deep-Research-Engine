import os
import io
import yaml
import google.generativeai as genai
from PIL import Image

class GeminiService:
    def __init__(self):
        # Initialize with placeholder methods
        try:
            # Try to load config if available
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "config")
            config_path = os.path.join(config_dir, "api_keys.yaml")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file)
                    api_key = config.get("google_api_key")
                    
                if api_key:
                    genai.configure(api_key=api_key)
                    self.text_model = genai.GenerativeModel('gemini-1.5-flash')
                    self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
                    return
        except Exception as e:
            print(f"Config loading error: {e}")
        
        # If we get here, either there was an error or no API key
        print("Warning: Using placeholder Gemini service")
        self.text_model = None
        self.vision_model = None
    
    def generate(self, prompt, model=None, stream=False):
        """Placeholder generate method"""
        if self.text_model:
            try:
                response = self.text_model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"API Error: {str(e)}"
        return "Sample classification: technical"
            
    def process_image(self, image_path):
        """Placeholder image processing method"""
        if self.vision_model:
            try:
                image = Image.open(image_path)
                response = self.vision_model.generate_content([image])
                return response.text
            except Exception as e:
                return f"Image processing error: {str(e)}"
        return "Sample extracted text from image"
    
    def extract_table(self, image_path):
        """Placeholder table extraction method"""
        if self.vision_model:
            try:
                image = Image.open(image_path)
                prompt = "Extract the table from this image and format it as CSV."
                response = self.vision_model.generate_content([prompt, image])
                return response.text
            except Exception as e:
                return f"Table extraction error: {str(e)}"
        return "header1,header2\nvalue1,value2\nvalue3,value4"