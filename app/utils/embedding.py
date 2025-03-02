# app/utils/embedding.py
import os
import openai
from app.core.logging import logger

openai.api_key = os.environ.get("OPENAI_API_KEY")


def generate_embedding(text: str) -> list:
    try:
        logger.info(f"Generating embedding for text: {text}")
        response = openai.embeddings.create(input=text, model="text-embedding-3-small")
        embedding = response.data[0].embedding
        logger.info("Successfully generated embedding")
        return embedding
    except Exception as e:
        logger.error("Error generating embedding: %s", str(e))
        return []
