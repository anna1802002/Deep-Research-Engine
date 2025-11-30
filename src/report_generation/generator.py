import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import markdown

class ReportGenerator:
    """Generates research reports from ranked content chunks."""
    
    def __init__(self, output_dir: str = "output"):
        self.logger = logging.getLogger("deep_research.report_generation.generator")
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, query: str, ranked_chunks: List[Dict], format: str = "markdown") -> str:
        """
        Generate a report from ranked chunks.
        
        Args:
            query: Original query
            ranked_chunks: Ranked content chunks
            format: Output format (markdown or html)
            
        Returns:
            Path to generated report
        """
        if not ranked_chunks:
            self.logger.warning("No chunks provided for report generation")
            return ""
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create sanitized query for filename
        sanitized_query = "".join(c if c.isalnum() or c.isspace() else "_" for c in query)
        sanitized_query = sanitized_query.lower().replace(" ", "_")[:30]
        
        # Full report filename
        report_filename = f"{sanitized_query}_{timestamp}"
        report_path = os.path.join(self.output_dir, f"{report_filename}.md")
        
        # Build report content
        report_content = self._build_report_content(query, ranked_chunks)
        
        # Write markdown report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        # Generate HTML if requested
        if format.lower() == "html":
            html_path = os.path.join(self.output_dir, f"{report_filename}.html")
            html_content = self._convert_to_html(report_content, query)
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            return html_path
        
        return report_path
    
    def _build_report_content(self, query: str, ranked_chunks: List[Dict]) -> str:
        """Build markdown report content."""
        report = [
            f"# Research Report: {query}",
            f"\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            
            "\n## Summary",
            f"This report contains the top {len(ranked_chunks)} most relevant excerpts from various sources related to your query.",
            
            "\n## Key Findings"
        ]
        
        # Add each chunk as a section
        for i, chunk in enumerate(ranked_chunks):
            metadata = chunk.get("metadata", {})
            title = metadata.get("title", "Unknown Source")
            url = metadata.get("url", "#")
            source = metadata.get("source", "Unknown")
            score = metadata.get("final_score", 0)
            
            report.append(f"\n### {i+1}. {title}")
            report.append(f"**Source**: {source}")
            if url != "#":
                report.append(f"**URL**: {url}")
            if "publication_date" in metadata:
                report.append(f"**Date**: {metadata['publication_date']}")
            report.append(f"**Relevance Score**: {score:.2f}")
            report.append("")
            report.append(chunk.get("text", ""))
        
        # Add bibliography
        report.append("\n## Sources")
        sources = {}
        
        for chunk in ranked_chunks:
            metadata = chunk.get("metadata", {})
            url = metadata.get("url", "")
            title = metadata.get("title", "Unknown")
            
            if url and url not in sources and url != "#":
                sources[url] = title
        
        for url, title in sources.items():
            report.append(f"- [{title}]({url})")
        
        return "\n".join(report)
    
    def _convert_to_html(self, markdown_content: str, title: str) -> str:
        """Convert markdown to HTML."""
        html_content = markdown.markdown(markdown_content)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report: {title}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            color: #333;
        }}
        h1 {{ 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #3498db; 
            border-bottom: 1px solid #eee; 
            padding-bottom: 5px; 
            margin-top: 25px;
        }}
        h3 {{ 
            color: #2980b9; 
            margin-top: 20px;
        }}
        a {{ 
            color: #3498db; 
            text-decoration: none; 
        }}
        a:hover {{ 
            text-decoration: underline; 
        }}
        .metadata {{ 
            color: #7f8c8d; 
            font-size: 0.9em; 
            margin-bottom: 15px; 
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""