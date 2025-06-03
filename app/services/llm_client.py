import logging
from typing import Optional
from pydantic import BaseModel
import openai
from ..config import settings

logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    content: str
    tokens_used: int
    model: str
    finish_reason: str

class LLMClient:
    """
    Service for calling OpenAI API
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        # TODO Task 3: Implement OpenAI client setup
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized LLM client with model: {model}")
    
    async def get_tags(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 500
    ) -> LLMResponse:
        """
        Call OpenAI API to get event tags
        TODO Task 3: Implement API calling logic
        """
        try:
            # TODO: Implement OpenAI API call
            # 1. Format messages properly
            # 2. Handle different prompt types
            # 3. Parse response
            # 4. Handle errors and retries
            
            logger.info(f"Calling OpenAI API with model {self.model}")
            
            # Placeholder implementation
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at tagging events."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=response.model,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise