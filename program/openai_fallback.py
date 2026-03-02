import base64
import json
import os
from openai import OpenAI
from logger_config import status_logger, error_logger
import bet_data_processor

# Initialize OpenAI client using environment variable or config file
def _get_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if config.get("general", {}).get("openai_api_key"):
            return config["general"]["openai_api_key"]
    except Exception:
        pass
    raise ValueError("OPENAI_API_KEY not found. Set it in .env or config/config.json")

client = OpenAI(api_key=_get_api_key())

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_betting_image_with_openai(image_path, category):
    """
    Analyze betting screenshot with OpenAI Vision API when YOLO crops are missing
    Returns the same JSON structure as bet_data_processor.py
    """
    try:
        # Encode the image
        base64_image = encode_image(image_path)
        
        # Create detailed prompt based on betting analysis requirements
        prompt = """
        Analyze this betting screenshot and extract the following information:
        
        1. Team names (Team A and Team B)
        2. Betting category (e.g. Asian Handicap, Over/Under)
        3. The SELECTION/LINE for the chosen bet (e.g. handicap "-1.0,-1.5", "Over 2.5", or "Team Name -1, -1.5")
        4. Whether this is a bet builder (multiple selections) or simple bet
        5. Detect if text is in Latin characters (English) or Greek
        
        CRITICAL - "bet" is the SELECTION only, NOT the odds:
        - The number next to the selection (e.g. 1.87, 2.10) is the ODDS. Do NOT put the odds in the "bet" field.
        - "bet" must be only the selection/line text. Never put a single decimal like 1.87 in "bet".
        
        CRITICAL - For HANDICAP (and any team-specific market): include the TEAM name in "bet" so it is clear which side the selection refers to.
        - Good: "FC Struga Trim & Lum -1.0,-1.5", "Team A -0.5", "KF Bashkimi +1.0,+1.5"
        - Bad: "-1.0,-1.5" alone (ambiguous which team). For Over/Under or neutral markets you can use just the line (e.g. "Over 2.5", "Under 3.5").
        
        Do NOT infer or return "category" from the image. Category is set by the application (e.g. user/config); use empty string "" for category in your JSON. We will overwrite it.
        
        For BET BUILDER (multiple selections), return JSON format:
        {
            "bet1": "first selection: for handicaps include team name (e.g. Team A -1.0,-1.5), no odds",
            "bet2": "second selection: for handicaps include team name, no odds",
            "bet_category1": "first bet category",
            "bet_category2": "second bet category",
            "teamA": "team A name",
            "teamB": "team B name",
            "bet_builder": 1,
            "has_latin": 1 or 0,
            "category": ""
        }
        
        For SIMPLE BET (single selection), return JSON format:
        {
            "bet": "selection/line: for handicaps include team (e.g. FC Struga Trim & Lum -1.0,-1.5); for Over/Under use e.g. Over 2.5; NEVER the odds number",
            "bet_category": "bet category",
            "teamA": "team A name",
            "teamB": "team B name",
            "bet_builder": 0,
            "has_latin": 1 or 0,
            "category": ""
        }
        
        Rules:
        - has_latin: 1 if text contains only Latin characters (English), 0 if Greek/other
        - bet / bet1 / bet2 = selection or line ONLY (no odds). For Asian Handicap, Handicap, or any market where the selection is per team: include the team name in the bet (e.g. "FC Struga Trim & Lum -1.0,-1.5"). For Over/Under you can use "Over 2.5" or "Under 3.5".
        - bet_category = category name only. No emojis, no odds.
        - If you can't clearly identify something, use empty string ""
        - Return only valid JSON, no additional text
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Parse the JSON response
        result_text = response.choices[0].message.content.strip()
        
        # Remove any markdown formatting if present
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        result_data = json.loads(result_text)
        
        # Category always from application (e.g. thread_manager, run_with_photo), never from AI
        result_data["category"] = category
        
        status_logger.info("OpenAI Vision API successfully analyzed betting image")
        status_logger.info(f"Extracted data: {result_data}")
        
        return result_data
        
    except json.JSONDecodeError as e:
        error_logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        error_logger.error(f"Raw response: {result_text}")
        return 'error'
    except Exception as e:
        error_logger.error(f"OpenAI Vision API error: {e}")
        return 'error'

def process_with_openai_fallback(image_path, category):
    """
    Main fallback function that processes image with OpenAI and applies the same 
    transformations as bet_data_processor.py
    """
    try:
        # Get raw data from OpenAI
        raw_data = analyze_betting_image_with_openai(image_path, category)
        
        if raw_data == 'error':
            return 'error'
            
        # Apply the same transformations as bet_data_processor.py
        processed_data = apply_bet_processing_logic(raw_data, category)
        
        # Export to the same JSON files as bet_data_processor.py
        export_processed_data(processed_data, category)
        
        return processed_data
        
    except Exception as e:
        error_logger.error(f"Error in OpenAI fallback processing: {e}")
        return 'error'

def apply_bet_processing_logic(raw_data, category):
    """Apply the same business logic as bet_data_processor.py - assumes Stoiximan processing"""
    
    # Check if it's bet builder or simple bet
    is_bet_builder = raw_data.get('bet_builder', 0) == 1
    has_latin = raw_data.get('has_latin', 0)
    
    if is_bet_builder:
        # BET BUILDER logic - exactly like bet_data_processor.py lines 203-244
        bet1 = raw_data.get('bet1', '')
        bet2 = raw_data.get('bet2', '')
        bet_category1 = raw_data.get('bet_category1', '')
        bet_category2 = raw_data.get('bet_category2', '')
        teamA = raw_data.get('teamA', '')
        teamB = raw_data.get('teamB', '')
        
        # 1. Export as-is to data.json (like Stoiximan branch in original)
        data = {
            "bet1": bet1,
            "bet2": bet2,
            "teamA": teamA,
            "teamB": teamB,
            "bet_category1": bet_category1,
            "bet_category2": bet_category2,
            "has_latin": has_latin,
            "bet_builder": 1,
            "category": category
        }
        
        # 2. Transform bet categories for novidata.json
        if has_latin == 1:
            new_bet_category1_stoiximan, new_bet_category2_stoiximan = (
                bet_data_processor.stoiximan_bet_builder_english(bet_category1, bet_category2)
            )
        else:
            new_bet_category1_stoiximan, new_bet_category2_stoiximan = (
                bet_data_processor.stoiximan_bet_builder_no_english(bet_category1, bet_category2)
            )
        
        data_stoiximan = {
            "bet1": bet1,
            "bet2": bet2,
            "teamA": teamA,
            "teamB": teamB,
            "bet_category1": new_bet_category1_stoiximan,
            "bet_category2": new_bet_category2_stoiximan,
            "has_latin": has_latin,
            "bet_builder": 1,
            "category": category
        }
        
        return {
            'main_data': data,
            'stoiximan_data': data_stoiximan,
            'bet_builder': True
        }
        
    else:
        # SIMPLE BET logic - exactly like bet_data_processor.py lines 378-410
        bet = raw_data.get('bet', '')
        bet_category = raw_data.get('bet_category', '')
        teamA = raw_data.get('teamA', '')
        teamB = raw_data.get('teamB', '')
        
        # 1. Export as-is to data.json
        data = {
            "bet": bet,
            "teamA": teamA,
            "teamB": teamB,
            "has_latin": has_latin,
            "bet_category": bet_category,
            "bet_builder": 0,
            "category": category
        }
        
        # 2. Transform bet category for novidata.json
        if has_latin == 1:
            transformed_bet_category = bet_data_processor.stoiximan_english(bet_category)
        else:
            transformed_bet_category = bet_data_processor.stoiximan_no_english(bet_category)
        
        data_stoiximan = {
            "bet": bet,
            "teamA": teamA,
            "teamB": teamB,
            "bet_category": transformed_bet_category,
            "has_latin": has_latin,
            "bet_builder": 0,
            "category": category
        }
        
        return {
            'main_data': data,
            'stoiximan_data': data_stoiximan,
            'bet_builder': False
        }

def export_processed_data(processed_data, category):
    """Export data to the same JSON files as bet_data_processor.py"""
    try:
        main_data = processed_data['main_data']
        stoiximan_data = processed_data['stoiximan_data']
        
        # Export main data to data.json (exactly like bet_data_processor.py)
        with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
            json.dump(main_data, f)
        
        if processed_data['bet_builder']:
            status_logger.info("ΕΞΑΓΑΜΕ BET BUILDER (Stoiximan) AS IS -> data.json")
        else:
            status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA (Stoiximan) -> data.json")
        
        # Export stoiximan data to novidata.json (exactly like bet_data_processor.py)
        with open('/Users/jimmyntak/Downloads/blade/novidata.json', 'w') as f:
            json.dump(stoiximan_data, f)
        
        if processed_data['bet_builder']:
            status_logger.info("ΕΞΑΓΑΜΕ BET BUILDER (Stoiximan) TRANSFORMED -> novidata.json")
        else:
            status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA (Stoiximan) -> novidata.json")
        
        # Export translated data (same as bet_data_processor.py)
        export_translated_data(processed_data)
        
    except Exception as e:
        error_logger.error(f"Error exporting OpenAI processed data: {e}")

def export_translated_data(processed_data):
    """Export translated data in English"""
    try:
        main_data = processed_data['main_data']
        is_bet_builder = processed_data['bet_builder']
        
        if is_bet_builder:
            # Translate bet builder data
            translated_bet_category1 = bet_data_processor.translate_text(main_data.get('bet_category1', ''))
            translated_bet1 = bet_data_processor.translate_text(main_data.get('bet1', ''))
            translated_bet_category2 = bet_data_processor.translate_text(main_data.get('bet_category2', ''))
            translated_bet2 = bet_data_processor.translate_text(main_data.get('bet2', ''))
            
            translated_data = {
                "First Selection": f"{translated_bet_category1} | {translated_bet1}",
                "Second Selection": f"{translated_bet_category2} | {translated_bet2}"
            }
        else:
            # Translate simple bet data
            translated_bet_category = bet_data_processor.translate_text(main_data.get('bet_category', ''))
            translated_bet = bet_data_processor.translate_text(main_data.get('bet', ''))
            
            translated_data = {
                "Selection": f"{translated_bet_category} - {translated_bet}"
            }
        
        # Export to translated data file
        translated_json_path = '/Users/jimmyntak/Downloads/forPerumal/translated_data.json'
        with open(translated_json_path, 'w') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=4)
        status_logger.info(f"OpenAI fallback exported translated data to {translated_json_path}")
        
    except Exception as e:
        error_logger.error(f"Error exporting translated data from OpenAI fallback: {e}")