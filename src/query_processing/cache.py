import duckdb
import os
import json

class QueryCache:
    """Handles caching of research queries using DuckDB."""

    def __init__(self, db_path="cache/query_cache.duckdb"):
        """
        Initialize DuckDB connection.
        - `db_path`: Path to the DuckDB database file.
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)  # ✅ Ensure cache folder exists
        self.db_path = db_path
        self.conn = duckdb.connect(database=self.db_path, read_only=False)
        self._initialize_db()

    def _initialize_db(self):
        """Creates the query cache table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                query TEXT PRIMARY KEY,
                result TEXT
            )
        """)
        self.conn.commit()  # ✅ Ensure changes are saved

    def get_cached_result(self, query: str):
        """Retrieves cached result for a given query."""
        result = self.conn.execute(
            "SELECT result FROM query_cache WHERE query = ?", [query]
        ).fetchone()
        
        if result:
            return json.loads(result[0])  # ✅ Convert JSON string back to dictionary
        return None

    def store_result(self, query: str, result: dict):
        """Stores a new result in the cache."""
        self.conn.execute(
            "INSERT OR REPLACE INTO query_cache (query, result) VALUES (?, ?)",
            [query, json.dumps(result)]
        )
        self.conn.commit()  # ✅ Ensure data is saved

    def clear_cache(self):
        """Deletes all cached queries."""
        self.conn.execute("DELETE FROM query_cache")
        self.conn.commit()
        print("🗑️ Cache cleared!")

# ✅ **Test the Query Cache**
if __name__ == "__main__":
    cache = QueryCache()

    test_query = "Blockchain"
    cached_result = cache.get_cached_result(test_query)

    if cached_result:
        print(f"✅ Cached Result: {cached_result}")
    else:
        print("🔄 Query not found in cache. Storing result...")
        test_result = {"papers": ["Paper 1", "Paper 2", "Paper 3"]}  # Simulated result
        cache.store_result(test_query, test_result)
        print("✅ Result stored!")
