from typing import Dict, Any, Union
import os
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenAIWrapper:
    """Wrapper for OpenAI Responses API with structured outputs."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def _create_json_schema(self, pydantic_model: BaseModel) -> Dict[str, Any]:
        """Convert Pydantic model to JSON schema for structured outputs."""
        schema = pydantic_model.model_json_schema()
        
        # Ensure additionalProperties is false for all objects to meet OpenAI's strict requirements
        def fix_schema(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "object" and "additionalProperties" not in obj:
                    obj["additionalProperties"] = False
                for key, value in obj.items():
                    fix_schema(value)
            elif isinstance(obj, list):
                for item in obj:
                    fix_schema(item)
        
        fix_schema(schema)
        
        return {
            "type": "json_schema",
            "name": pydantic_model.__name__,
            "strict": True,
            "schema": schema
        }
    
    def generate_text(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate plain text response."""
        resp = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature
        )
        return resp.output_text
    
    def generate_structured(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema."""
        resp = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": self._create_json_schema(schema_model)},
            temperature=temperature
        )
        return schema_model.model_validate(resp.output_parsed)
    
    async def generate_text_async(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate plain text response asynchronously."""
        resp = await self.async_client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature
        )
        return resp.output_text
    
    async def generate_structured_async(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema asynchronously."""
        resp = await self.async_client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": self._create_json_schema(schema_model)},
            temperature=temperature
        )
        return schema_model.model_validate(resp.output_parsed)
    
    
