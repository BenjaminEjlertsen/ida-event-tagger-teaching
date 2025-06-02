import logging
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
import json

from ...models.requests import EventTagRequest, BatchTagRequest, EvaluationRequest
from ...models.responses import EventTagResponse, BatchTagResponse, EvaluationResponse
from ...services.event_processor import (
    process_single_event, 
    process_batch_events,
    stream_event_processing
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
    """
    Tag a single Danish arrangement
    
    TODO Task 2: Implement basic endpoint
    TODO Task 4: Add proper error handling
    TODO Task 6: Add rate limiting and monitoring
    """
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
    
    TODO Task 5: Implement batch processing
    TODO Task 6: Add background task handling
    """
    try:
        logger.info(f"Received batch tagging request for {len(request.events)} events")
        
        # For large batches, process in background
        if len(request.events) > settings.background_processing_threshold:
            # TODO: Implement background processing
            # background_tasks.add_task(process_batch_in_background, request)
            pass
        
        result = await process_batch_events(request)
        
        logger.info(f"Successfully processed batch {result.batch_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/tag/stream")
async def tag_event_stream(request: EventTagRequest):
    """
    Tag an event with streaming response
    
    TODO Task 7: Implement streaming responses
    """
    try:
        async def generate_stream():
            async for chunk in stream_event_processing(request):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/tags")
async def get_available_tags():
    """
    Get all available tags and their descriptions
    
    TODO Task 1: Implement simple data endpoint
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

@router.post("/events/evaluate", response_model=EvaluationResponse)
async def evaluate_performance(request: EvaluationRequest):
    """
    Evaluate tagging performance against test data
    
    TODO Task 7: Implement evaluation endpoint
    """
    try:
        # TODO: Implement evaluation logic
        # 1. Process test events
        # 2. Compare with expected results
        # 3. Calculate metrics
        # 4. Return performance report
        
        raise HTTPException(status_code=501, detail="Evaluation endpoint not yet implemented")
        
    except Exception as e:
        logger.error(f"Error in evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/stats")
async def get_processing_stats():
    """
    Get processing statistics
    
    TODO Task 6: Implement monitoring endpoint
    """
    try:
        # TODO: Implement stats collection
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