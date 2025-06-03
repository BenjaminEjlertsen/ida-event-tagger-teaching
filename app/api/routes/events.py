import logging
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
import json
import time

from ...models.requests import EventTagRequest, BatchTagRequest, EvaluationRequest
from ...models.responses import EventTagResponse, BatchTagResponse, EvaluationResponse
from app.services.initialization import evaluation_data, load_evaluation_data
from app.services.evaluation import evaluate_all
from ...services.event_processor import (
    process_single_event, 
    process_batch_events
)
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/events/test")
async def test_endpoint():
    """Simple test endpoint"""
    logger.info("Test endpoint called!")
    try:
        from ...services.initialization import available_tags
        tags_count = len(available_tags)
    except:
        tags_count = 0
    
    return {
        "status": "success", 
        "message": "Endpoint is working", 
        "tags_loaded": tags_count,
        "log_level": settings.log_level
    }

@router.get("/events/evaluate", response_model=EvaluationResponse)
async def evaluate_tagging_performance():
    """
    Run a full evaluation of tagging performance against the loaded ground truth.
    """
    try:
        logger.info("Starting tagging performance evaluation (GET)...")
        start_time = time.time()

        # Run the full evaluation
        evaluation_response = await evaluate_all()

        # Add processing time (in milliseconds) to the response
        processing_time = (time.time() - start_time) * 1000
        evaluation_response.processing_time_ms = processing_time

        logger.info(f"Evaluation completed in {processing_time:.2f} ms")
        return evaluation_response

    except HTTPException:
        # Re‐raise HTTPExceptions so FastAPI handles them
        raise
    except Exception as e:
        logger.error(f"Error evaluating performance: {e}")
        logger.exception("Full evaluation error:")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/evaluation-data")
async def get_evaluation_data():
    """
    Get available evaluation data for testing
    """
    try:
        from ...services.initialization import evaluation_data
        
        return {
            "total_arrangements": len(evaluation_data),
            "sample_data": evaluation_data[:3] if evaluation_data else [],
            "ground_truth_tags_distribution": _analyze_ground_truth_distribution(evaluation_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting evaluation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _analyze_ground_truth_distribution(data):
    """Helper function to analyze ground truth tag distribution"""
    tag_counts = {}
    for item in data:
        for gt_tag in item['ground_truth_tags']:
            tag = gt_tag['tag']
            priority = gt_tag['priority']
            if tag not in tag_counts:
                tag_counts[tag] = {'total': 0, 'priority_1': 0, 'priority_2': 0, 'priority_3': 0}
            tag_counts[tag]['total'] += 1
            tag_counts[tag][f'priority_{priority}'] += 1
    
    return dict(sorted(tag_counts.items(), key=lambda x: x[1]['total'], reverse=True)[:10])


@router.post("/events/debug-prompt")
async def debug_prompt_generation(request: EventTagRequest):
    """
    Debug endpoint to see generated prompt
    """
    try:
        logger.info("=== DEBUG PROMPT GENERATION ===")
        
        from ...services.initialization import prompt_generator, available_tags
        
        if not prompt_generator:
            return {"error": "Prompt generator not initialized"}
        
        # Generate the prompt
        prompt_response = await prompt_generator.generate_tagging_prompt(request)
        
        return {
            "status": "success",
            "prompt": prompt_response.prompt,
            "available_tags_count": len(prompt_response.available_tags),
            "sample_available_tags": prompt_response.available_tags[:5],
            "arrangement_data": {
                "titel": request.arrangement_titel,
                "arrangør": request.arrangør,
                "teaser": request.nc_teaser
            }
        }
        
    except Exception as e:
        logger.error(f"Debug prompt error: {e}")
        logger.exception("Full error:")
        return {"error": str(e)}

@router.post("/events/debug")
async def debug_arrangement_request(request: dict):
    """
    Debug endpoint to see raw request data
    """
    try:
        logger.info(f"=== DEBUG ENDPOINT CALLED ===")
        logger.info(f"Raw request data: {request}")
        logger.info(f"Request type: {type(request)}")
        
        # Try to create EventTagRequest from the data
        try:
            arrangement = EventTagRequest(**request)
            logger.info("Successfully created EventTagRequest!")
            return {
                "status": "success",
                "message": "Successfully parsed arrangement",
                "parsed_data": {
                    "arrangement_titel": arrangement.arrangement_titel,
                    "arrangør": arrangement.arrangør,
                    "nc_teaser": arrangement.nc_teaser
                }
            }
        except Exception as validation_error:
            logger.error(f"Validation error: {validation_error}")
            return {
                "status": "validation_error", 
                "error": str(validation_error),
                "raw_data": request
            }
            
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {"status": "error", "error": str(e)}

@router.post("/events/tag", response_model=EventTagResponse)
async def tag_single_event(request: EventTagRequest):
    try:
        logger.info(f"Received tagging request for arrangement: {request.arrangement_titel[:50]}...")
        logger.info(f"Request data: arrangement_titel={request.arrangement_titel}, arrangør={request.arrangør}")
        
        # Process the arrangement through the workflow
        result = await process_single_event(request)
        
        logger.info(f"Successfully tagged arrangement {result.event_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error tagging arrangement: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/tag/batch", response_model=BatchTagResponse)
async def tag_batch_events(
    request: BatchTagRequest,
    background_tasks: BackgroundTasks
):
    """
    Tag multiple events in batch
    
    TODO Implement batch processing
    """
    try:
        logger.info(f"Received batch tagging request for {len(request.events)} events")
        
        result = await process_batch_events(request)
        
        logger.info(f"Successfully processed batch {result.batch_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/tags")
async def get_available_tags():
    """
    Get all available tags and their descriptions
    """
    try:
        from ...services.initialization import available_tags
        
        return {
            "tags": available_tags,
            "count": len(available_tags)
        }
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/stats")
async def get_processing_stats():
    """
    Get processing statistics
    """
    try:
        # Implement stats collection
        # 1. Total events processed
        # 2. Success/error rates
        # 3. Average processing time
        # 4. Cost metrics
        
        return {
            "total_events_processed": 0,
            "success_rate": 0.0,
            "average_processing_time_ms": 0.0,
            "total_cost_usd": 0.0,
            "message": "Stats collection not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))