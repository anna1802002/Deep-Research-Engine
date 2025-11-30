# src/database/analytics_store.py
import duckdb
import hashlib
import json
from datetime import datetime
import uuid

def initialize_duckdb():
    """Initialize DuckDB connection."""
    return duckdb.connect('data/analytics.duckdb')

def create_tables():
    """Create necessary tables if they don't exist."""
    conn = initialize_duckdb()
    
    # Create queries table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        query_id VARCHAR PRIMARY KEY,
        query_text VARCHAR,
        timestamp TIMESTAMP,
        params JSON
    )
    """)
    
    # Create results table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS results (
        result_id VARCHAR PRIMARY KEY, 
        query_id VARCHAR,
        source VARCHAR,
        result_data JSON,
        timestamp TIMESTAMP,
        FOREIGN KEY (query_id) REFERENCES queries(query_id)
    )
    """)
    
    conn.close()

def cache_query_results(query_text, results):
    """Cache query results in DuckDB."""
    conn = initialize_duckdb()
    
    # Generate IDs
    query_id = hashlib.md5(query_text.encode()).hexdigest()
    
    # Store query
    conn.execute(
        "INSERT INTO queries (query_id, query_text, timestamp, params) VALUES (?, ?, ?, ?)",
        [query_id, query_text, datetime.now(), json.dumps({})]
    )
    
    # Store results
    for idx, result in enumerate(results):
        result_id = f"{query_id}_{idx}"
        source = result.get("source", "unknown")
        conn.execute(
            "INSERT INTO results (result_id, query_id, source, result_data, timestamp) VALUES (?, ?, ?, ?, ?)",
            [result_id, query_id, source, json.dumps(result), datetime.now()]
        )
    
    conn.close()

def store_report(query_id, report_content, format):
    """Store generated report in DuckDB."""
    conn = initialize_duckdb()
    
    # Create reports table if it doesn't exist
    conn.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id VARCHAR PRIMARY KEY,
        query_id VARCHAR,
        content TEXT,
        format VARCHAR,
        timestamp TIMESTAMP,
        FOREIGN KEY (query_id) REFERENCES queries(query_id)
    )
    """)
    
    # Generate report ID
    report_id = str(uuid.uuid4())
    
    # Store report
    conn.execute(
        "INSERT INTO reports (report_id, query_id, content, format, timestamp) VALUES (?, ?, ?, ?, ?)",
        [report_id, query_id, report_content, format, datetime.now()]
    )
    
    conn.close()
    return report_id