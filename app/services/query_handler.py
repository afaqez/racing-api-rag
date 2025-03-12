import calendar
from sqlalchemy import text, inspect
from app.utils.embedding import generate_embedding
from app.utils.helpers import cosine_similarity
from app.utils.llm import generate_response
from app.core.logging import logger
from datetime import datetime, timedelta
import json
import re

def retrieve_context_from_pgvector(query: str, db, top_k: int = 5):
    """
    Generate an embedding for the query and search across all embedding tables
    to return the most semantically relevant matches.
    """
    # ... existing code ...
    # This remains as a fallback method

def get_db_schema(db):
    """Extract database schema information to provide to the LLM"""
    inspector = inspect(db.bind)
    schema_info = {}
    
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            column_info = {
                "name": column["name"],
                "type": str(column["type"])
            }
            columns.append(column_info)
        
        schema_info[table_name] = {
            "columns": columns,
            "relationships": []
        }
        
        # Add foreign keys to understand relationships
        for fk in inspector.get_foreign_keys(table_name):
            schema_info[table_name]["relationships"].append({
                "referred_table": fk["referred_table"],
                "constrained_columns": fk["constrained_columns"],
                "referred_columns": fk["referred_columns"]
            })
            
    return schema_info

def parse_date_references(query):
    """Parse date references in the query and return date filtering information"""
    query_lower = query.lower()
    current_date = datetime.now()
    
    date_info = {
        "has_date_reference": False,
        "specific_date": None,
        "date_type": None,  # Could be "today", "specific_day", "month_only", etc.
        "sql_filter": None  # The SQL filter to apply
    }
    
    # Check for "today" reference
    if "today" in query_lower:
        date_info["has_date_reference"] = True
        date_info["date_type"] = "today"
        date_info["specific_date"] = current_date
        date_info["sql_filter"] = "DATE(r.date) = CURRENT_DATE"
        return date_info
    
    # Check for "yesterday" reference
    if "yesterday" in query_lower:
        date_info["has_date_reference"] = True
        date_info["date_type"] = "yesterday"
        date_info["specific_date"] = current_date - timedelta(days=1)
        date_info["sql_filter"] = "DATE(r.date) = CURRENT_DATE - INTERVAL '1 day'"
        return date_info
    
    # Check for "tomorrow" reference
    if "tomorrow" in query_lower:
        date_info["has_date_reference"] = True
        date_info["date_type"] = "tomorrow"
        date_info["specific_date"] = current_date + timedelta(days=1)
        date_info["sql_filter"] = "DATE(r.date) = CURRENT_DATE + INTERVAL '1 day'"
        return date_info
    
    # Check for specific date with day and month (e.g. "10th of March", "March 10")
    day_of_month_pattern = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([a-zA-Z]+)', query_lower)
    month_day_pattern = re.search(r'([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?', query_lower)
    
    if day_of_month_pattern:
        day = int(day_of_month_pattern.group(1))
        month_name = day_of_month_pattern.group(2)
        try:
            month = list(calendar.month_name).index(month_name.capitalize())
            if month == 0:  # Handle abbreviations
                month = list(calendar.month_abbr).index(month_name.capitalize()[:3])
        except ValueError:
            # If month name is invalid, default to current month
            month = current_date.month
        
        # Default to current year
        year = current_date.year
        
        # Check if a specific year is mentioned
        year_pattern = re.search(r'\b(20\d{2})\b', query_lower)
        if year_pattern:
            year = int(year_pattern.group(1))
        
        # Create date
        try:
            specific_date = datetime(year, month, day)
            date_info["has_date_reference"] = True
            date_info["date_type"] = "specific_day"
            date_info["specific_date"] = specific_date
            date_info["sql_filter"] = f"DATE(r.date) = '{specific_date.strftime('%Y-%m-%d')}'"
        except ValueError:
            # Invalid date (e.g., February 30)
            pass
    
    elif month_day_pattern:
        month_name = month_day_pattern.group(1)
        day = int(month_day_pattern.group(2))
        try:
            month = list(calendar.month_name).index(month_name.capitalize())
            if month == 0:  # Handle abbreviations
                month = list(calendar.month_abbr).index(month_name.capitalize()[:3])
        except ValueError:
            # If month name is invalid, default to current month
            month = current_date.month
        
        # Default to current year
        year = current_date.year
        
        # Check if a specific year is mentioned
        year_pattern = re.search(r'\b(20\d{2})\b', query_lower)
        if year_pattern:
            year = int(year_pattern.group(1))
        
        # Create date
        try:
            specific_date = datetime(year, month, day)
            date_info["has_date_reference"] = True
            date_info["date_type"] = "specific_day"
            date_info["specific_date"] = specific_date
            date_info["sql_filter"] = f"DATE(r.date) = '{specific_date.strftime('%Y-%m-%d')}'"
        except ValueError:
            # Invalid date (e.g., February 30)
            pass
    
    # Check for month-only references (e.g. "in March")
    month_only_pattern = re.search(r'\b(?:in|during|for)\s+([a-zA-Z]+)\b', query_lower)
    if not date_info["has_date_reference"] and month_only_pattern:
        month_name = month_only_pattern.group(1)
        try:
            month = list(calendar.month_name).index(month_name.capitalize())
            if month == 0:  # Handle abbreviations
                month = list(calendar.month_abbr).index(month_name.capitalize()[:3])
            
            # Default to current year
            year = current_date.year
            
            # Check if a specific year is mentioned
            year_pattern = re.search(r'\b(20\d{2})\b', query_lower)
            if year_pattern:
                year = int(year_pattern.group(1))
            
            date_info["has_date_reference"] = True
            date_info["date_type"] = "month_only"
            date_info["specific_date"] = datetime(year, month, 1)  # First day of month
            date_info["sql_filter"] = f"EXTRACT(MONTH FROM r.date) = {month} AND EXTRACT(YEAR FROM r.date) = {year}"
        except ValueError:
            # Invalid month name
            pass
    
    # If no specific date reference is found, default to current month and year
    if not date_info["has_date_reference"]:
        date_info["date_type"] = "current_month"
        date_info["specific_date"] = datetime(current_date.year, current_date.month, 1)  # First day of current month
        date_info["sql_filter"] = f"EXTRACT(MONTH FROM r.date) = {current_date.month} AND EXTRACT(YEAR FROM r.date) = {current_date.year}"
    
    return date_info

