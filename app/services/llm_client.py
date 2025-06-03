import logging
from typing import Optional
from pydantic import BaseModel
import openai
from ..config import settings
import json

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
        # TODO Implement OpenAI client setup
        self.model = "PUT ACTUAL OPENAI MODEL HERE"
        logger.info(f"Initialized LLM client with model: {model}")
    
    async def get_tags(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 500
    ) -> LLMResponse:
        """
        Call OpenAI API to get event tags
        TODO Implement API calling logic
        """
        try:
            # TODO: Implement OpenAI API call
            # 1. Format messages properly
            # 2. Handle different prompt types
            # 3. Parse response
            # 4. Handle errors and retries
            
            logger.info(f"Calling OpenAI API with model {self.model}")

            response = {
                "object": "chat.completion",
                "id": "chatcmpl-AyPNinnUqUDYo9SAdA52NobMflmj2",
                "model": "gpt-4o-2024-08-06",
                "created": 1738960610,
                "request_id": "req_ded8ab984ec4bf840f37566c1011c417",
                "tool_choice": None,
                "usage": {
                    "total_tokens": 31,
                    "completion_tokens": 18,
                    "prompt_tokens": 13
                },
                "seed": 4944116822809979520,
                "top_p": 1.0,
                "temperature": 1.0,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "system_fingerprint": "fp_50cad350e4",
                "input_user": None,
                "service_tier": "default",
                "tools": None,
                "metadata": {
                    "foo": "bar"
                },
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "content": "{\n"
                                    "\"TAG1\": \"PROGRAMMERING_OG_SOFTWAREUDVIKLING\",\n"
                                    "\"TAG2\": \"\",\n"
                                    "\"TAG3\": \"\",\n"
                                    "\"CONFIDENCE\": -1,\n"
                                    "\"REASONING\": \"Bare fordi\"\n"
                                    "}",
                            "role": "assistant",
                            "tool_calls": None,
                            "function_call": None
                        },
                        "finish_reason": "stop",
                        "logprobs": None
                    }
                ],
                "response_format": None
            }

            logger.info(response.keys())
            
            # JSON placeholder
            return LLMResponse(
                content=response["choices"][0]["message"]["content"],
                tokens_used=response["usage"]["total_tokens"],
                model=response["model"],
                finish_reason=response["choices"][0]["finish_reason"]
            )
        
            # For the response object from OpenAI:
            """
            return LLMResponse(
                content=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=response.model,
                finish_reason=response.choices[0].finish_reason
            )"""
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise