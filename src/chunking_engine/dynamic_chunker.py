import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
import mimetypes

# Add the project root to sys.path if needed
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from .gemini_service import GeminiService
from .content_analyzer import ContentAnalyzer

class ChunkEntry:
    def __init__(self, chunk_id, document_id, content, start_index, end_index, metadata):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.content = content
        self.start_index = start_index
        self.end_index = end_index
        self.metadata = metadata

    def __repr__(self):
        return f"ChunkEntry(id={self.chunk_id}, content='{self.content[:30]}...')"

class DynamicChunker:
    def __init__(self):
        self.gemini = GeminiService()
        self.content_analyzer = ContentAnalyzer()
        
        # Initialize mimetypes
        mimetypes.init()
        
        # Load the tags hierarchy from tags_test.json
        self.tags_hierarchy = self._load_tags_hierarchy()
        
    def _load_tags_hierarchy(self):
        """
        Load the tag hierarchy from tags_test.json file.
        Returns a flattened list of all available tags.
        """
        try:
            self.tags_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tags_test.json")
            if os.path.exists(self.tags_file_path):
                with open(self.tags_file_path, 'r') as f:
                    tags_hierarchy = json.load(f)
                    return tags_hierarchy
            return {}
        except Exception as e:
            print(f"Error loading tags hierarchy: {e}")
            return {}
    
    def _extract_tags_from_hierarchy(self, hierarchy, current_path=None, result=None):
        """
        Extract all tags from a nested hierarchy into a flat list.
        
        Args:
            hierarchy (dict): The hierarchy dictionary
            current_path (list): Current path in the hierarchy
            result (list): Result list to append tags to
            
        Returns:
            list: Flat list of all tags with their hierarchical paths
        """
        if result is None:
            result = []
        
        if current_path is None:
            current_path = []
        
        for key, value in hierarchy.items():
            new_path = current_path + [key]
            # Add the current tag with its full path
            result.append({
                "tag": key,
                "path": " > ".join(new_path)
            })
            
            # Recursively process children
            if isinstance(value, dict):
                self._extract_tags_from_hierarchy(value, new_path, result)
                
        return result

    def generate_chunk_tag(self, chunk_content):
        """
        Generate a tag for a chunk using LLM based on the chunk's content.
        First checks if any existing tag from the tags hierarchy is suitable.
        
        Args:
            chunk_content (str): The content of the chunk
            
        Returns:
            str: A tag name representing the content
        """
        # Limit content size to avoid overloading the model
        content_sample = chunk_content[:1500] if len(chunk_content) > 1500 else chunk_content
        
        # Extract all available tags from the hierarchy
        all_tags = self._extract_tags_from_hierarchy(self.tags_hierarchy)
        
        if all_tags:
            # If we have existing tags, ask the LLM to check if any of them are suitable
            tag_options = "\n".join([f"- {tag_info['path']}" for tag_info in all_tags])
            
            prompt = f"""
            Given the following text content and a list of existing tags, determine if any of the existing tags 
            are suitable for the content. If multiple tags could apply, choose the most specific one.
            If none of the existing tags are suitable, respond with "NONE".

            Content:
            {content_sample}

            Available Tags (with their hierarchy paths):
            {tag_options}

            If one of the existing tags is suitable, return ONLY that tag's name (the last part of the path).
            If none are suitable, return only "NONE".
            """
            
            try:
                response = self.gemini.generate(prompt)
                tag = response.strip()
                
                # If a suitable tag was found, use it
                if tag != "NONE":
                    # Update the tag hierarchy with this chunk's content
                    self._update_tag_hierarchy(tag, content_sample, is_new_tag=False)
                    return tag
            except Exception as e:
                print(f"Error matching existing tags: {e}")
        
        # If no suitable tag was found or there was an error, generate a new tag
        prompt = f"""
        Given the following text content, generate a single, short (1-3 words) tag that best represents the main topic or theme.
        The tag should be concise, descriptive, and reflect the key subject matter.
        
        Content:
        {content_sample}
        
        Return ONLY the tag, with no additional text, punctuation, or formatting.
        """
        
        try:
            response = self.gemini.generate(prompt)
            # Clean up any extra whitespace or newlines
            tag = response.strip()
            
            # Update the tag hierarchy with this new tag and chunk content
            self._update_tag_hierarchy(tag, content_sample, is_new_tag=True)
            
            return tag
        except Exception as e:
            print(f"Error generating tag: {e}")
            return "Untagged"

    def split_document(self, document, chunk_size):
        """
        Splits the document into fixed-length chunks.
        """
        chunks = []
        for i in range(0, len(document), chunk_size):
            chunk_content = document[i:i+chunk_size]
            # Generate tag for this chunk
            tag = self.generate_chunk_tag(chunk_content)
            chunk = ChunkEntry(
                chunk_id=i // chunk_size,
                document_id="doc_1",
                content=chunk_content,
                start_index=i,
                end_index=i + len(chunk_content),
                metadata={"type": "text", "method": "split-based", "tag": tag}
            )
            chunks.append(chunk)
        return chunks

    def adjust_chunk_size(self, chunks, max_size):
        """
        Re-splits any chunk that exceeds the maximum allowed size.
        """
        adjusted_chunks = []
        for chunk in chunks:
            if len(chunk.content) > max_size:
                # Recursively re-split this chunk if too long
                subchunks = self.split_document(chunk.content, max_size)
                adjusted_chunks.extend(subchunks)
            else:
                adjusted_chunks.append(chunk)
        return adjusted_chunks

    def merge_chunks(self, chunks, min_size):
        """
        Merges adjacent chunks if their combined content size is less than min_size.
        This helps maintain semantic coherence if chunks are too short.
        """
        if not chunks:
            return []
        
        merged_chunks = []
        temp_chunk = chunks[0]
        
        for chunk in chunks[1:]:
            if len(temp_chunk.content) + len(chunk.content) <= min_size:
                # Merge content and extend the end index
                temp_chunk.content += chunk.content
                temp_chunk.end_index = chunk.end_index
            else:
                merged_chunks.append(temp_chunk)
                temp_chunk = chunk
        
        merged_chunks.append(temp_chunk)
        return merged_chunks

    def rule_based_chunking(self, document):
        """
        Uses regex patterns to identify natural document boundaries.
        
        Args:
            document (str): The document content to chunk
            
        Returns:
            list: List of ChunkEntry objects
        """
        # Define patterns for natural boundaries (headings, paragraphs, etc.)
        patterns = [
            r'#{1,6}\s+.+\n',  # Markdown headings
            r'\n\n+',          # Multiple newlines (paragraph breaks)
            r'\d+\.\s+',       # Numbered lists
            r'``````',         # Code blocks
            r'\*\*.*?\*\*',    # Bold text (potential section titles)
        ]
        
        # Combine patterns
        combined_pattern = '|'.join(f'({p})' for p in patterns)
        
        # Split the document using the combined pattern
        splits = re.split(f'({combined_pattern})', document)
        
        # Reassemble chunks, keeping the delimiters
        chunks = []
        current_chunk = ""
        start_index = 0
        chunk_id = 0
        
        for i, split in enumerate(splits):
            if not split:  # Skip empty splits
                continue
                
            # Check if this is a delimiter
            is_delimiter = any(re.match(p, split) for p in patterns)
            
            if is_delimiter and current_chunk:
                # End the current chunk and start a new one
                # Generate tag for this chunk
                tag = self.generate_chunk_tag(current_chunk)
                chunks.append(ChunkEntry(
                    chunk_id=chunk_id,
                    document_id="doc_1",
                    content=current_chunk,
                    start_index=start_index,
                    end_index=start_index + len(current_chunk),
                    metadata={"type": "text", "method": "rule-based", "tag": tag}
                ))
                chunk_id += 1
                start_index += len(current_chunk)
                current_chunk = split
            else:
                # Add to the current chunk
                current_chunk += split
        
        # Add the last chunk if there is one
        if current_chunk:
            # Generate tag for this chunk
            tag = self.generate_chunk_tag(current_chunk)
            chunks.append(ChunkEntry(
                chunk_id=chunk_id,
                document_id="doc_1",
                content=current_chunk,
                start_index=start_index,
                end_index=start_index + len(current_chunk),
                metadata={"type": "text", "method": "rule-based", "tag": tag}
            ))
        
        return chunks

    def llm_based_chunking(self, document):
        """
        Uses LLM to create semantically coherent chunks from the document.
        The LLM decides both the number of chunks and their sizes based on semantic coherence.
        
        Args:
            document (str): The document content to chunk
            
        Returns:
            list: List of ChunkEntry objects
        """
        # Check if document is JSON and parse it
        try:
            import json
            doc_json = json.loads(document)
            # If it's our research paper format with sections
            if "Sections" in doc_json:
                chunks = []
                chunk_id = 0
                
                # Process each section as a separate chunk
                for section in doc_json["Sections"]:
                    title = section.get("title", "")
                    content = section.get("content", "")
                    
                    # Further chunk the content if it's too large (> 1500 characters)
                    if len(content) > 1500:
                        # Split content into paragraphs
                        paragraphs = re.split(r'\n\n+', content)
                        current_chunk = ""
                        current_title = title
                        
                        for para in paragraphs:
                            # If adding this paragraph would exceed max size, create a new chunk
                            if len(current_chunk) + len(para) > 1500 and current_chunk:
                                # Generate tag for this chunk
                                tag = self.generate_chunk_tag(current_chunk)
                                chunks.append(ChunkEntry(
                                    chunk_id=chunk_id,
                                    document_id="doc_1",
                                    content=current_chunk,
                                    start_index=0,
                                    end_index=len(current_chunk),
                                    metadata={
                                        "type": "text", 
                                        "method": "llm-based",
                                        "title": current_title,
                                        "tag": tag
                                    }
                                ))
                                chunk_id += 1
                                current_chunk = para + "\n\n"
                            else:
                                current_chunk += para + "\n\n"
                        
                        # Add the last chunk if there's content left
                        if current_chunk:
                            # Generate tag for this chunk
                            tag = self.generate_chunk_tag(current_chunk)
                            chunks.append(ChunkEntry(
                                chunk_id=chunk_id,
                                document_id="doc_1",
                                content=current_chunk,
                                start_index=0,
                                end_index=len(current_chunk),
                                metadata={
                                    "type": "text", 
                                    "method": "llm-based",
                                    "title": current_title,
                                    "tag": tag
                                }
                            ))
                            chunk_id += 1
                    else:
                        # Create a chunk for this section
                        # Generate tag for this section
                        tag = self.generate_chunk_tag(content)
                        chunk = ChunkEntry(
                            chunk_id=chunk_id,
                            document_id="doc_1",
                            content=content,
                            start_index=0,  # We don't have exact indices in the original
                            end_index=len(content),
                            metadata={
                                "type": "text", 
                                "method": "llm-based",
                                "title": title,
                                "tag": tag
                            }
                        )
                        chunks.append(chunk)
                        chunk_id += 1
                
                return chunks
        except (json.JSONDecodeError, TypeError):
            pass
        
        # If not JSON or different format, use regular LLM chunking
        # Limit document size to avoid overloading the model
        sample = document[:5000] if len(document) > 5000 else document
        
        prompt = f"""
        Split the following document into semantically coherent chunks.
        Each chunk should represent a complete thought, concept, or section.
        
        You should decide:
        1. The appropriate number of chunks based on the content
        2. The appropriate size for each chunk (aim for 1000-1500 characters per chunk)
        
        Document:
        {sample}
        
        Return the chunks separated by three hyphens (---).
        Do NOT format the response as JSON. Just return plain text chunks.
        """
        
        response = self.gemini.generate(prompt)
        
        # Split the response by the separator
        chunks_content = response.split("---")
        
        # Clean up chunks and create ChunkEntry objects
        chunks = []
        chunk_id = 0
        
        for chunk_text in chunks_content:
            # Skip empty chunks
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
            
            # Create a chunk entry
            # Generate tag for this chunk
            tag = self.generate_chunk_tag(chunk_text)
            chunk = ChunkEntry(
                chunk_id=chunk_id,
                document_id="doc_1",
                content=chunk_text,
                start_index=0,  # We don't have exact indices in the original doc due to LLM chunking
                end_index=len(chunk_text),
                metadata={"type": "text", "method": "llm-based", "tag": tag}
            )
            chunks.append(chunk)
            chunk_id += 1
        
        return chunks
    
    def process_image(self, image_path):
        """
        Process an image file and extract text content using Gemini Vision.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list: List of ChunkEntry objects created from the image
        """
        # Extract text from image using Gemini
        extracted_info = self.content_analyzer.process_image_content(image_path)
        content = extracted_info["content"]
        
        # Generate tag for image content
        tag = self.generate_chunk_tag(content)
        
        # Create a chunk for the extracted text
        chunk = ChunkEntry(
            chunk_id=0,
            document_id=os.path.basename(image_path),
            content=content,
            start_index=0,
            end_index=len(content),
            metadata={
                "type": "image",
                "method": "vision_model",
                "source": image_path,
                "extraction_method": "gemini_vision",
                "tag": tag
            }
        )
        
        return [chunk]
    
    def process_table_image(self, image_path):
        """
        Process an image containing a table and extract structured data.
        
        Args:
            image_path (str): Path to the image file containing a table
            
        Returns:
            list: List of ChunkEntry objects created from the table
        """
        # Extract table content using Gemini
        extracted_info = self.content_analyzer.process_table_image(image_path)
        content = extracted_info["content"]
        
        # Generate tag for table content
        tag = self.generate_chunk_tag(content)
        
        # Create a chunk for the extracted table
        chunk = ChunkEntry(
            chunk_id=0,
            document_id=os.path.basename(image_path),
            content=content,
            start_index=0,
            end_index=len(content),
            metadata={
                "type": "table",
                "method": "vision_model",
                "source": image_path,
                "extraction_method": "gemini_vision",
                "tag": tag
            }
        )
        
        return [chunk]

    def _update_tag_hierarchy(self, tag, chunk_content, is_new_tag=False):
        """
        Update the tags hierarchy with chunk content.
        If it's an existing tag, add the chunk content to that tag.
        If it's a new tag, add it to the hierarchy.
        
        Args:
            tag (str): The tag name
            chunk_content (str): The content of the chunk
            is_new_tag (bool): Whether this is a new tag or existing tag
        """
        try:
            # If it's a new tag, try to add it to the most appropriate category
            if is_new_tag:
                # Get category suggestions from LLM
                prompt = f"""
                Given the tag "{tag}" and considering the following top-level categories in our tag hierarchy,
                which top-level category would be most appropriate to place this tag under?
                
                Categories:
                {", ".join(self.tags_hierarchy.keys())}
                
                Return ONLY the name of the most appropriate top-level category.
                """
                
                try:
                    response = self.gemini.generate(prompt)
                    category = response.strip()
                    
                    # Check if the suggested category exists
                    if category in self.tags_hierarchy:
                        # Add the new tag under this category with the chunk content
                        self.tags_hierarchy[category][tag] = {
                            "content_samples": [chunk_content[:200]]  # Store a sample of the content
                        }
                    else:
                        # If category doesn't exist, add directly to top level
                        self.tags_hierarchy[tag] = {
                            "content_samples": [chunk_content[:200]]
                        }
                except Exception as e:
                    print(f"Error getting category suggestion: {e}")
                    # Add directly to top level
                    self.tags_hierarchy[tag] = {
                        "content_samples": [chunk_content[:200]]
                    }
            else:
                # For existing tags, find and update
                self._add_content_to_existing_tag(self.tags_hierarchy, tag, chunk_content)
            
            # Save the updated hierarchy
            self._save_tags_hierarchy()
                
        except Exception as e:
            print(f"Error updating tag hierarchy: {e}")
    
    def _add_content_to_existing_tag(self, hierarchy, tag, chunk_content, max_samples=5):
        """
        Recursively search for the tag in the hierarchy and add the chunk content to it.
        
        Args:
            hierarchy (dict): The current level of hierarchy to search
            tag (str): The tag to find
            chunk_content (str): The content to add
            max_samples (int): Maximum number of content samples to store
        
        Returns:
            bool: True if tag was found and updated, False otherwise
        """
        for key, value in hierarchy.items():
            if key == tag:
                # Found the tag, add the content
                if "content_samples" not in value:
                    value["content_samples"] = []
                
                # Add content sample if we haven't reached the maximum
                if len(value["content_samples"]) < max_samples:
                    value["content_samples"].append(chunk_content[:200])  # Store a sample of the content
                return True
            
            # Recursively search in nested dictionaries
            if isinstance(value, dict):
                if self._add_content_to_existing_tag(value, tag, chunk_content, max_samples):
                    return True
        
        return False
    
    def _save_tags_hierarchy(self):
        """Save the updated tags hierarchy to the JSON file."""
        try:
            # First, remove all content_samples entries from a copy of the hierarchy for clean storage
            clean_hierarchy = self._create_clean_hierarchy(self.tags_hierarchy)
            
            with open(self.tags_file_path, 'w') as f:
                json.dump(clean_hierarchy, f, indent=4)
        except Exception as e:
            print(f"Error saving tags hierarchy: {e}")
    
    def _create_clean_hierarchy(self, hierarchy):
        """
        Create a clean copy of the hierarchy without the content_samples.
        
        Args:
            hierarchy (dict): The hierarchy to clean
            
        Returns:
            dict: Clean hierarchy
        """
        clean_dict = {}
        
        for key, value in hierarchy.items():
            if isinstance(value, dict):
                # Skip the content_samples key
                if key == "content_samples":
                    continue
                
                # Recursively clean nested dictionaries
                clean_dict[key] = self._create_clean_hierarchy(value)
            else:
                clean_dict[key] = value
                
        return clean_dict