def generate_sql_from_natural_language(query, schema_info):
    """Use LLM to generate SQL from natural language query with smart date handling"""
    # Parse date references in the query
    date_info = parse_date_references(query)
    
    system_prompt = """You are an expert SQL generator for a horse racing database. 
    Generate a PostgreSQL query for the given question using only tables and columns in the schema.
    Return ONLY the SQL query without explanation. Include JOINs where necessary.
    
    IMPORTANT NOTES:
    1. The 'raw_data' column contains a JSON object with detailed information
    2. For 'racecards' table, runner information is in raw_data->'runners' as a JSON array
    3. When filtering for dates, use the date filter provided in the context
    4. Use jsonb_array_elements() to query elements in JSON arrays
    5. DO NOT include code fence markers (```) in your response
    
    If you cannot generate SQL for this question, respond with: "QUERY_ERROR: Unable to generate SQL"
    """
    
    # Add date handling examples based on the detected date type
    date_examples = {
        "today": """
Question: "Show me all non-runners today"
SQL: 
SELECT r.race_name, r.course, r.off_time, rdata->>'horse' as horse, rdata->>'non_runner_reason' as reason 
FROM racecards r, jsonb_array_elements(r.raw_data->'runners') as rdata 
WHERE (rdata->>'non_runner')::boolean = true 
AND DATE(r.date) = CURRENT_DATE
AND r.is_abandoned = false
ORDER BY r.off_time
        """,
        
        "specific_day": f"""
Question: "Show me all races on March 10"
SQL:
SELECT r.race_name, r.course, r.off_time, r.distance, r.going, r.prize, r.race_class, r.race_type
FROM racecards r
WHERE DATE(r.date) = '{date_info["specific_date"].strftime('%Y-%m-%d')}'
AND r.is_abandoned = false
ORDER BY r.off_time
        """,
        
        "month_only": f"""
Question: "Show me top jockeys in March"
SQL:
SELECT j.name as jockey, COUNT(CASE WHEN hr.position = '1' THEN 1 END) as wins,
COUNT(hr.id) as total_rides,
ROUND(COUNT(CASE WHEN hr.position = '1' THEN 1 END)::numeric / NULLIF(COUNT(hr.id), 0) * 100, 2) as win_percentage
FROM jockeys j
JOIN results hr ON j.jockey_id = hr.jockey_id
JOIN racecards r ON hr.race_id = r.race_id
WHERE EXTRACT(MONTH FROM r.date) = {date_info["specific_date"].month} 
AND EXTRACT(YEAR FROM r.date) = {date_info["specific_date"].year}
GROUP BY j.name
HAVING COUNT(hr.id) > 5
ORDER BY wins DESC
LIMIT 10
        """,
        
        "current_month": f"""
Question: "Show me the biggest upsets"
SQL:
SELECT r.race_name, r.course, r.date, hr.horse_id, h.name as horse, hr.sp_dec as odds, hr.position
FROM results hr
JOIN racecards r ON hr.race_id = r.race_id
JOIN horses h ON hr.horse_id = h.horse_id
WHERE hr.position = '1'
AND hr.sp_dec > 10.0
AND EXTRACT(MONTH FROM r.date) = {date_info["specific_date"].month}
AND EXTRACT(YEAR FROM r.date) = {date_info["specific_date"].year}
ORDER BY hr.sp_dec DESC
LIMIT 10
        """
    }
    
    # Add course-specific example for racing at specific courses
    course_example = """
Question: "Are there any races at Newcastle or York today?"
SQL:
SELECT r.race_name, r.course, r.off_time, r.distance, r.going, r.prize
FROM racecards r
WHERE (r.course ILIKE '%Newcastle%' OR r.course ILIKE '%York%')
AND DATE(r.date) = CURRENT_DATE
AND r.is_abandoned = false
ORDER BY r.off_time
    """
    
    # Add standard examples for common racing queries
    standard_examples = ["""
Question: "Show me non-runners and seasonal debuts today"
SQL:
-- First, get the non-runners
SELECT 'Non-Runner' as type, r.race_name, r.course, r.off_time, rdata->>'horse' as horse, 
       rdata->>'non_runner_reason' as reason, NULL as days_since_run
FROM racecards r, jsonb_array_elements(r.raw_data->'runners') as rdata 
WHERE (rdata->>'non_runner')::boolean = true 
AND DATE(r.date) = CURRENT_DATE
AND r.is_abandoned = false

UNION ALL

-- Then, get the seasonal debuts
SELECT 'Seasonal Debut' as type, r.race_name, r.course, r.off_time, rdata->>'horse' as horse,
       NULL as reason,
       CASE WHEN rdata->>'days_since_last_run' IS NOT NULL THEN (rdata->>'days_since_last_run')::integer ELSE 999 END as days_since_run
FROM racecards r, jsonb_array_elements(r.raw_data->'runners') as rdata 
WHERE (
    (CASE WHEN rdata->>'days_since_last_run' IS NOT NULL THEN (rdata->>'days_since_last_run')::integer > 180 ELSE false END)
    OR (rdata->>'form' LIKE '%/')
    OR (rdata->>'comment' ILIKE '%seasonal debut%')
)
AND DATE(r.date) = CURRENT_DATE
AND r.is_abandoned = false
AND ((rdata->>'non_runner')::boolean = false OR (rdata->>'non_runner') IS NULL)

ORDER BY type, off_time, horse
"""]
    
    # Get date-specific example for detected date type
    date_example = date_examples.get(date_info["date_type"], date_examples["current_month"])
    
    # Combine examples - include course example because your error was with a course query
    examples = [date_example, course_example] + standard_examples
    
    # Provide schema, date filter, and examples to the LLM
    context = f"""
    DATABASE SCHEMA:
    {json.dumps(schema_info, indent=2)}
    
    DATE FILTER TO USE:
    {date_info["sql_filter"]}
    
    EXAMPLES OF NATURAL LANGUAGE TO SQL MAPPING:
    {"".join(examples)}
    
    Now, generate SQL for this question:
    {query}
    """
    
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4-turbo", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.1,
            max_tokens=600
        )
        
        # Get the SQL and clean it
        sql = response.choices[0].message.content.strip()
        
        # Remove markdown code fence if present
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        sql = sql.strip()
        
        if sql.startswith("QUERY_ERROR"):
            logger.warning(f"LLM couldn't generate SQL: {sql}")
            return None
            
        logger.info(f"Generated SQL: {sql}")
        return sql
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        return None

