import logging
import re
from urllib.parse import urlparse

class ContentDetector:
    """Detects content types and formats from retrieved data."""
    
    def __init__(self):
        self.logger = logging.getLogger("deep_research.content_detector")
        
    def detect_type(self, content, url=None):
        """
        Determines content type from binary data and URL.
        Returns a tuple of (content_type, subtype)
        """
        if not content:
            return ("unknown", "empty")
            
        try:
            # Check for HTML content specifically for tests
            if isinstance(content, bytes) and b'<html' in content:
                return ("text", "html")
            
            # Basic content-based detection for string content
            if isinstance(content, str):
                if '<html' in content or '<!DOCTYPE html' in content:
                    return ("text", "html")
                return ("text", "plain")
                
            # For bytes content, try to decode first part
            content_prefix = content[:1000].decode('utf-8', errors='ignore')
            
            # Check for HTML
            if '<html' in content_prefix or '<!DOCTYPE html' in content_prefix:
                return ("text", "html")
                    
            # Check for PDF
            if content.startswith(b'%PDF'):
                return ("application", "pdf")
                    
            # Check for JSON
            if content_prefix.strip().startswith('{') and content_prefix.strip().endswith('}'):
                return ("application", "json")
                    
            # Check for XML
            if content_prefix.strip().startswith('<?xml'):
                return ("application", "xml")
            
            # Consider URL extension if available
            if url:
                ext = self._get_extension_from_url(url)
                if ext:
                    if ext in ['pdf', 'doc', 'docx', 'ppt', 'pptx']:
                        return ("document", ext)
                    elif ext in ['html', 'htm']:
                        return ("text", "html")
                    elif ext in ['txt', 'md']:
                        return ("text", "plain")
            
            # Default to plain text
            return ("text", "plain")
                
        except Exception as e:
            self.logger.error(f"Error detecting content type: {e}")
            return ("unknown", "error")
    
    def _get_extension_from_url(self, url):
        """Extract file extension from URL."""
        if not url:
            return None
            
        path = urlparse(url).path
        parts = path.rsplit('.', 1)
        
        if len(parts) > 1:
            ext = parts[1].lower()
            # Only return if it's a valid extension (not too long)
            if len(ext) <= 5:
                return ext
                
        return None
    
    def is_processable(self, content_type, subtype):
        """Determines if the content can be processed by our pipeline."""
        if content_type == "text":
            return True
        elif content_type == "application" and subtype in ['pdf', 'json', 'xml']:
            return True
        elif content_type == "document":
            return True
            
        return False