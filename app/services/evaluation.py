# eval_dataset.py

import asyncio
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Optional
import logging
from pathlib import Path
from ..config import settings
import csv

# Adjust these imports to match your project’s structure:
from app.services.initialization import evaluation_data, load_evaluation_data
from app.services.event_processor import process_single_event
from app.models.requests import EventTagRequest

from app.models.responses import (
    EvaluationMetrics,
    EvaluationResult,
    EvaluationResponse
)

logger = logging.getLogger(__name__)

async def evaluate_all() -> EvaluationResponse:
    """
    Load the ground truth CSV, iterate over evaluation_data, call process_single_event 
    for each arrangement, build per‐arrangement EvaluationResult, compute overall metrics, 
    and return one EvaluationResponse.
    """
    # 1) Ensure evaluation_data is loaded
    if not evaluation_data:
        load_evaluation_data()
    if not evaluation_data:
        # If loading still yields no data, we raise an error
        raise RuntimeError("No evaluation data available after load_evaluation_data()")

    # 2) Create a unique ID for this evaluation run
    evaluation_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "_" + str(uuid.uuid4())[:8]

    results: List[EvaluationResult] = []
    total_confidence = 0.0
    confusion_counter: Dict[str, int] = defaultdict(int)

    # For precision/recall across tags:
    tp_counts: Dict[str, int] = defaultdict(int)
    fp_counts: Dict[str, int] = defaultdict(int)
    fn_counts: Dict[str, int] = defaultdict(int)

    # Per‐tag total and correct, for best/worst categories
    per_tag_total: Dict[str, int] = defaultdict(int)
    per_tag_correct: Dict[str, int] = defaultdict(int)

    correct_predictions_overall = 0
    start_time = time.time()

    # 3) Loop over each item in evaluation_data
    for item in evaluation_data:
        arr = item["arrangement"]
        gt_list = item["ground_truth_tags"]
        # Sort by priority 1→2→3
        sorted_gt = sorted(gt_list, key=lambda d: d["priority"])
        ground_truth_tags = [d["tag"] for d in sorted_gt]

        # Pad up to 3 slots with None
        while len(ground_truth_tags) < 3:
            ground_truth_tags.append(None)

        # Build the request
        req = EventTagRequest(
            arrangement_nummer=arr.get("arrangement_nummer"),
            arrangement_titel=arr.get("arrangement_titel", ""),
            arrangør=arr.get("arrangør", ""),
            nc_teaser=arr.get("nc_teaser", ""),
            nc_beskrivelse=arr.get("nc_beskrivelse", ""),
            beskrivelse_html_fri=arr.get("beskrivelse_html_fri", "")
        )

        predicted_tag1: Optional[str] = None
        predicted_tag2: Optional[str] = None
        predicted_tag3: Optional[str] = None
        predicted_confidence = 0.0
        match_priority: Optional[int] = None
        error_msg: Optional[str] = None

        try:
            # Call the LLM‐based processor
            response = await process_single_event(req)
            tri = response.tag_triple
            predicted_tag1 = tri.tag1 or None
            predicted_tag2 = tri.tag2 or None
            predicted_tag3 = tri.tag3 or None
            predicted_confidence = tri.confidence or 0.0

            # Determine if predicted_tag matches any ground_truth at positions 1, 2, or 3:
            matched = False
            for idx, true_tag in enumerate(ground_truth_tags, start=1):
                if true_tag is None:
                    continue
                if predicted_tag1 == true_tag:
                    match_priority = idx
                    matched = True
                    break

            is_correct = matched
            if is_correct:
                correct_predictions_overall += 1

            # For confusion matrix: if wrong (pred != any of the GT), record “true→pred”
            if predicted_tag1 and not is_correct:
                # Use the highest‐priority ground truth that exists
                true_nonnull = next((t for t in ground_truth_tags if t), None)
                if true_nonnull:
                    key = f"{true_nonnull} → {predicted_tag1}"
                    confusion_counter[key] += 1

            # Build per‐tag counts for precision/recall:
            all_tags_in_dataset = set()
            for t in ground_truth_tags:
                if t:
                    per_tag_total[t] += 1
                    all_tags_in_dataset.add(t)
            if predicted_tag1:
                all_tags_in_dataset.add(predicted_tag1)

            for t in all_tags_in_dataset:
                in_true = t in ground_truth_tags
                is_pred = (t == predicted_tag1)
                if is_pred and in_true:
                    tp_counts[t] += 1
                elif is_pred and not in_true:
                    fp_counts[t] += 1
                elif (not is_pred) and in_true:
                    fn_counts[t] += 1

            # Mark per‐tag correct if predicted_tag equals that tag
            if is_correct and predicted_tag1:
                per_tag_correct[predicted_tag1] += 1

        except Exception as e:
            is_correct = False
            error_msg = str(e)
            # Still count each ground truth tag into per_tag_total
            for t in ground_truth_tags:
                if t:
                    per_tag_total[t] += 1

        # Accumulate confidence for “average_confidence”
        total_confidence += predicted_confidence

        # Build this arrangement’s result
        results.append(
            EvaluationResult(
                arrangement_id=arr.get("arrangement_nummer", ""),
                arrangement_title=arr.get("arrangement_titel", ""),
                predicted_tag1=predicted_tag1,
                predicted_tag2=predicted_tag2,
                predicted_tag3=predicted_tag3,
                predicted_confidence=predicted_confidence,
                ground_truth_tags=[t for t in ground_truth_tags if t],
                is_correct=is_correct,
                match_priority=match_priority,
                error_message=error_msg
            )
        )

    # 4) Compute overall metrics
    N = len(results)

    # a) accuracy_at_1: fraction where match_priority == 1
    correct_at_1 = sum(1 for r in results if r.match_priority == 1)
    accuracy_at_1 = correct_at_1 / N if N > 0 else 0.0

    # b) accuracy_at_2: fraction where match_priority in {1,2}
    correct_at_2 = sum(1 for r in results if r.match_priority in (1, 2))
    accuracy_at_2 = correct_at_2 / N if N > 0 else 0.0

    # c) accuracy_at_3: fraction where match_priority in {1,2,3}
    correct_at_3 = sum(1 for r in results if r.match_priority in (1, 2, 3))
    accuracy_at_3 = correct_at_3 / N if N > 0 else 0.0

    exact2_count = 0
    exact3_count = 0

    for r in results:
        # Reconstruct padded ground truth slots:
        gt_list = r.ground_truth_tags  # this is a List[str] of length 1..3
        gt1 = gt_list[0]
        gt2 = gt_list[1] if len(gt_list) > 1 else None
        gt3 = gt_list[2] if len(gt_list) > 2 else None

        p1 = r.predicted_tag1
        p2 = r.predicted_tag2
        p3 = r.predicted_tag3

        # EXACT@2: 
        #   Must match gt1, and either:
        #     • gt2 is None and p2 is also None, or
        #     • gt2 is not None and p2 == gt2
        if p1 == gt1 and ( (gt2 is None and p2 is None) or (gt2 is not None and p2 == gt2) ):
            exact2_count += 1

        # EXACT@3:
        #   Must match gt1 and gt2 (where gt2 or p2 may be None), and
        #   either:
        #     • gt3 is None and p3 is also None, or
        #     • gt3 is not None and p3 == gt3
        if (
            p1 == gt1
            and ((gt2 is None and p2 is None) or (gt2 is not None and p2 == gt2))
            and ((gt3 is None and p3 is None) or (gt3 is not None and p3 == gt3))
        ):
            exact3_count += 1

    # Now divide by total arrangements to get a fraction:
    total = len(results)
    exact_match_at_2 = exact2_count / total if total > 0 else 0.0
    exact_match_at_3 = exact3_count / total if total > 0 else 0.0

    # d) weighted_accuracy: average of (1/priority) for each correct; else 0
    total_weight = 0.0
    for r in results:
        if r.match_priority:
            total_weight += 1.0 / r.match_priority
    weighted_accuracy = (total_weight / N) if N > 0 else 0.0

    # e) average_confidence
    average_confidence = (total_confidence / N) if N > 0 else 0.0

    # f) precision / recall / f1_score (micro‐avg over tags)
    sum_tp = sum(tp_counts.values())
    sum_fp = sum(fp_counts.values())
    sum_fn = sum(fn_counts.values())

    precision = sum_tp / (sum_tp + sum_fp) if (sum_tp + sum_fp) > 0 else 0.0
    recall = sum_tp / (sum_tp + sum_fn) if (sum_tp + sum_fn) > 0 else 0.0
    f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # g) total_predictions and correct_predictions
    total_predictions = N
    correct_predictions = correct_predictions_overall

    # 5) Build “additional insights”
    most_confused = dict(sorted(confusion_counter.items(), key=lambda x: x[1], reverse=True))

    # per‐tag accuracy = per_tag_correct[tag] / per_tag_total[tag]
    tag_accuracy: Dict[str, float] = {}
    for tag, total_cnt in per_tag_total.items():
        correct_cnt = per_tag_correct.get(tag, 0)
        tag_accuracy[tag] = correct_cnt / total_cnt if total_cnt > 0 else 0.0

    sorted_by_acc = sorted(tag_accuracy.items(), key=lambda kv: kv[1], reverse=True)
    best_performing_categories = [tag for tag, _ in sorted_by_acc[:3]]

    sorted_by_acc_asc = sorted(tag_accuracy.items(), key=lambda kv: kv[1])
    worst_performing_categories = [tag for tag, _ in sorted_by_acc_asc[:3]]

    # 6) Build the metrics object
    metrics = EvaluationMetrics(
        accuracy_at_1=accuracy_at_1,
        accuracy_at_2=accuracy_at_2,
        accuracy_at_3=accuracy_at_3,
        weighted_accuracy=weighted_accuracy,
        exact_match_at_2=exact_match_at_2,
        exact_match_at_3=exact_match_at_3,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        average_confidence=average_confidence,
        total_predictions=total_predictions,
        correct_predictions=correct_predictions,

    )

    # 7) Return the populated EvaluationResponse
    return EvaluationResponse(
        evaluation_id=evaluation_id,
        metrics=metrics,
        results=results,
        processing_time_ms=0.0,       # endpoint will overwrite this
        timestamp=datetime.utcnow(),
        most_confused_tags=most_confused,
        best_performing_categories=best_performing_categories,
        worst_performing_categories=worst_performing_categories
    )