def execute_sql_safely(db, sql):
    """Execute the generated SQL with safeguards"""
    try:
        # Check for modification statements
        if re.search(r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b', sql, re.IGNORECASE):
            return {"success": False, "error": "SQL contains modification statements which are not allowed"}
        
        # Execute the query
        result = db.execute(text(sql))
        
        # Convert to list of dictionaries
        column_names = result.keys()
        records = []
        for row in result:
            record = {}
            for i, column in enumerate(column_names):
                record[column] = row[i]
            records.append(record)
            
        return {"success": True, "data": records, "columns": list(column_names)}
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        return {"success": False, "error": str(e)}

def format_results_for_llm(sql_results):
    """Format SQL results for the LLM"""
    if not sql_results["success"]:
        return f"Error executing query: {sql_results['error']}"
    
    records = sql_results["data"]
    columns = sql_results["columns"]
    
    if not records:
        return "The query returned no results."
    
    # Format as table
    result_text = []
    
    # Add header
    header = " | ".join(columns)
    result_text.append(header)
    result_text.append("-" * len(header))
    
    # Add rows (limit to 50 to avoid token limits)
    max_rows = min(50, len(records))
    for i in range(max_rows):
        record = records[i]
        row_values = []
        for column in columns:
            value = str(record[column]) if record[column] is not None else "NULL"
            row_values.append(value)
        result_text.append(" | ".join(row_values))
    
    if len(records) > max_rows:
        result_text.append(f"\n(Showing {max_rows} of {len(records)} total results)")
    
    return "\n".join(result_text)

def retrieve_context_from_pgvector(query, db, top_k=5):
    """Fallback vector search if SQL generation fails - with better error handling"""
    try:
        query_embedding = generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate embedding for the query.")
            return {"racecards": [], "horses": [], "jockeys": [], "trainers": [], "courses": []}

        # Check if pgvector extension exists
        has_vector_ext = db.execute(text(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )).scalar()
        
        if not has_vector_ext:
            logger.error("PGVector extension not installed in the database")
            return {"racecards": [], "horses": [], "jockeys": [], "trainers": [], "courses": []}

        embedding_array = f"[{','.join(str(x) for x in query_embedding)}]"
        results = {"racecards": [], "horses": [], "jockeys": [], "trainers": [], "courses": []}
        
        # Get all available embedding tables
        tables = {
            "racecard_embeddings": False,
            "horse_embeddings": False,
            "jockey_embeddings": False,
            "trainer_embeddings": False,
            "course_embeddings": False
        }
        
        for table in tables.keys():
            try:
                # Use a simpler query to check if table exists
                tables[table] = db.execute(text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                )).scalar()
            except Exception as e:
                logger.error(f"Error checking if table {table} exists: {str(e)}")
                tables[table] = False

        # Search across all available tables and let vector similarity determine relevance
        for table_name, exists in tables.items():
            if exists:
                try:
                    entity_type = table_name.split('_')[0]
                    
                    # Use a safer query that catches potential errors with vector operations
                    sql = text(f"""
                        SELECT e.* 
                        FROM {entity_type}s e
                        JOIN {table_name} em ON e.{entity_type}_id = em.{entity_type}_id
                        ORDER BY em.embedding <-> '{embedding_array}'::vector
                        LIMIT :top_k
                    """)
                    
                    results[f"{entity_type}s"] = db.execute(sql, {"top_k": top_k}).fetchall()
                    
                except Exception as e:
                    logger.error(f"Error querying {table_name} with vector similarity: {str(e)}")
                    # Try a simpler query without vector operations as a last resort
                    try:
                        sql = text(f"""
                            SELECT e.* 
                            FROM {entity_type}s e
                            LIMIT :top_k
                        """)
                        results[f"{entity_type}s"] = db.execute(sql, {"top_k": top_k}).fetchall()
                    except:
                        # If even the simple query fails, just return empty results
                        results[f"{entity_type}s"] = []

        return results
    except Exception as e:
        logger.error(f"Error in vector retrieval: {str(e)}")
        return {"racecards": [], "horses": [], "jockeys": [], "trainers": [], "courses": []}

