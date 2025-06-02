import logging
import time
import uuid
from typing import List, Tuple, Optional, Dict, Any

from ..models.requests import EventTagRequest, BatchTagRequest
from ..models.responses import EventTagResponse, BatchTagResponse, ProcessingStatus, TagResult
from ..config import settings

# Import all the service components
from .initialization import (
    input_validator,
    prompt_generator, 
    llm_client,
    output_parser,
    confidence_evaluator,
    human_review_checker
)
from .helpers import (
    calculate_processing_time,
    estimate_cost,
    format_event_for_processing,
    stream_response
)

logger = logging.getLogger(__name__)

async def process_single_event(request: EventTagRequest) -> EventTagResponse:
    """
    Main workflow for processing a single Danish arrangement
    This mirrors your generate_answer function structure
    """
    start_time = time.time()
    event_id = request.arrangement_nummer or str(uuid.uuid4())
    
    logger.info(f"Processing arrangement {event_id}: {request.arrangement_titel[:50]}...")
    
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
        # Step 1: Input validation and cleaning (similar to substitute_abbreviation)
        validated_arrangement = await input_validator.validate_and_clean(request)
        logger.info(f"Arrangement validation completed for {event_id}")
        
        # Step 2: Check for sensitive content (similar to input_classification_generator)
        sensitivity_check = await input_validator.check_sensitive_content(validated_arrangement)
        
        if sensitivity_check.contains_sensitive_content:
            logger.warning(f"Sensitive content detected in arrangement {event_id}: {sensitivity_check.reason}")
            return EventTagResponse(
                event_id=event_id,
                status=ProcessingStatus.ERROR,
                error_message="Arrangement indeholder følsomt indhold og kan ikke behandles",
                needs_human_review=True
            )
        
        # Step 3: Generate prompts for tagging (similar to query_generator)
        prompt_response = await prompt_generator.generate_tagging_prompt(
            validated_arrangement, 
            custom_prompt=request.custom_prompt
        )
        logger.info(f"Generated Danish prompt for arrangement {event_id}")
        
        # Step 4: Call LLM for tagging (similar to embedding_retriever but for LLM)
        llm_response = await llm_client.get_tags(
            prompt_response.prompt,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        logger.info(f"LLM response received for arrangement {event_id}")
        logger.info(f"LLM response content: {llm_response.content[:500]}...")  # Log first 500 chars
        
        # Step 5: Parse and validate LLM output (similar to document_grader)
        parsed_tags = await output_parser.parse_tag_response(
            llm_response.content,
            available_tags=prompt_response.available_tags
        )
        
        if not parsed_tags.is_valid:
            logger.warning(f"Invalid LLM response for arrangement {event_id}: {parsed_tags.error}")
            logger.warning(f"Full LLM response was: {llm_response.content}")
            return EventTagResponse(
                event_id=event_id,
                status=ProcessingStatus.ERROR,
                error_message=f"Ugyldig AI-respons: {parsed_tags.error}",
                needs_human_review=True
            )
        
        # Step 6: Confidence evaluation and quality checks
        confidence_scores = await confidence_evaluator.evaluate_confidence(
            validated_arrangement,
            parsed_tags,
            llm_response
        )
        
        # Step 7: Determine if human review is needed
        review_check = await human_review_checker.needs_review(
            confidence_scores,
            parsed_tags,
            validated_arrangement
        )
        
        # Step 8: Build final response (similar to answer_generator)
        processing_time = calculate_processing_time(start_time)
        estimated_cost = estimate_cost(llm_response.tokens_used)
        
        # Create tag results
        primary_tag = None
        if parsed_tags.primary_tag:
            primary_tag = TagResult.from_confidence(
                parsed_tags.primary_tag,
                confidence_scores.primary_confidence
            )
        
        secondary_tags = [
            TagResult.from_confidence(tag, confidence_scores.secondary_confidences.get(tag, 0.0))
            for tag in parsed_tags.secondary_tags
        ]
        
        response = EventTagResponse(
            event_id=event_id,
            status=ProcessingStatus.SUCCESS,
            primary_tag=primary_tag,
            secondary_tags=secondary_tags,
            reasoning=parsed_tags.reasoning if request.include_reasoning else None,
            processing_time_ms=processing_time,
            tokens_used=llm_response.tokens_used,
            cost_usd=estimated_cost,
            needs_human_review=review_check.needs_review
        )
        
        logger.info(f"Successfully processed event {event_id} in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        processing_time = calculate_processing_time(start_time)
        logger.error(f"Error processing event {event_id}: {str(e)}")
        
        return EventTagResponse(
            event_id=event_id,
            status=ProcessingStatus.ERROR,
            error_message=str(e),
            processing_time_ms=processing_time,
            needs_human_review=True
        )

async def process_batch_events(request: BatchTagRequest) -> BatchTagResponse:
    """
    Process multiple events in batch
    """
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    
    logger.info(f"Processing batch {batch_id} with {len(request.events)} events")
    
    results = []
    total_tokens = 0
    total_cost = 0.0
    events_needing_review = 0
    review_reasons = set()
    
    # Process events (could be parallel in advanced version)
    for i, event_request in enumerate(request.events):
        logger.info(f"Processing event {i+1}/{len(request.events)} in batch {batch_id}")
        
        try:
            result = await process_single_event(event_request)
            results.append(result)
            
            # Accumulate metrics
            if result.tokens_used:
                total_tokens += result.tokens_used
            if result.cost_usd:
                total_cost += result.cost_usd
            if result.needs_human_review:
                events_needing_review += 1
                if result.error_message:
                    review_reasons.add(result.error_message)
                
        except Exception as e:
            logger.error(f"Failed to process event {i+1} in batch {batch_id}: {e}")
            results.append(EventTagResponse(
                event_id=event_request.event_id or f"batch_{batch_id}_event_{i}",
                status=ProcessingStatus.ERROR,
                error_message=str(e),
                needs_human_review=True
            ))
            events_needing_review += 1
            review_reasons.add(str(e))
    
    # Calculate summary statistics
    successful_events = len([r for r in results if r.status == ProcessingStatus.SUCCESS])
    failed_events = len(results) - successful_events
    
    # Calculate average confidence
    all_confidences = []
    for result in results:
        if result.primary_tag:
            all_confidences.append(result.primary_tag.confidence)
        for tag in result.secondary_tags:
            all_confidences.append(tag.confidence)
    
    average_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else None
    
    total_processing_time = calculate_processing_time(start_time)
    
    # Determine overall status
    if failed_events == 0:
        overall_status = ProcessingStatus.SUCCESS
    elif successful_events == 0:
        overall_status = ProcessingStatus.ERROR
    else:
        overall_status = ProcessingStatus.PARTIAL
    
    response = BatchTagResponse(
        batch_id=batch_id,
        status=overall_status,
        results=results,
        total_events=len(request.events),
        successful_events=successful_events,
        failed_events=failed_events,
        total_processing_time_ms=total_processing_time,
        average_confidence=average_confidence,
        total_cost_usd=total_cost,
        total_tokens_used=total_tokens,
        events_needing_review=events_needing_review,
        review_reasons=list(review_reasons)
    )
    
    logger.info(f"Completed batch {batch_id}: {successful_events}/{len(request.events)} successful")
    return response

async def stream_event_processing(request: EventTagRequest):
    """
    Stream processing results for real-time feedback
    Similar to your stream_answer function
    """
    event_id = request.event_id or str(uuid.uuid4())
    
    # Yield initial status
    yield {
        "event_id": event_id,
        "status": "started",
        "message": "Starting event processing..."
    }
    
    try:
        # Stream each step of processing
        yield {
            "event_id": event_id,
            "status": "validating",
            "message": "Validating event data..."
        }
        
        validated_event = await input_validator.validate_and_clean(request)
        
        yield {
            "event_id": event_id,
            "status": "generating_prompt",
            "message": "Generating AI prompt..."
        }
        
        prompt_response = await prompt_generator.generate_tagging_prompt(validated_event)
        
        yield {
            "event_id": event_id,
            "status": "calling_ai",
            "message": "Calling OpenAI API..."
        }
        
        llm_response = await llm_client.get_tags(prompt_response.prompt)
        
        yield {
            "event_id": event_id,
            "status": "parsing_response",
            "message": "Parsing AI response..."
        }
        
        parsed_tags = await output_parser.parse_tag_response(llm_response.content)
        
        # Final result
        final_result = await process_single_event(request)
        
        yield {
            "event_id": event_id,
            "status": "completed",
            "result": final_result.dict()
        }
        
    except Exception as e:
        yield {
            "event_id": event_id,
            "status": "error",
            "error": str(e)
        }