def load_evaluation_data():
    """
    Load evaluation data with ground truth tags from arrangement.csv
    """
    global evaluation_data
    
    try:
        # Load evaluation data from arrangement.csv
        eval_file = Path(settings.data_dir) / "arrangementer_til_tagging_test_set.csv"
        logger.info(f"Looking for evaluation file: {eval_file}")
        
        evaluation_data = []
        
        if eval_file.exists():
            logger.info(f"Found evaluation file, reading with UTF-8 encoding...")
            with open(eval_file, 'r', encoding='utf-8') as f:
                # 1) Read the first line to detect delimiter
                first_line = f.readline().rstrip("\n")
                logger.info(f"First line of CSV: {repr(first_line)}")
                delimiter = ';' if ';' in first_line else ','
                logger.info(f"Detected delimiter: {repr(delimiter)}")

                # 2) Rewind and create a single DictReader
                f.seek(0)
                reader = csv.DictReader(f, delimiter=delimiter)
                logger.info(f"Reader.fieldnames: {reader.fieldnames}")

                for i, row in enumerate(reader):
                    try:
                        # Extract arrangement data using the exact column names:
                        arrangement_data = {
                            'arrangement_nummer': row.get('ArrangementNummer', '').strip(),
                            'arrangement_titel': row.get('ArrangementTitel', '').strip(),
                            'arrangør': row.get('arrangør', '').strip(),
                            'nc_teaser': row.get('nc_Teaser', '').strip(),
                            'nc_beskrivelse': row.get('CleanText', '').strip(),
                            'arrangement_undertype': row.get('ArrangementUndertype', '').strip()
                        }

                        # Build ground_truth_tags from Underkategori1/2/3
                        ground_truth_tags = []
                        for j in range(1, 4):
                            tag_col = f"Underkategori{j}"
                            raw_val = row.get(tag_col, "") or ""
                            tag_value = raw_val.strip()
                            if tag_value:
                                tag_normalized = (
                                    tag_value.replace(' ', '_')
                                            .replace('/', '_')
                                            .replace('-', '_')
                                            .upper()
                                )
                                ground_truth_tags.append({
                                    'tag': tag_normalized,
                                    'priority': j,
                                    'original_value': tag_value
                                })

                        # Only keep rows that have a nonempty title AND at least one tag
                        if arrangement_data['arrangement_titel'] and ground_truth_tags:
                            evaluation_data.append({
                                'arrangement': arrangement_data,
                                'ground_truth_tags': ground_truth_tags
                            })

                    except Exception as e:
                        logger.warning(f"Error processing evaluation row {i}: {e}")
                        continue

                logger.info(f"Loaded {len(evaluation_data)} arrangements for evaluation")
                if evaluation_data:
                    sample = evaluation_data[0]
                    logger.info(f"Sample title: {sample['arrangement']['arrangement_titel']}")
                    logger.info(f"Sample tags: {sample['ground_truth_tags']}")

                    return evaluation_data
        else:
            logger.warning(f"Evaluation file not found: {eval_file}")
            
    except Exception as e:
        logger.error(f"Error loading evaluation data: {e}")
        logger.exception("Full traceback:")
        evaluation_data = []