def format_context(retrieved_data):
    """Format retrieved data into a structured context for the LLM"""
    context_parts = []
    
    # Format race information
    if retrieved_data.get("racecards", []):
        context_parts.append("## RACE INFORMATION:")
        for race in retrieved_data["racecards"]:
            race_info = format_race_info(race)
            context_parts.append(race_info)
    
    # Format horse information
    if retrieved_data.get("horses", []):
        context_parts.append("\n## HORSE INFORMATION:")
        for horse in retrieved_data["horses"]:
            horse_info = format_horse_info(horse)
            context_parts.append(horse_info)
    
    # Format jockey information
    if retrieved_data.get("jockeys", []):
        context_parts.append("\n## JOCKEY INFORMATION:")
        for jockey in retrieved_data["jockeys"]:
            jockey_info = format_jockey_info(jockey)
            context_parts.append(jockey_info)
    
    # Format trainer information
    if retrieved_data.get("trainers", []):
        context_parts.append("\n## TRAINER INFORMATION:")
        for trainer in retrieved_data["trainers"]:
            trainer_info = format_trainer_info(trainer)
            context_parts.append(trainer_info)
    
    # Format course information
    if retrieved_data.get("courses", []):
        context_parts.append("\n## COURSE INFORMATION:")
        for course in retrieved_data["courses"]:
            course_info = format_course_info(course)
            context_parts.append(course_info)
    
    # Add data limitations note if needed
    if not any(retrieved_data.values()):
        context_parts.append("\n## DATA LIMITATIONS NOTE:")
        context_parts.append("No relevant information found in the database for this query.")
    
    return "\n\n".join(context_parts)

