import json
import logging
import time
from typing import List, MutableSequence
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic import PredictionServiceClient
from google.protobuf.json_format import ParseDict, MessageToDict
from google.protobuf.struct_pb2 import Value
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationResponse, GenerationConfig

from prompts import GET_NOTE_HEADLINE, SUMMARIZE_NOTE_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
PROJECT_ID = "jarvis-8ce89"
REGION = "us-central1"  # Change to your region
vertexai.init(project=PROJECT_ID, location=REGION)

MODEL = "gemini-1.5-flash-002"
client = GenerativeModel(MODEL)

def predict_text(prompt: str) -> str:
    max_retries = 5
    base_delay = 1  # Start with 1 second delay
    for attempt in range(max_retries):
        try:
            logger.info(f"Gemini predicting... (attempt {attempt + 1}/{max_retries})")
            model_response: GenerationResponse = client.generate_content(
                prompt, 
                generation_config=GenerationConfig(temperature=0.7)
            )
            logger.info("Gemini response successful!")
            logger.info(model_response.text)
            return model_response.text
            
        except Exception as e:
            if "429" in str(e) or "quota exceeded" in str(e).lower():
                if attempt == max_retries - 1:
                    logger.error(f"Max retries ({max_retries}) exceeded for Gemini API")
                    raise
                    
                delay = base_delay * (5 ** attempt)  # Exponential backoff
                logger.warning(f"Rate limit hit, retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Unexpected error from Gemini API: {e}")
                raise
    logger.error("Could not predict.")
    return ""

def summarize(notes: List[str]) -> str:
    try:
        # Combine system prompt with notes
        full_prompt = SUMMARIZE_NOTE_PROMPT + "\n\n" + "\n".join(notes)
        return predict_text(full_prompt)
    except Exception as e:
        print(f"Error in summarization: {e}")
        return str(e)

def generate_note_headline(note) -> str:
    try:
        # Combine headline prompt with note
        full_prompt = GET_NOTE_HEADLINE + "\n\n" + note
        return predict_text(full_prompt)
    except Exception as e:
        print(f"Error in headline generation: {e}")
        return str(e)