def process_document(file_path, chunking_method="Auto-detect", output_dir="output"):
    """
    Processes the document at file_path using the specified chunking method.
    Now supports multi-modal inputs including images and tables.
    
    Args:
        file_path (str): Path to the document file
        chunking_method (str): Chunking method to use 
                              ("Auto-detect", "Split-based", "Rule-based", or "LLM-based")
        output_dir (str): Directory to save the JSON outputs
    
    Returns:
        tuple: (summary, chunks_serialized, json_path)
    """
    # Initialize objects
    analyzer = ContentAnalyzer()
    chunker = DynamicChunker()
    
    # Detect file type
    file_metadata = analyzer.detect_file_type(file_path)
    file_type = file_metadata["type"]
    
    # Process based on file type
    if file_type == "image":
        # Process image file
        chunks = chunker.process_image(file_path)
        summary = f"Image processed: {os.path.basename(file_path)}. Created {len(chunks)} chunks using Gemini Vision."
        
    elif file_type == "table":
        # Process image with table
        chunks = chunker.process_table_image(file_path)
        summary = f"Table processed: {os.path.basename(file_path)}. Created {len(chunks)} chunks using Gemini Vision."
    
    elif file_type == "excel" or file_path.lower().endswith(('.xlsx', '.xls')):
        try:
            # Use pandas to extract data from Excel
            import pandas as pd
            
            # Read Excel file into a pandas DataFrame
            df = pd.read_excel(file_path)
            
            # Convert DataFrame to string representation
            excel_content = df.to_string(index=False)
            
            # Create a chunk with the Excel content
            chunk = ChunkEntry(
                chunk_id=0,
                document_id=os.path.basename(file_path),
                content=excel_content,
                start_index=0,
                end_index=len(excel_content),
                metadata={
                    "type": "excel",
                    "method": "pandas",
                    "source": file_path,
                    "rows": len(df),
                    "columns": len(df.columns)
                }
            )
            
            chunks = [chunk]
            summary = f"Excel file processed: {os.path.basename(file_path)}. Created {len(chunks)} chunks containing {len(df)} rows and {len(df.columns)} columns."
            
        except ImportError:
            return f"Error: pandas module not found. Please install it with 'pip install pandas'.", [], ""
        except Exception as e:
            return f"Error processing Excel file: {str(e)}", [], ""
        
    elif file_type == "pdf":
        try:
            # Use PyPDF2 to extract text from PDF
            import PyPDF2
            content = ""
            with open(file_path, 'rb') as file:  # Note: 'rb' mode for binary reading
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    content += page.extract_text() + "\n\n"
            
            if not content.strip():
                # If PyPDF2 extraction fails or returns empty content, try using Gemini directly
                prompt = f"Extract and return only the text content from this PDF file: {os.path.basename(file_path)}"
                
                # In a real implementation, you'd use Gemini's API to process the PDF directly
                content = "PDF content extracted by Gemini would appear here."
                
        except ImportError:
            return "Error: PyPDF2 module not found. Please install it with 'pip install PyPDF2'.", [], ""
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}", [], ""
            
        # Analyze content using the Content Analyzer
        doc_type = analyzer.analyze(content)
        
        # Choose chunking method based on user selection or auto-detect
        if chunking_method == "Auto-detect":
            if doc_type == "technical":
                chunking_method = "Rule-based"
            elif doc_type == "conversational":
                chunking_method = "Split-based"
            else:  # mixed
                chunking_method = "LLM-based"
        
        # Apply the selected chunking method
        if chunking_method == "Rule-based":
            chunks = chunker.rule_based_chunking(content)
        elif chunking_method == "LLM-based":
            chunks = chunker.llm_based_chunking(content)
        else:  # Split-based (default)
            chunk_size = 100 if doc_type == "conversational" else 50
            initial_chunks = chunker.split_document(content, chunk_size)
            chunks = chunker.adjust_chunk_size(initial_chunks, chunk_size)
            chunks = chunker.merge_chunks(chunks, chunk_size // 2)
        
        summary = f"Document analyzed as: {doc_type}. Created {len(chunks)} chunks using method {chunking_method}."
        
    else:  # text or other file types
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='iso-8859-1') as f:
                    content = f.read()
            except UnicodeDecodeError:
                return "Error: Unable to decode file with UTF-8 or ISO-8859-1 encoding.", [], ""
        
        # Analyze content using the Content Analyzer
        doc_type = analyzer.analyze(content)
        
        # Choose chunking method based on user selection or auto-detect
        if chunking_method == "Auto-detect":
            if doc_type == "technical":
                chunking_method = "Rule-based"
            elif doc_type == "conversational":
                chunking_method = "Split-based"
            else:  # mixed
                chunking_method = "LLM-based"
        
        # Apply the selected chunking method
        if chunking_method == "Rule-based":
            chunks = chunker.rule_based_chunking(content)
        elif chunking_method == "LLM-based":
            chunks = chunker.llm_based_chunking(content)
        else:  # Split-based (default)
            chunk_size = 100 if doc_type == "conversational" else 50
            initial_chunks = chunker.split_document(content, chunk_size)
            chunks = chunker.adjust_chunk_size(initial_chunks, chunk_size)
            chunks = chunker.merge_chunks(chunks, chunk_size // 2)
        
        summary = f"Document analyzed as: {doc_type}. Created {len(chunks)} chunks using method {chunking_method}."
    
    # Save chunks to JSON
    filename = os.path.basename(file_path).split('.')[0] + "_chunks.json"
    json_path = save_chunks_to_json(chunks, output_dir=output_dir, filename=filename)
    
    # Add file path to summary
    summary += f" Saved to {json_path}"
    
    # Serialize chunks for return
    chunks_serialized = [vars(chunk) for chunk in chunks]
    
    return summary, chunks_serialized, json_path

def process_multiple_documents(file_paths, chunking_method="Auto-detect", output_dir="output"):
    """
    Process multiple documents and save their chunks to JSON files.
    
    Args:
        file_paths (list): List of paths to document files
        chunking_method (str): Chunking method to use
        output_dir (str): Directory to save the JSON outputs
        
    Returns:
        list: Summary information for each processed file
    """
    results = []
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for file_path in file_paths:
        try:
            summary, chunks, json_path = process_document(file_path, chunking_method, output_dir)
            results.append({
                "file": file_path,
                "status": "success",
                "summary": summary,
                "output_path": json_path,
                "chunk_count": len(chunks)
            })
        except Exception as e:
            results.append({
                "file": file_path,
                "status": "error",
                "error": str(e)
            })
    
    # Save a summary of all processed files
    summary_path = os.path.join(output_dir, f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    return results

def save_chunks_to_json(chunks, output_dir="output", filename=None):
    """
    Save chunks to a JSON file locally.
    
    Args:
        chunks (list): List of chunk objects or dictionaries
        output_dir (str): Directory to save the JSON file
        filename (str, optional): Custom filename, defaults to timestamp-based name
        
    Returns:
        str: Path to the saved JSON file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chunks_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Full path to output file
    output_path = os.path.join(output_dir, filename)
    
    # Convert chunks to serializable format if needed
    serializable_chunks = {}
    for i, chunk in enumerate(chunks):
        # If chunks are already dictionaries, use them directly
        if isinstance(chunk, dict):
            serializable_chunks[str(i)] = chunk
        # If chunks are ChunkEntry objects, convert to dict
        else:
            serializable_chunks[str(i)] = vars(chunk)
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_chunks, f, indent=2)
    
    return output_path