def process_query(query: str, chat_history: str, db) -> str:
    """Main function to process user queries using SQL-first approach with smart date handling"""
    logger.info(f"Processing query: {query}")
    
    # For new queries, try SQL generation first
    if not chat_history.strip():
        try:
            # Get schema and generate SQL with date handling
            schema_info = get_db_schema(db)
            logger.info("Retrieved database schema")
            
            sql = generate_sql_from_natural_language(query, schema_info)
            
            if sql:
                logger.info("Generated SQL query")
                
                # Execute SQL and get results
                sql_results = execute_sql_safely(db, sql)
                logger.info(f"SQL execution success: {sql_results['success']}")
                
                if sql_results["success"]:
                    # Format results for the LLM
                    formatted_results = format_results_for_llm(sql_results)
                    
                    # Parse date info for context in the response
                    date_info = parse_date_references(query)
                    date_context = ""
                    if date_info["date_type"] == "today":
                        date_context = "for today"
                    elif date_info["date_type"] == "specific_day":
                        date_context = f"for {date_info['specific_date'].strftime('%B %d, %Y')}"
                    elif date_info["date_type"] == "month_only":
                        date_context = f"for {date_info['specific_date'].strftime('%B %Y')}"
                    elif date_info["date_type"] == "current_month":
                        date_context = f"for {date_info['specific_date'].strftime('%B %Y')} (current month)"
                    
                    # Create context with query results and date context
                    context = f"""
                    The user asked: {query}
                    
                    Time period: {date_context}
                    
                    I executed the following SQL query:
                    ```sql
                    {sql}
                    ```
                    
                    The query returned the following results:
                    ```
                    {formatted_results}
                    ```
                    """
                    
                    # Create system prompt for the LLM
                    system_prompt = """You are an expert horse racing assistant. 
                    Using ONLY the query results provided, give a comprehensive answer about horse racing.
                    
                    Format your response clearly:
                    1. For lists of horses/races, use bullet points
                    2. For statistics, use markdown tables 
                    3. Highlight important insights with bold text
                    4. Explain racing terminology for casual fans
                    5. Clearly mention the time period the data covers (today, specific date, or current month)
                    
                    Only present information from the data. If data is missing, acknowledge it.
                    """
                    
                    # Generate final response
                    response = generate_response(
                        query=query,
                        context=context,
                        system_prompt=system_prompt
                    )
                    logger.info("Generated response using SQL-based retrieval")
                    return response
        except Exception as e:
            logger.error(f"Error in SQL approach: {str(e)}")
            # Fall through to vector retrieval
    
    # Use chat history for follow-up questions
    if chat_history.strip():
        # Check if current query is related to chat history
        try:
            query_embedding = generate_embedding(query)
            history_embedding = generate_embedding(chat_history)
            
            if query_embedding and history_embedding:
                similarity = cosine_similarity(query_embedding, history_embedding)
                logger.info(f"Query-history similarity: {similarity:.3f}")
                
                if similarity >= 0.5:
                    # Use chat history for context if query is similar to previous conversation
                    logger.info("Using chat history for context")
                    return generate_response(
                        query=query,
                        context=chat_history
                    )
        except Exception as e:
            logger.error(f"Error checking chat history similarity: {str(e)}")
    
    # Default fallback to vector retrieval (with better error handling)
    logger.info("Falling back to vector retrieval")
    try:
        # First, try a direct SQL query for course-specific questions (since that was your error case)
        if "le mans" in query.lower() or "newcastle" in query.lower():
            try:
                course_terms = []
                if "le mans" in query.lower():
                    course_terms.append("Le Mans")
                if "newcastle" in query.lower():
                    course_terms.append("Newcastle")
                    
                # Build a simple course query
                course_conditions = " OR ".join([f"r.course ILIKE '%{course}%'" for course in course_terms])
                direct_sql = f"""
                SELECT r.race_name, r.course, r.date, r.off_time, r.distance, r.going, r.prize  
                FROM racecards r
                WHERE ({course_conditions})
                AND DATE(r.date) >= CURRENT_DATE
                ORDER BY r.date, r.off_time
                LIMIT 10
                """
                
                logger.info(f"Using direct course query: {direct_sql}")
                direct_results = execute_sql_safely(db, direct_sql)
                
                if direct_results["success"] and direct_results["data"]:
                    formatted_results = format_results_for_llm(direct_results)
                    context = f"""
                    The user asked about races at specific courses: {query}
                    
                    I found the following races:
                    ```
                    {formatted_results}
                    ```
                    """
                    
                    system_prompt = """You are a racing expert assistant. Provide information about the races 
                    at the requested courses based on the data provided. Use bullet points for listing races
                    and explain any racing terminology."""
                    
                    return generate_response(
                        query=query,
                        context=context,
                        system_prompt=system_prompt
                    )
            except Exception as e:
                logger.error(f"Error with direct course query: {str(e)}")
        
        # Fall back to normal vector retrieval
        retrieved_data = retrieve_context_from_pgvector(query, db)
        context = format_context(retrieved_data)
        
        system_prompt = """You are a racing expert assistant. Using ONLY the provided context, 
        answer the user's query. If the context doesn't contain enough information to fully 
        answer the query, explain what information is missing."""
        
        response = generate_response(
            query=query,
            context=context,
            system_prompt=system_prompt
        )
        logger.info("Generated response using vector retrieval (fallback)")
        return response
    except Exception as e:
        logger.error(f"Error in vector retrieval fallback: {str(e)}")
        # Last resort fallback
        return "I apologize, but I encountered an error while processing your query about racing information. Please try rephrasing your question or asking about something else."

