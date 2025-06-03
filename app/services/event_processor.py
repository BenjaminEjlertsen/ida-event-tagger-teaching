import logging
import time
import uuid
from typing import List, Dict, Any

from ..models.requests import EventTagRequest, BatchTagRequest
from ..models.responses import EventTagResponse, BatchTagResponse, ProcessingStatus, TagTriple, BatchTagSummary
from ..config import settings
from .helpers import calculate_processing_time, estimate_cost

logger = logging.getLogger(__name__)

async def process_single_event(request: EventTagRequest) -> EventTagResponse:

    start_time = time.time()
    event_id = request.arrangement_nummer or str(uuid.uuid4())
    
    logger.info(f"Processing event {event_id}: {request.arrangement_titel[:50]}...")
    
    # Failsafe: ensure services are initialized
    from .initialization import (
        input_validator, prompt_generator, llm_client, output_parser, 
        confidence_evaluator, human_review_checker, initialize_services
    )
    
    if input_validator is None:
        logger.warning("Services not initialized, forcing initialization...")
        await initialize_services()
        # Re-import after initialization
        from .initialization import (
            input_validator, prompt_generator, llm_client, output_parser, 
            confidence_evaluator, human_review_checker
        )
    
    try:
        # Step 1: Input validation and sanitization
        validated_request = await input_validator.validate_and_clean(request)
        logger.info(f"Arrangement validation completed for {event_id}")
        
        # Step 1.5: Check for sensitive content
        sensitivity_check = await input_validator.check_sensitive_content(validated_request)
        if sensitivity_check.contains_sensitive_content:
            logger.warning(f"Sensitive content detected in arrangement {event_id}: {sensitivity_check.reason}")
            return EventTagResponse(
                event_id=event_id,
                status=ProcessingStatus.ERROR,
                error_message="Arrangement indeholder følsomt indhold og kan ikke behandles",
                needs_human_review=True
            )
        
        # Step 2: Generate tagging prompt
        prompt_response = await prompt_generator.generate_tagging_prompt(
            validated_request
        )
        logger.info(f"Generated prompt for event {event_id}")
        
        # Step 3: Validate available tags
        if not prompt_response.available_tags:
            logger.error(f"No available tags for event {event_id}")
            return EventTagResponse(
                event_id=event_id,
                status=ProcessingStatus.ERROR,
                error_message="Ingen tilgængelige tags fundet",
                needs_human_review=True
            )
        
        # Step 4: Call LLM for tagging
        llm_response = await llm_client.get_tags(
            prompt_response.prompt,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        logger.info(f"LLM response received for event {event_id}")
        logger.info(f"LLM response content: {llm_response.content[:500]}...")  # Log first 500 chars
        
        # Step 5: Parse and validate LLM output
        parsed_tags = await output_parser.parse_tag_response(
            llm_response.content,
            available_tags=prompt_response.available_tags
        )
        
        if not parsed_tags.is_valid:
            logger.warning(f"Invalid LLM response for event {event_id}: {parsed_tags.error}")
            logger.warning(f"Full LLM response was: {llm_response.content}")
            return EventTagResponse(
                event_id=event_id,
                status=ProcessingStatus.ERROR,
                error_message=f"Ugyldig AI-respons: {parsed_tags.error}",
                needs_human_review=True
            )
        
        # Step 6: Build successful response
        tag_triple = TagTriple(
            tag1=parsed_tags.tag1,
            tag2=parsed_tags.tag2,
            tag3=parsed_tags.tag3,
            confidence=parsed_tags.confidence,
            reasoning=parsed_tags.reasoning
        )
        
        # Step 8: Calc cost and time.
        processing_time_ms = calculate_processing_time(start_time)
        estimated_cost = estimate_cost(llm_response.tokens_used)
        
        response = EventTagResponse(
            event_id=event_id,
            status=ProcessingStatus.SUCCESS,
            tag_triple=tag_triple,
            reasoning=tag_triple.reasoning,
            processing_time_ms=processing_time_ms,
            tokens_used=llm_response.tokens_used,
            cost_dkk=estimated_cost
        )
        
        logger.info(f"Successfully processed event {event_id} in {processing_time_ms:.2f}ms")
        return response
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(f"Error processing event {event_id}: {e}")
        logger.exception("Full processing error:")
        return EventTagResponse(
            event_id=event_id,
            status=ProcessingStatus.ERROR,
            error_message=f"Intern fejl: {str(e)}",
            processing_time_ms=processing_time_ms,
            needs_human_review=True
        )

async def process_batch_events(request: BatchTagRequest) -> BatchTagResponse:
    """
    Process multiple arrangements in batch
    TODO Implement batch processing
    """
    logger.info(f"Processing batch of {len(request.events)} arrangements...")
    start_time = time.time()
    
    results = []
    batch_id = str(uuid.uuid4())
    
    """
    
    Process all event

    """
    
    # Calculate summary statistics
    successful = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == ProcessingStatus.ERROR)
    needs_review = sum(1 for r in results if r.needs_human_review)
    
    avg_confidence = 0.0
    if successful > 0:
        confidences = [r.primary_tag.confidence for r in results 
                      if r.primary_tag and r.status == ProcessingStatus.SUCCESS]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    total_time = (time.time() - start_time) * 1000
    
    summary = BatchTagSummary(
        total_events=len(request.events),
        successful=successful,
        failed=failed,
        needs_human_review=needs_review,
        total_processing_time_ms=total_time,
        average_confidence=avg_confidence
    )
    
    logger.info(f"Batch processing completed: {successful}/{len(request.events)} successful")
    
    return BatchTagResponse(
        batch_id=batch_id,
        status=ProcessingStatus.SUCCESS if failed == 0 else ProcessingStatus.ERROR,
        results=results,
        summary=summary
    )