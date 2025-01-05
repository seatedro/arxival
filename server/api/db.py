import os
import libsql_experimental as libsql
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Create client once at startup
client = libsql.connect(
    database=os.getenv("TURSO_URL", ""), auth_token=os.getenv("TURSO_TOKEN", "")
)


async def get_chat_context(session_id: str) -> Dict[str, List[str]]:
    """Fetch chat history and extract paper context from a session."""

    query = f"""
    SELECT m.type, m.content, m.metadata
    FROM messages m
    WHERE m.session_id = '{session_id}'
    ORDER BY m.created_at ASC
    """

    results = client.execute(query).fetchall()

    responses = []
    queries = []

    for result in results:
        if result[0] == "response":
            responses.append(result[1])
        elif result[0] == "query":
            queries.append(result[1])

    return {"responses": responses, "queries": queries}
