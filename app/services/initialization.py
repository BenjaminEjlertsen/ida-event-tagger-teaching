import logging
import csv
from pathlib import Path
from typing import Dict, List

from ..config import settings
from .input_validator import InputValidator
from .prompt_generator import PromptGenerator
from .llm_client import LLMClient
from .output_parser import OutputParser
from .confidence_evaluator import ConfidenceEvaluator
from .human_review_checker import HumanReviewChecker

logger = logging.getLogger(__name__)

# Global service instances
input_validator: InputValidator = None
prompt_generator: PromptGenerator = None
llm_client: LLMClient = None
output_parser: OutputParser = None
confidence_evaluator: ConfidenceEvaluator = None
human_review_checker: HumanReviewChecker = None

# Global data
available_tags: Dict[str, dict] = {}
tag_rules: List[dict] = []
evaluation_data: List = [] 

async def initialize_services():
    """
    Initialize all service components
    Implement this step by step
    """
    global input_validator, prompt_generator, llm_client, output_parser, confidence_evaluator, human_review_checker, available_tags, tag_rules
    
    logger.info("Initializing Event Tagging Services...")
    
    try:
        # Load tag rules and data first
        await load_tag_data()
        logger.info(f"Loaded {len(available_tags)} tags")

        logger.info("Loading evaluation data...")
        await load_evaluation_data()
        
        # Initialize each service component with error handling
        logger.info("Initializing InputValidator...")
        input_validator = InputValidator()
        
        logger.info("Initializing PromptGenerator...")
        prompt_generator = PromptGenerator(
            available_tags=available_tags,
            tag_rules=tag_rules
        )
        
        logger.info("Initializing LLMClient...")
        llm_client = LLMClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        
        logger.info("Initializing OutputParser...")
        output_parser = OutputParser(
            available_tags=list(available_tags.keys())
        )
        
        logger.info("Initializing ConfidenceEvaluator...")
        confidence_evaluator = ConfidenceEvaluator(
            confidence_threshold=settings.confidence_threshold
        )
        
        logger.info("Initializing HumanReviewChecker...")
        human_review_checker = HumanReviewChecker(
            review_threshold=settings.human_review_threshold
        )
        
        # Verify all services are initialized
        services_status = {
            "input_validator": input_validator is not None,
            "prompt_generator": prompt_generator is not None, 
            "llm_client": llm_client is not None,
            "output_parser": output_parser is not None,
            "confidence_evaluator": confidence_evaluator is not None,
            "human_review_checker": human_review_checker is not None,
        }
        
        logger.info(f"Service initialization status: {services_status}")
        
        if not all(services_status.values()):
            failed_services = [name for name, status in services_status.items() if not status]
            raise Exception(f"Failed to initialize services: {failed_services}")
            
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # Don't raise - let the app start with minimal functionality
        logger.warning("App will start with limited functionality")
        
        # Initialize with dummy/basic services so the app doesn't crash
        if input_validator is None:
            input_validator = InputValidator()
        if prompt_generator is None:
            prompt_generator = PromptGenerator()
        if llm_client is None:
            llm_client = LLMClient(api_key="dummy", model="gpt-4o")
        if output_parser is None:
            output_parser = OutputParser()
        if confidence_evaluator is None:
            confidence_evaluator = ConfidenceEvaluator()
        if human_review_checker is None:
            human_review_checker = HumanReviewChecker()

async def load_tag_data():
    """
    Load tagging rules and available tags from CSV files
    """
    global available_tags, tag_rules
    
    try:
        # Load tag rules from tagsregler.csv
        rules_file = Path(settings.data_dir) / "tagsregler.csv"
        logger.info(f"Looking for tag rules file: {rules_file}")
        
        if rules_file.exists():
            logger.info(f"Found tag rules file, reading with UTF-8 encoding...")
            with open(rules_file, 'r', encoding='utf-8') as f:
                # Read first line to check column names
                first_line = f.readline().strip()
                logger.info(f"CSV header: {first_line}")
                
                # Reset file pointer
                f.seek(0)
                
                # Try different delimiters
                if ';' in first_line:
                    delimiter = ';'
                elif ',' in first_line:
                    delimiter = ','
                else:
                    delimiter = ';'  # default
                
                logger.info(f"Using delimiter: '{delimiter}'")
                
                reader = csv.DictReader(f, delimiter=delimiter)
                tag_rules = list(reader)
                
                logger.info(f"Read {len(tag_rules)} rows")
                if tag_rules:
                    logger.info(f"Sample row keys: {list(tag_rules[0].keys())}")
                    logger.info(f"Sample row: {tag_rules[0]}")
                
                # Create lookup dictionary with structure
                available_tags = {}
                for i, rule in enumerate(tag_rules):
                    try:
                        # Check different possible column name variations
                        hovedkategori = rule.get('Hovedkategori') or rule.get('hovedkategori') or rule.get('main_category') or ''
                        underkategori = rule.get('Underkategori') or rule.get('underkategori') or rule.get('sub_category') or ''
                        beskrivelse = rule.get('Beskrivelse') or rule.get('beskrivelse') or rule.get('description') or ''
                        eksempler = rule.get('Relevante tilbudseksempler') or rule.get('eksempler') or rule.get('examples') or ''
                        
                        if not hovedkategori:
                            logger.warning(f"Row {i}: No hovedkategori found, available keys: {list(rule.keys())}")
                            continue
                        
                        # Create combined tag name
                        #tag_name = f"{hovedkategori}_{underkategori}" if underkategori else hovedkategori
                        tag_name = underkategori if underkategori else hovedkategori
                        tag_name = tag_name.replace(' ', '_').replace('/', '_').replace('-', '_').upper()
                        
                        available_tags[tag_name] = {
                            'hovedkategori': hovedkategori,
                            'underkategori': underkategori,
                            'description': beskrivelse,
                            'examples': eksempler.split(',') if eksempler else [],
                            'display_name': f"{hovedkategori} - {underkategori}" if underkategori else hovedkategori
                        }
                        logger.debug(f"Created tag: {tag_name}")
                        
                    except Exception as e:
                        logger.error(f"Error processing row {i}: {e}, row data: {rule}")
            
            logger.info(f"Successfully loaded {len(available_tags)} tags from {rules_file}")
            
        logger.info(f"Final available tags: {list(available_tags.keys())}")
            
    except Exception as e:
        logger.error(f"Error loading tag data: {e}")
        logger.exception("Full traceback:")
        # Create minimal fallback
        available_tags = {
            "GENERAL": {
                "hovedkategori": "Generelt", 
                "underkategori": "",
                "description": "Generel kategori", 
                "examples": [], 
                "display_name": "Generelt"
            }
        }
        tag_rules = []

async def load_evaluation_data():
    """
    Load evaluation data with ground truth tags from arrangement.csv
    """
    global evaluation_data
    
    try:
        # Load evaluation data from arrangement.csv
        eval_file = Path(settings.data_dir) / "arrangementer_til_tagging.csv"
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
        else:
            logger.warning(f"Evaluation file not found: {eval_file}")
            
    except Exception as e:
        logger.error(f"Error loading evaluation data: {e}")
        logger.exception("Full traceback:")
        evaluation_data = []