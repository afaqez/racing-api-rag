from sqlalchemy import text
from app.utils.embedding import generate_embedding
from app.utils.helpers import cosine_similarity
from app.utils.llm import generate_response
from app.core.logging import logger
import json


def retrieve_context_from_pgvector(query: str, db, top_k: int = 5):
    """
    Generate an embedding for the query and run SQL queries against both
    racecard_embeddings and horse_embeddings tables to return the most relevant matches.
    """
    query_embedding = generate_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for the query.")
        return {"racecards": [], "horses": []}

    # Format the embedding as a PostgreSQL array literal with square brackets
    embedding_array = f"[{','.join(str(x) for x in query_embedding)}]"
    
    # Query for similar racecards
    try:
        # First check if the tables exist
        racecard_table_exists = db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'racecard_embeddings')"
        )).scalar()
        
        horse_table_exists = db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'horse_embeddings')"
        )).scalar()
        
        racecards = []
        horses = []
        
        if racecard_table_exists:
            # Query for similar racecards using direct SQL with the embedding array
            racecard_sql = text(f"""
                SELECT r.race_id, 
                       rc.race_name,
                       rc.course,
                       rc.date,
                       rc.distance,
                       rc.going,
                       rc.surface,
                       rc.race_class,
                       rc.race_type,
                       rc.prize,
                       rc.raw_data
                FROM racecard_embeddings r
                JOIN racecards rc ON r.race_id = rc.race_id
                ORDER BY r.embedding <-> '{embedding_array}'::vector
                LIMIT :top_k
            """)
            racecard_result = db.execute(racecard_sql, {"top_k": top_k})
            racecards = racecard_result.fetchall()
            logger.info(f"Found {len(racecards)} similar races")
        
        if horse_table_exists:
            # Query for similar horses using direct SQL with the embedding array
            horse_sql = text(f"""
                SELECT h.horse_id, 
                       h.name,
                       h.dob,
                       h.age,
                       h.sex,
                       h.colour,
                       h.region,
                       h.sire,
                       h.dam,
                       h.damsire,
                       h.trainer,
                       h.owner,
                       h.form,
                       h.last_run,
                       h.raw_data
                FROM horse_embeddings e
                JOIN horses h ON e.horse_id = h.horse_id
                ORDER BY e.embedding <-> '{embedding_array}'::vector
                LIMIT :top_k
            """)
            horse_result = db.execute(horse_sql, {"top_k": top_k})
            horses = horse_result.fetchall()
            logger.info(f"Found {len(horses)} similar horses")
        
        return {
            "racecards": racecards,
            "horses": horses
        }
    except Exception as e:
        logger.error(f"Error querying vector database: {str(e)}")
        return {"racecards": [], "horses": []}


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
        # Increase top_k for more comprehensive context
        retrieved = retrieve_context_from_pgvector(query, db, top_k=5)
        
        if not retrieved["racecards"] and not retrieved["horses"]:
            return "I couldn't find any relevant information to answer your question. Our database currently contains information about horses and upcoming races, but we don't yet have comprehensive historical results data."

        # Format detailed context for GPT
        context_parts = []
        
        # Add racecard information
        if retrieved["racecards"]:
            context_parts.append("## RACE INFORMATION:")
            for row in retrieved["racecards"]:
                race_info = [
                    f"Race: {row.race_name}",
                    f"Course: {row.course}",
                    f"Date: {row.date}",
                    f"Distance: {row.distance}",
                    f"Going: {row.going}",
                ]
                
                if hasattr(row, 'surface') and row.surface:
                    race_info.append(f"Surface: {row.surface}")
                if hasattr(row, 'race_class') and row.race_class:
                    race_info.append(f"Class: {row.race_class}")
                if hasattr(row, 'race_type') and row.race_type:
                    race_info.append(f"Type: {row.race_type}")
                if hasattr(row, 'prize') and row.prize:
                    race_info.append(f"Prize: {row.prize}")
                if hasattr(row, 'field_size') and row.field_size:
                    race_info.append(f"Field Size: {row.field_size}")

                # Add runner information if available
                if row.raw_data and "runners" in row.raw_data:
                    runners = row.raw_data["runners"]
                    race_info.append("\nRunners:")
                    for runner in runners:
                        runner_info = [f"  - Horse: {runner.get('horse', 'N/A')}"]
                        
                        # Add horse ID if available
                        if runner.get('horse_id'):
                            runner_info.append(f"    ID: {runner.get('horse_id')}")
                        
                        # Add jockey if available
                        if runner.get('jockey'):
                            runner_info.append(f"    Jockey: {runner.get('jockey')}")
                            
                        # Add trainer if available
                        if runner.get('trainer'):
                            runner_info.append(f"    Trainer: {runner.get('trainer')}")
                            
                        # Add weight if available
                        if runner.get('weight'):
                            runner_info.append(f"    Weight: {runner.get('weight')}")
                            
                        # Add draw if available
                        if runner.get('draw'):
                            runner_info.append(f"    Draw: {runner.get('draw')}")
                            
                        # Add odds if available
                        odds = runner.get('odds', [])
                        if odds and isinstance(odds, list) and len(odds) > 0:
                            fraction = odds[0].get('fraction', 'N/A')
                            decimal = odds[0].get('decimal', 'N/A')
                            runner_info.append(f"    Odds: {fraction} (decimal: {decimal})")
                            
                        race_info.extend(runner_info)

                context_parts.append("\n".join(race_info))
        
        # Add horse information
        if retrieved["horses"]:
            context_parts.append("\n## HORSE INFORMATION:")
            for row in retrieved["horses"]:
                horse_info = [
                    f"Horse: {row.name}",
                    f"ID: {row.horse_id}",
                ]
                
                # Add basic information
                if hasattr(row, 'dob') and row.dob:
                    horse_info.append(f"Date of Birth: {row.dob}")
                if hasattr(row, 'age') and row.age:
                    horse_info.append(f"Age: {row.age}")
                if hasattr(row, 'sex') and row.sex:
                    horse_info.append(f"Sex: {row.sex}")
                if hasattr(row, 'colour') and row.colour:
                    horse_info.append(f"Colour: {row.colour}")
                if hasattr(row, 'region') and row.region:
                    horse_info.append(f"Region: {row.region}")
                    
                # Add pedigree information
                pedigree_info = []
                if hasattr(row, 'sire') and row.sire:
                    pedigree_info.append(f"Sire: {row.sire}")
                if hasattr(row, 'dam') and row.dam:
                    pedigree_info.append(f"Dam: {row.dam}")
                if hasattr(row, 'damsire') and row.damsire:
                    pedigree_info.append(f"Damsire: {row.damsire}")
                if pedigree_info:
                    horse_info.append("\nPedigree:")
                    horse_info.extend([f"  - {info}" for info in pedigree_info])
                    
                # Add connections
                connections = []
                if hasattr(row, 'trainer') and row.trainer:
                    connections.append(f"Trainer: {row.trainer}")
                if hasattr(row, 'owner') and row.owner:
                    connections.append(f"Owner: {row.owner}")
                if connections:
                    horse_info.append("\nConnections:")
                    horse_info.extend([f"  - {info}" for info in connections])
                    
                # Add form information
                if hasattr(row, 'form') and row.form:
                    horse_info.append(f"\nForm: {row.form}")
                if hasattr(row, 'last_run') and row.last_run:
                    horse_info.append(f"Last Run: {row.last_run}")
                
                context_parts.append("\n".join(horse_info))

        # Add a note about data limitations
        context_parts.append("\n## DATA LIMITATIONS NOTE:")
        context_parts.append("The database currently contains information about horses and upcoming races, but comprehensive historical results data is not yet available. This may limit the ability to answer questions about past performances, statistics, and trends.")

        detailed_context = "\n\n".join(context_parts)

        # Generate natural language response using GPT-4
        response = generate_response(query, detailed_context)
        logger.info("Generated GPT response based on retrieved context")
        return response
    else:
        return generate_response(query, chat_history)