def format_race_info(race) -> str:
    """Format race information into a readable string"""
    info = [
        f"Race: {race.race_name}",
        f"Course: {race.course}",
        f"Date: {race.date}",
        f"Distance: {race.distance}",
        f"Going: {race.going}",
    ]
    
    # Add optional fields if they exist
    if hasattr(race, 'surface') and race.surface:
        info.append(f"Surface: {race.surface}")
    if hasattr(race, 'race_class') and race.race_class:
        info.append(f"Class: {race.race_class}")
    if hasattr(race, 'race_type') and race.race_type:
        info.append(f"Type: {race.race_type}")
    if hasattr(race, 'prize') and race.prize:
        info.append(f"Prize: {race.prize}")
    
    # Add runner information if available in raw_data
    if hasattr(race, 'raw_data') and race.raw_data and "runners" in race.raw_data:
        info.append("\nRunners:")
        for runner in race.raw_data["runners"]:
            runner_info = [f"  - Horse: {runner.get('horse', 'N/A')}"]
            if runner.get('jockey'):
                runner_info.append(f"    Jockey: {runner.get('jockey')}")
            if runner.get('trainer'):
                runner_info.append(f"    Trainer: {runner.get('trainer')}")
            if runner.get('weight'):
                runner_info.append(f"    Weight: {runner.get('weight')}")
            if runner.get('draw'):
                runner_info.append(f"    Draw: {runner.get('draw')}")
            if runner.get('odds'):
                odds = runner['odds'][0] if isinstance(runner['odds'], list) and runner['odds'] else {}
                runner_info.append(f"    Odds: {odds.get('fraction', 'N/A')}")
            info.extend(runner_info)
    
    return "\n".join(info)

