import sys
import os
import mimetypes
from pathlib import Path

# Add the src directory to the path
current_dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.dirname(current_dir)  # Go up one level to src
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from .gemini_service import GeminiService


class ContentAnalyzer:
    def __init__(self):
        """Initialize the content analyzer with Gemini 2.0 Flash"""
        self.gemini = GeminiService()
        
        # Initialize mimetypes
        mimetypes.init()
    
    def analyze(self, document_content):
        """
        Analyze document content using Gemini 2.0 Flash.
        Returns 'technical', 'conversational', or 'mixed'.
        
        Args:
            document_content (str): The document content to analyze
            
        Returns:
            str: The document type ('technical', 'conversational', or 'mixed')
        """
        # Use only the first 1000 characters to avoid overloading the model
        sample = document_content[:1000]
        
        prompt = f"""
        Analyze the following document content and classify it as exactly one of these categories:
        - 'technical' (if it contains technical information, code, or specialized terminology)
        - 'conversational' (if it's informal, dialogue-based, or narrative)
        - 'mixed' (if it contains elements of both)
        
        Document content:
        {sample}
        
        Respond with only one word: technical, conversational, or mixed.
        """
        
        response = self.gemini.generate(prompt)
        
        # Process the response to extract the classification
        response = response.lower().strip()
        
        if "technical" in response:
            return "technical"
        elif "conversational" in response:
            return "conversational"
        else:
            return "mixed"
            
    def detect_file_type(self, file_path):
        """
        Detect the type of file and return appropriate metadata.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            dict: File metadata including type, mime_type, and processing_method
        """
        file_path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Default metadata
        metadata = {
            "file_name": file_path.name,
            "extension": file_path.suffix.lower(),
            "mime_type": mime_type or "application/octet-stream",
            "type": "unknown",
            "processing_method": "unknown"
        }
        
        # Determine file type and processing method
        if mime_type:
            if mime_type.startswith('image/'):
                metadata["type"] = "image"
                metadata["processing_method"] = "vision_model"
                
            elif mime_type == 'application/pdf':
                metadata["type"] = "pdf"
                metadata["processing_method"] = "pdf_extraction"
                
            elif mime_type.startswith('text/'):
                metadata["type"] = "text"
                metadata["processing_method"] = "text_chunking"
                
            elif mime_type in ['application/vnd.ms-excel', 
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                metadata["type"] = "excel"
                metadata["processing_method"] = "pandas_extraction"
                
            elif mime_type in ['application/vnd.ms-excel.sheet.macroEnabled.12', 
                              'application/vnd.ms-excel.template.macroEnabled.12']:
                metadata["type"] = "excel"
                metadata["processing_method"] = "pandas_extraction"
        
        # Fallback to extension-based detection
        else:
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                metadata["type"] = "image"
                metadata["processing_method"] = "vision_model"
                
            elif ext == '.pdf':
                metadata["type"] = "pdf"
                metadata["processing_method"] = "pdf_extraction"
                
            elif ext in ['.txt', '.md', '.py', '.js', '.html', '.css']:
                metadata["type"] = "text"
                metadata["processing_method"] = "text_chunking"
                
            elif ext in ['.xls', '.xlsx']:
                metadata["type"] = "excel"
                metadata["processing_method"] = "pandas_extraction"
                
            elif ext == '.csv':
                metadata["type"] = "table"
                metadata["processing_method"] = "table_extraction"
        
        return metadata
    
    def process_image_content(self, image_path):
        """
        Process image content using Gemini Vision model.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Extracted content and metadata
        """
        # Extract text from image using Gemini
        extracted_text = self.gemini.process_image(image_path)
        
        return {
            "content": extracted_text,
            "metadata": {
                "source": "image",
                "extraction_method": "gemini_vision",
                "original_path": image_path
            }
        }
    
    def process_table_image(self, image_path):
        """
        Process an image containing a table using Gemini.
        
        Args:
            image_path (str): Path to the image file containing a table
            
        Returns:
            dict: Extracted table content and metadata
        """
        # Extract table from image using Gemini
        table_content = self.gemini.extract_table(image_path)
        
        return {
            "content": table_content,
            "metadata": {
                "source": "table_image",
                "extraction_method": "gemini_vision",
                "original_path": image_path
            }
        }