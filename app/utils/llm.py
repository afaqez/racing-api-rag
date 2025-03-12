import os
import openai
from app.core.logging import logger

openai.api_key = os.environ.get("OPENAI_API_KEY")


def generate_response(query: str, context: str, system_prompt: str = None) -> str:
    """
    Generate a natural language response using GPT-4 based on the query and context.
    """
    logger.info("Using GPT-4 to generate response")
    logger.info(f"Generating response for query: {query}")
    logger.info(f"Context: {context}")
    
    try:
        # Use provided system prompt or fall back to default
        if system_prompt is None:
            system_prompt = """You are an expert horse racing assistant with deep knowledge of racing forms, odds, horses, jockeys, trainers, and betting strategies. 
            
            Answer questions based ONLY on the provided context information. If the context doesn't contain enough information to answer the question fully, acknowledge the limitations and provide the best answer you can with the available data.
            
            When discussing:
            - HORSES: Include details about name, age, sex, color, pedigree (sire/dam), trainer, owner, form, and past performances when available.
            - RACES: Include details about race name, course, date, distance, going, surface, class, type, prize money, and runners when available.
            - ODDS: Present odds in both fractional (e.g., 5/1) and decimal (e.g., 6.0) formats when available.
            - FORM: Explain what the form figures mean (e.g., 1=win, 2=second, 0=unplaced, P=pulled up, F=fell, etc.) when discussing a horse's form.
            
            For betting-related questions:
            - Clearly state that you're providing information, not betting advice
            - Explain the reasoning behind any selections you discuss
            - Present multiple options when appropriate
            - Mention relevant factors like going, distance, class, and recent form
            
            For statistical questions:
            - Present data in a clear, organized manner
            - Use tables when appropriate for comparing multiple horses/races
            - Highlight notable trends or patterns
            
            For questions about today's races:
            - Be specific about which races are happening today
            - Provide details about race times, courses, and conditions
            - List the runners and their odds when available
            - Highlight any notable horses, jockeys, or trainers
            
            Always maintain a professional, knowledgeable tone while being accessible to both racing experts and newcomers.
            
            If you cannot answer a question due to missing information, suggest what data would be needed to provide a complete answer.
            """

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""
            Context about races and horses:
            {context}
            
            User question: {query}
            
            Please provide a detailed, informative response based on this information.""",
            },
        ]

        response = openai.chat.completions.create(
            model="gpt-4", messages=messages, temperature=0.7, max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating GPT response: {str(e)}")
        return "I apologize, but I encountered an error generating a response. Please try again."