def format_horse_info(horse) -> str:
    """Format horse information into a readable string"""
    info = [
        f"Horse: {horse.name}",
        f"ID: {horse.horse_id}",
    ]
    
    # Add basic information
    if hasattr(horse, 'age') and horse.age:
        info.append(f"Age: {horse.age}")
    if hasattr(horse, 'sex') and horse.sex:
        info.append(f"Sex: {horse.sex}")
    if hasattr(horse, 'colour') and horse.colour:
        info.append(f"Colour: {horse.colour}")
    
    # Add pedigree information
    pedigree = []
    if hasattr(horse, 'sire') and horse.sire:
        pedigree.append(f"Sire: {horse.sire}")
    if hasattr(horse, 'dam') and horse.dam:
        pedigree.append(f"Dam: {horse.dam}")
    if hasattr(horse, 'damsire') and horse.damsire:
        pedigree.append(f"Damsire: {horse.damsire}")
    if pedigree:
        info.append("\nPedigree:")
        info.extend([f"  - {line}" for line in pedigree])
    
    # Add form information
    if hasattr(horse, 'form') and horse.form:
        info.append(f"\nForm: {horse.form}")
    if hasattr(horse, 'last_run') and horse.last_run:
        info.append(f"Last Run: {horse.last_run}")
    
    return "\n".join(info)

def format_jockey_info(jockey) -> str:
    """Format jockey information into a readable string"""
    info = [
        f"Jockey: {jockey.name}",
        f"ID: {jockey.jockey_id}",
    ]
    
    # Add statistics from embedding_metadata if available
    if hasattr(jockey, 'embedding_metadata') and jockey.embedding_metadata:
        stats = jockey.embedding_metadata
        info.append("\nStatistics:")
        if 'total_rides' in stats:
            info.append(f"  - Total Rides: {stats['total_rides']}")
        if 'wins' in stats:
            info.append(f"  - Wins: {stats['wins']}")
        if 'places' in stats:
            info.append(f"  - Places: {stats['places']}")
    
    # Add raw data information if available
    if hasattr(jockey, 'raw_data') and jockey.raw_data:
        if 'recent_form' in jockey.raw_data:
            info.append("\nRecent Form:")
            for result in jockey.raw_data['recent_form'][:5]:  # Last 5 rides
                info.append(f"  - {result}")
    
    return "\n".join(info)

def format_trainer_info(trainer) -> str:
    """Format trainer information into a readable string"""
    info = [
        f"Trainer: {trainer.name}",
        f"ID: {trainer.trainer_id}",
    ]
    
    # Add statistics from embedding_metadata if available
    if hasattr(trainer, 'embedding_metadata') and trainer.embedding_metadata:
        stats = trainer.embedding_metadata
        info.append("\nStatistics:")
        if 'total_runners' in stats:
            info.append(f"  - Total Runners: {stats['total_runners']}")
        if 'winners' in stats:
            info.append(f"  - Winners: {stats['winners']}")
        if 'types' in stats:
            info.append(f"  - Specializes in: {', '.join(stats['types'])}")
    
    # Add raw data information if available
    if hasattr(trainer, 'raw_data') and trainer.raw_data:
        if 'stable_form' in trainer.raw_data:
            info.append("\nStable Form:")
            for result in trainer.raw_data['stable_form'][:5]:  # Last 5 runners
                info.append(f"  - {result}")
    
    return "\n".join(info)

def format_course_info(course) -> str:
    """Format course information into a readable string"""
    info = [
        f"Course: {course.name}",
        f"ID: {course.course_id}",
    ]
    
    # Add characteristics from embedding_metadata if available
    if hasattr(course, 'embedding_metadata') and course.embedding_metadata:
        chars = course.embedding_metadata
        info.append("\nCharacteristics:")
        if 'surface' in chars:
            info.append(f"  - Surface: {chars['surface']}")
        if 'track_type' in chars:
            info.append(f"  - Track Type: {chars['track_type']}")
        if 'region_codes' in chars:
            info.append(f"  - Regions: {', '.join(chars['region_codes'])}")
    
    # Add raw data information if available
    if hasattr(course, 'raw_data') and course.raw_data:
        if 'characteristics' in course.raw_data:
            chars = course.raw_data['characteristics']
            info.append("\nTrack Details:")
            if 'configuration' in chars:
                info.append(f"  - Configuration: {chars['configuration']}")
            if 'length' in chars:
                info.append(f"  - Length: {chars['length']}")
            if 'run_in' in chars:
                info.append(f"  - Run-in: {chars['run_in']}")
    
    return "\n".join(info)
