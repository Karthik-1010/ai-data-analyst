import json
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool
from typing import Optional


# Module-level reference set by the agent before invocation
_db_session: Optional[AsyncSession] = None
_user_id: Optional[int] = None
_user_role: Optional[str] = None


def set_context(db: AsyncSession, user_id: int, user_role: str):
    """Set the database session and user context for tool execution."""
    global _db_session, _user_id, _user_role
    _db_session = db
    _user_id = user_id
    _user_role = user_role


@tool
async def sql_query(query: str) -> str:
    """Execute a read-only SQL SELECT query against the data_records table.
    
    Args:
        query: A SQL SELECT query string. Only SELECT statements are allowed.
        
    Returns:
        JSON string of query results or error message.
    """
    global _db_session, _user_id, _user_role

    if not _db_session:
        return "Error: No database session available."

    # Safety: only allow SELECT
    cleaned = query.strip().upper()
    if not cleaned.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed. No data modification permitted."

    # Block dangerous keywords
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "EXEC"]
    for keyword in dangerous:
        if keyword in cleaned:
            return f"Error: {keyword} operations are not allowed."

    # RBAC: inject user_id filter for non-admin users
    if _user_role != "admin":
        # Add WHERE clause if not present, or AND to existing WHERE
        if "WHERE" in cleaned:
            query = query.rstrip(";") + f" AND user_id = {_user_id}"
        else:
            # Find the right place to inject WHERE
            query = query.rstrip(";")
            # Simple injection before GROUP BY, ORDER BY, or LIMIT
            for clause in ["GROUP BY", "ORDER BY", "LIMIT", "HAVING"]:
                if clause in query.upper():
                    idx = query.upper().index(clause)
                    query = query[:idx] + f" WHERE user_id = {_user_id} " + query[idx:]
                    break
            else:
                query += f" WHERE user_id = {_user_id}"

    try:
        result = await _db_session.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()

        if not rows:
            return "No data found for this query."

        data = [dict(zip(columns, row)) for row in rows]

        # Convert dates to strings for JSON serialization
        for record in data:
            for key, value in record.items():
                if hasattr(value, "isoformat"):
                    record[key] = value.isoformat()

        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return f"Query error: {str(e)}"


@tool
async def analyze_data(data_json: str, analysis_type: str = "summary") -> str:
    """Analyze data using pandas for statistical insights.
    
    Args:
        data_json: JSON string of data to analyze (from sql_query results).
        analysis_type: Type of analysis - "summary", "trends", "top", or "comparison".
        
    Returns:
        String with analysis results.
    """
    try:
        data = json.loads(data_json)
        if not data:
            return "No data to analyze."

        df = pd.DataFrame(data)

        if analysis_type == "summary":
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) == 0:
                return f"Data has {len(df)} rows. Columns: {', '.join(df.columns)}"

            stats = df[numeric_cols].describe().round(2)
            return f"Data summary ({len(df)} records):\n{stats.to_string()}"

        elif analysis_type == "trends":
            if "record_date" in df.columns or "month" in df.columns:
                date_col = "record_date" if "record_date" in df.columns else "month"
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                if numeric_cols:
                    trend = df.groupby(date_col)[numeric_cols[0]].mean().round(2)
                    return f"Trend for {numeric_cols[0]}:\n{trend.to_string()}"
            return "No date column found for trend analysis."

        elif analysis_type == "top":
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                top = df.nlargest(5, col)
                return f"Top 5 by {col}:\n{top.to_string(index=False)}"
            return "No numeric columns to rank."

        elif analysis_type == "comparison":
            if "department" in df.columns:
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                if numeric_cols:
                    comparison = df.groupby("department")[numeric_cols].mean().round(2)
                    return f"Department comparison:\n{comparison.to_string()}"
            return "No department column for comparison."

        return f"Data has {len(df)} rows and {len(df.columns)} columns."

    except json.JSONDecodeError:
        return "Error: Invalid JSON data provided."
    except Exception as e:
        return f"Analysis error: {str(e)}"
