# shared_libs/atomic/tools/sql_tool.py

import sqlite3 # Example database connector
import asyncio
from typing import Any, Dict, List
import logging
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor

from shared_libs.base.base_tool import BaseTool
from shared_libs.exceptions import SecurityError, ToolExecutionError
from shared_libs.schemas.tool.sql_tool_schema import SQLToolInput, SQLToolOutput

logger = logging.getLogger(__name__)

# --- Configuration for security enforcement ---
# List of DDL/DML keywords to block (Least Privilege enforcement)
BLOCKED_KEYWORDS = {'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE'}

class SQLTool(BaseTool):
    """
    A hardened SQL tool for read-only database queries.
    Enforces least privilege and prevents SQL Injection via keyword blocking.
    """

    # --- BaseTool Properties ---
    @property
    def name(self) -> str:
        return "sql_query_executor"

    @property
    def description(self) -> str:
        return "Execute read-only SQL SELECT queries against the central data warehouse to retrieve specific data."

    @property
    def input_schema(self) -> BaseModel:
        return SQLToolInput

    @property
    def output_schema(self) -> BaseModel:
        return SQLToolOutput

    def __init__(self, db_config: Dict[str, str]):
        # Store DB connection string/config (connection should use SELECT-only user)
        self.db_config = db_config 
        self.db_path = db_config.get("database_path", ":memory:")
        # Use ThreadPoolExecutor for offloading blocking synchronous I/O
        self.executor = ThreadPoolExecutor(max_workers=1)

    # --- Security Check (HARDENING) ---
    def _check_security(self, query: str):
        """Checks the query for blocked keywords to enforce read-only access."""
        upper_query = query.upper()
        for keyword in BLOCKED_KEYWORDS:
            if keyword in upper_query:
                logger.error(f"Security violation detected: Blocked keyword '{keyword}' found in query.")
                raise SecurityError(
                    f"Query contains the dangerous keyword '{keyword}'. Only SELECT queries are permitted."
                )
        # Enforce SELECT-only start
        if not upper_query.strip().startswith('SELECT'):
            raise SecurityError("Query must start with 'SELECT'. DML/DDL operations are forbidden.")

    # --- Execution Logic ---
    
    def _execute(self, validated_input: SQLToolInput) -> Dict[str, Any]:
        """Synchronous, internal execution of the validated query."""
        query = validated_input.sql_query
        
        # 1. Security Check before execution
        self._check_security(query)
        
        # 2. Execute query safely
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Fetch column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch data and format as list of dictionaries
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # 3. Format output via Pydantic schema
            return SQLToolOutput(
                query_result=data,
                rows_returned=len(data)
            ).model_dump()
        except SecurityError:
            # Re-raise the SecurityError directly
            raise
        except Exception as e:
            logger.error(f"SQL execution failed for query: {query}. Error: {e}")
            raise ToolExecutionError(f"Database error occurred: {e}") from e
        finally:
            if conn:
                conn.close()

    async def _async_execute(self, validated_input: SQLToolInput) -> Dict[str, Any]:
        """Asynchronous execution by offloading the blocking I/O to a thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._execute, validated_input)