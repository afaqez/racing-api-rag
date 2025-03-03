import os
import openai
from app.core.logging import logger

openai.api_key = os.environ.get("OPENAI_API_KEY")


def generate_response(query: str, context: str) -> str:
    """
    Generate a natural language response using GPT-4 based on the query and context.
    """
    logger.info("Using GPT-4 to generate response")
    logger.info(f"Generating response for query: {query}")
    logger.info(f"Context: {context}")
    try:
        system_prompt = """You are a knowledgeable horse racing assistant. Using the provided race information, 
        answer questions accurately and naturally. Focus on the most relevant details from the context provided. 
        If you're not sure about something, say so rather than making assumptions."""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
            Context about races:
            {context}
            
            User question: {query}
            
            Please provide a natural, informative response based on this information.""",
            },
        ]

        response = openai.chat.completions.create(
            model="gpt-4", messages=messages, temperature=0.7, max_tokens=500
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating GPT response: {str(e)}")
        return "I apologize, but I encountered an error generating a response. Please try again."
