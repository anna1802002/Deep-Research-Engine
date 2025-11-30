# src/query_processing/expander.py (updated)
import groq
import yaml
import re

class QueryExpander:
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

    def expand_query(self, query: str) -> str:
        """
        Expand a query with additional relevant keywords.
        
        Args:
            query: Original query keywords
            
        Returns:
            Expanded query with additional relevant terms
        """
        # Create a domain-neutral prompt that focuses on generating relevant terms
        prompt = f"""
        You are an advanced AI for expanding research queries.
        Given the query keywords: "{query}", generate a highly relevant list of
        related research terms, synonyms, and technical concepts that would help
        improve search results.
        
        When generating terms, focus on:
        1. Technical terminology in the field
        2. Related concepts and processes
        3. Alternative phrasing of the key concepts
        4. Specific methodologies or approaches
        
        Return only a comma-separated list of words and phrases. No introduction or explanation.
        The most important and specific terms should come first.
        """

        # Call the language model with the prompt
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.6,  # Slightly lower temperature for more focus
            max_tokens=100
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract the comma-separated list of keywords
        expanded_terms = self._extract_keywords(response_text)
        
        # Add the original query terms at the beginning for emphasis
        if query not in expanded_terms:
            expanded_terms = query + ", " + expanded_terms
        
        return expanded_terms
        
    def _extract_keywords(self, response_text):
        """Extract just the keywords from the response."""
        # First, check if there's a comma-separated list
        if ',' in response_text:
            # Split by lines and get the line with most commas
            lines = response_text.split('\n')
            best_line = max(lines, key=lambda x: x.count(',')) if lines else response_text
            
            # Remove any quotation marks and explanatory text
            cleaned = re.sub(r'["\'()]', '', best_line)
            
            # If there's a colon, take only what comes after the last colon
            if ':' in cleaned:
                cleaned = cleaned.split(':')[-1].strip()
                
            return cleaned
        
        # If no commas, extract individual words and join them
        words = [word for word in re.findall(r'[\w\-]+', response_text) 
                if word.lower() not in ['output', 'input', 'example', 'query', 'the', 'and', 'is']]
        return ', '.join(words)

if __name__ == "__main__":
    expander = QueryExpander()
    
    user_query = input("🔍 Enter your research query: ")
    expanded_query = expander.expand_query(user_query)

    print(f"\n✅ Original Query: {user_query}")
    print(f"🚀 Expanded Query: {expanded_query}\n")