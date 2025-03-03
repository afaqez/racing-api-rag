from sqlalchemy import text
from app.utils.embedding import generate_embedding
from app.utils.helpers import cosine_similarity
from app.utils.llm import generate_response
from app.core.logging import logger


def retrieve_context_from_pgvector(query: str, db, top_k: int = 5):
    """
    Generate an embedding for the query and run a SQL query against the
    racecard_embeddings table (using pgvector) to return the top_k closest matches.
    """
    query_embedding = generate_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for the query.")
        return []

    sql = text(
        """
        WITH query_embedding AS (
            SELECT CAST(:query_embedding AS vector(1536)) AS qemb
        )
        SELECT r.race_id, 
               rc.race_name,
               rc.course,
               rc.date,
               rc.distance,
               rc.going,
               rc.raw_data,
               (r.embedding <-> (SELECT qemb FROM query_embedding)) AS distance
        FROM racecard_embeddings r
        JOIN racecards rc ON r.race_id = rc.race_id
        ORDER BY r.embedding <-> (SELECT qemb FROM query_embedding)
        LIMIT :top_k
    """
    )

    try:
        result = db.execute(sql, {"query_embedding": query_embedding, "top_k": top_k})
        rows = result.fetchall()
        logger.info(f"Found {len(rows)} similar races")
        return rows
    except Exception as e:
        logger.error(f"Error querying vector database: {str(e)}")
        return []


def process_query(query: str, chat_history: str, db) -> str:
    """
    Process the query using vector similarity search and GPT-4 for natural language responses.
    """
    if not chat_history.strip():
        use_retrieval = True
    else:
        query_embedding = generate_embedding(query)
        history_embedding = generate_embedding(chat_history)
        similarity = cosine_similarity(query_embedding, history_embedding)
        logger.info(
            "Cosine similarity between query and chat history: %.3f", similarity
        )
        use_retrieval = similarity < 0.5

    if use_retrieval:
        retrieved = retrieve_context_from_pgvector(query, db, top_k=5)
        if not retrieved:
            return "I couldn't find any relevant races to answer your question."

        # Format detailed context for GPT
        context_parts = []
        for row in retrieved:
            race_info = [
                f"Race: {row.race_name}",
                f"Course: {row.course}",
                f"Date: {row.date}",
                f"Distance: {row.distance}",
                f"Going: {row.going}",
            ]

            # Add runner information if available
            if row.raw_data and "runners" in row.raw_data:
                runners = row.raw_data["runners"]
                race_info.append("Runners:")
                for runner in runners:
                    race_info.append(
                        f"  - {runner.get('horse_name', 'N/A')} "
                        f"(Jockey: {runner.get('jockey_name', 'N/A')}, "
                        f"Trainer: {runner.get('trainer_name', 'N/A')})"
                    )

            context_parts.append("\n".join(race_info))

        detailed_context = "\n\n".join(context_parts)

        # Generate natural language response using GPT-4
        response = generate_response(query, detailed_context)
        logger.info("Generated GPT response based on retrieved context")
        return response
    else:
        return generate_response(query, chat_history)
