import groq
import yaml
import re

class QueryParser:
    def __init__(self, model="llama3-8b-8192"):
        self.api_key = self.load_api_key()
        if not self.api_key:
            raise ValueError("GROQ API Key is missing in config/api_keys.yaml")
        self.client = groq.Client(api_key=self.api_key)
        self.model = model  

    def load_api_key(self):
        """Load API key from config/api_keys.yaml"""
        try:
            with open("config/api_keys.yaml", "r") as file:
                config = yaml.safe_load(file)
                return config.get("GROQ_API_KEY", "").strip()
        except FileNotFoundError:
            raise FileNotFoundError("⚠️ Config file not found: config/api_keys.yaml")
        except yaml.YAMLError:
            raise ValueError("⚠️ Invalid YAML format in config/api_keys.yaml")

    def clean_query(self, query: str) -> str:
        """Uses LLM to clean, structure, and optimize the query."""
        prompt = f"""
        You are an expert in deep research query optimization.
        Given the user query: "{query}", transform it by:
        - Removing unnecessary words (e.g., "how does", "impact", "what is", "why is", etc.).
        - Keeping only important research keywords.
        - Returning the cleaned query as a structured list of key terms.
        - Output format: Comma-separated keywords only, no extra text.
        
        Example:
        Input: "How does AI impact global healthcare and hospitals???"
        Output: AI, healthcare, hospitals
        
        IMPORTANT: Return ONLY the comma-separated keywords, with NO explanatory text.
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.2,  # Lower temperature for consistent results
            max_tokens=50
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # If the response includes explanatory text, remove it
        if ":" in response_text:
            # Take everything after the last colon
            response_text = response_text.split(":")[-1].strip()
        
        # Extract only the comma-separated list
        cleaned_response = self._extract_keywords(response_text)
        
        # Final sanity check - if it still has explanatory phrases, extract just words
        if len(cleaned_response.split()) > 10 and "," not in cleaned_response:
            words = re.findall(r'\b\w+\b', cleaned_response)
            words = [w for w in words if w.lower() not in ['the', 'is', 'are', 'after', 'processing', 'query', 'cleaned']]
            cleaned_response = ", ".join(words)
        
        return cleaned_response
        
    def _extract_keywords(self, response_text):
        """Extract just the keywords from the response."""
        # Try to find a comma-separated list
        if ',' in response_text:
            # Split by newlines and take the line with commas
            for line in response_text.split('\n'):
                if ',' in line:
                    # Remove quotes if present
                    return line.replace('"', '').replace("'", '').strip()
            
            # If no specific line has commas, extract all comma-separated values
            words = []
            for word in re.findall(r'[\w\-]+', response_text):
                if word.lower() not in ['output', 'input', 'example']:
                    words.append(word)
            return ', '.join(words)
        
        # If no commas, just return cleaned text
        return ' '.join(re.findall(r'[\w\-]+', response_text))

if __name__ == "__main__":
    parser = QueryParser()
    
    user_query = input("🔍 Enter your search query: ")
    cleaned_query = parser.clean_query(user_query)

    print(f"\n✅ Original Query: {user_query}")
    print(f"🧹 Cleaned Query: {cleaned_query}\n")