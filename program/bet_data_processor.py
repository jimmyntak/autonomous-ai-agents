import text_recognition as text_recognition
import os
import re
import base64
from logger_config import status_logger, error_logger
import json
from google.cloud import translate_v3
from google.oauth2 import service_account

# Optional: OpenAI for OCR fallback (only used when primary OCR fails)
try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    OpenAI = None

# Path to your service account credentials JSON file
credentials_path = "/Users/jimmyntak/Downloads/blade/bets-414519-13edca7b7e58.json"

# Create credentials object
credentials = service_account.Credentials.from_service_account_file(credentials_path)

# Create the Translation client using the credentials
client = translate_v3.TranslationServiceClient(credentials=credentials)

# Helper function to check for Latin characters.
def has_latin_characters(sentence):
    pattern = r"^[a-zA-Z\s()\-/\d]*$"
    match = re.match(pattern, sentence)
    return match is not None

# Google Translate helper to determine the source language.
def get_source_language(text):
    # If the text contains only Latin characters, assume English; otherwise assume Greek.
    if has_latin_characters(text):
        return "en"
    else:
        return "el"


# -------------------------------------------------------------------------
# OpenAI OCR fallback (only when primary OCR fails)
# -------------------------------------------------------------------------

def _read_first_image_bytes(directory):
    """Read bytes of the first image in directory (.jpg, .jpeg, .png). Returns None if none found."""
    if not directory or not os.path.isdir(directory):
        return None
    image_files = [f for f in os.listdir(directory) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        return None
    image_path = os.path.join(directory, image_files[0])
    try:
        with open(image_path, 'rb') as f:
            return f.read()
    except Exception:
        return None


def _get_openai_api_key():
    """Read OpenAI API key from blade config if present; else use environment variable."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if config.get("general", {}).get("openai_api_key"):
            return config["general"]["openai_api_key"]
    except Exception:
        pass
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    raise ValueError("OPENAI_API_KEY not found. Set it in .env or config/config.json")


def openai_ocr_fallback(field_directories):
    """
    Fallback OCR using OpenAI GPT-4o vision. Reads one image per field directory,
    returns dict mapping field_name -> extracted text (raw). Used only when primary OCR fails.
    Returns dict on success; on failure returns None (caller should handle).
    """
    if not _openai_available or OpenAI is None:
        error_logger.warning("OpenAI not available; OCR fallback skipped.")
        return None
    client = OpenAI(api_key=_get_openai_api_key())
    result = {}
    for field_name, dir_path in field_directories.items():
        image_bytes = _read_first_image_bytes(dir_path)
        if not image_bytes:
            result[field_name] = ""
            continue
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = "Extract all text visible in this image exactly as written. Return only the extracted text, nothing else. If the image is empty or unreadable, respond with a single empty string."
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            text = (response.choices[0].message.content or "").strip()
            result[field_name] = text
        except Exception as e:
            error_logger.error(f"OpenAI OCR fallback error for field {field_name}: {e}")
            result[field_name] = ""
    status_logger.info("OpenAI OCR fallback completed; raw text per field used for parsing.")
    return result


def _is_ocr_failure(bet_builder, **fields):
    """True if required fields are missing or empty (after strip)."""
    def empty(v):
        return v is None or (isinstance(v, str) and not v.strip())
    if bet_builder == 1:
        return (
            empty(fields.get("teamA"))
            or empty(fields.get("teamB"))
            or empty(fields.get("bet1"))
            or empty(fields.get("bet_category1"))
        )
    else:
        return (
            empty(fields.get("teamA"))
            or empty(fields.get("teamB"))
            or empty(fields.get("bet"))
            or empty(fields.get("bet_category"))
        )


def _validate_bet_data_schema(data):
    """
    Ensure data matches exactly one of the two schemas (bet_builder 0 or 1).
    Returns a new dict with only the allowed keys and correct types; raises ValueError if invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("data must be a dict")
    bet_builder = data.get("bet_builder")
    if bet_builder not in (0, 1):
        raise ValueError("bet_builder must be 0 or 1")
    bet_builder = int(bet_builder)
    category = data.get("category", "")
    has_latin = 1 if data.get("has_latin") == 1 else 0
    if bet_builder == 1:
        allowed = {"bet1", "bet2", "teamA", "teamB", "bet_category1", "bet_category2", "has_latin", "bet_builder", "category"}
        for key in data:
            if key not in allowed:
                raise ValueError(f"Unexpected key for bet_builder=1: {key}")
        for key in allowed:
            if key not in data:
                raise ValueError(f"Missing required key for bet_builder=1: {key}")
        return {
            "bet1": str(data.get("bet1", "")),
            "bet2": str(data.get("bet2", "")),
            "teamA": str(data.get("teamA", "")),
            "teamB": str(data.get("teamB", "")),
            "bet_category1": str(data.get("bet_category1", "")),
            "bet_category2": str(data.get("bet_category2", "")),
            "has_latin": has_latin,
            "bet_builder": 1,
            "category": category,
        }
    else:
        allowed = {"bet", "teamA", "teamB", "bet_category", "has_latin", "bet_builder", "category"}
        for key in data:
            if key not in allowed:
                raise ValueError(f"Unexpected key for bet_builder=0: {key}")
        for key in allowed:
            if key not in data:
                raise ValueError(f"Missing required key for bet_builder=0: {key}")
        return {
            "bet": str(data.get("bet", "")),
            "teamA": str(data.get("teamA", "")),
            "teamB": str(data.get("teamB", "")),
            "bet_category": str(data.get("bet_category", "")),
            "has_latin": has_latin,
            "bet_builder": 0,
            "category": category,
        }


def translate_text(text, target_language="en", project_id="bets-414519"):
    if not text:
        return ""
    try:
        source_language = get_source_language(text)
        location = "us-central1"
        parent = f"projects/{project_id}/locations/{location}"
        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",
                "target_language_code": target_language,
                "source_language_code": source_language,
                # Removed the "model" field to use the default model.
            }
        )
        return response.translations[0].translated_text
    except Exception as e:
        print(f"Translation error for text '{text}': {e}")
        return text
    
def stoiximan_bet_builder_english(bet_category1, bet_category2):
    """Translate from Stoiximan (English) -> 'internal' English references."""
    new_bet_category1_stoiximan = text_recognition.translate_from_stoiximan_english(
        bet_category1, text_recognition.novibet_english_bets)
    new_bet_category2_stoiximan = text_recognition.translate_from_stoiximan_english(
        bet_category2, text_recognition.novibet_english_bets)
    status_logger.info(
        f'Μετάφραση (Stoiximan Αγγλικά) -> {new_bet_category1_stoiximan} | {new_bet_category2_stoiximan}')
    return new_bet_category1_stoiximan, new_bet_category2_stoiximan

def stoiximan_bet_builder_no_english(bet_category1, bet_category2):
    """Translate from Stoiximan (Greek) -> 'internal' Greek references."""
    new_bet_category1 = text_recognition.translate_from_stoiximan(
        bet_category1, text_recognition.stoiximan_bets)
    new_bet_category2 = text_recognition.translate_from_stoiximan(
        bet_category2, text_recognition.stoiximan_bets)
    status_logger.info(
        f'Μετάφραση (Stoiximan Ελληνικά) -> {new_bet_category1} | {new_bet_category2}')
    return new_bet_category1, new_bet_category2

def novibet_bet_builder_english(bet_category1, bet_category2):
    new_bet_category1 = text_recognition.translate_from_novibet_english(
        bet_category1, text_recognition.novibet_english_bets)
    new_bet_category2 = text_recognition.translate_from_novibet_english(
        bet_category2, text_recognition.novibet_english_bets)
    status_logger.info(
        f'Μετάφραση από novibet (Αγγλικά) --> {new_bet_category1} | {new_bet_category2}')
    return new_bet_category1, new_bet_category2

def fonbet_no_english(bet_category):
    new_bet_category = text_recognition.translate_from_fonbet(
        bet_category, text_recognition.fonbet_bets)
    status_logger.info(f'Μετάφραση από Fonbet (Ελληνική) --> {new_bet_category}')
    return new_bet_category

def stoiximan_bet_builder_no_english_deprecated(bet_category1, bet_category2):
    """(Not used if you prefer the new function above)"""
    new_bet_category1 = text_recognition.translate_from_stoiximan(
        bet_category1, text_recognition.stoiximan_bets)
    new_bet_category2 = text_recognition.translate_from_stoiximan(
        bet_category2, text_recognition.stoiximan_bets)
    status_logger.info(
        f'Μετάφραση από stoiximan (Ελληνική) --> {new_bet_category1} | {new_bet_category2}')
    return new_bet_category1, new_bet_category2

def novibet_bet_builder_no_english(bet_category1, bet_category2):
    new_bet_category1_stoiximan = text_recognition.translate_from_novibet(
        bet_category1, text_recognition.novibet_bets)
    new_bet_category2_stoiximan = text_recognition.translate_from_novibet(
        bet_category2, text_recognition.novibet_bets)
    status_logger.info(
        f'Μετάφραση από novibet (Ελληνική) --> {new_bet_category1_stoiximan} | {new_bet_category2_stoiximan}')
    return new_bet_category1_stoiximan, new_bet_category2_stoiximan

def bet365_bet_builder_no_english(bet_category1, bet_category2):
    new_bet_category1 = text_recognition.translate_from_bet365(
        bet_category1, text_recognition.bet365_bets)
    new_bet_category2 = text_recognition.translate_from_bet365(
        bet_category2, text_recognition.bet365_bets)
    status_logger.info(
        f'Μετάφραση από bet365 (Ελληνική) --> {new_bet_category1} | {new_bet_category2}')
    return new_bet_category1, new_bet_category2

def stoiximan_english(bet_category):
    new_bet_category = text_recognition.translate_from_stoiximan_english(
        bet_category, text_recognition.stoiximan_english_bets)
    status_logger.info(f'Μετάφραση από stoiximan (Αγγλική) --> {new_bet_category}')
    return new_bet_category

def novibet_english(bet_category):
    new_bet_category_stoiximan = text_recognition.translate_from_stoiximan_english(
        bet_category, text_recognition.novibet_english_bets)
    status_logger.info(f'Μετάφραση από novibet (Αγγλική) --> {new_bet_category_stoiximan}')
    return new_bet_category_stoiximan

def stoiximan_no_english(bet_category):
    new_bet_category = text_recognition.translate_from_stoiximan(
        bet_category, text_recognition.stoiximan_bets)
    status_logger.info(f'Μετάφραση από stoiximan (Ελληνική) --> {new_bet_category}')
    return new_bet_category

def novibet_no_english(bet_category):
    new_bet_category_stoiximan = text_recognition.translate_from_novibet(
        bet_category, text_recognition.novibet_bets)
    status_logger.info(f'Μετάφραση από novibet (Ελληνική) --> {new_bet_category_stoiximan}')
    return new_bet_category_stoiximan

def bet365_no_english(bet_category):
    new_bet_category = text_recognition.translate_from_bet365(
        bet_category, text_recognition.bet365_bets)
    status_logger.info(f'Μετάφραση από bet365 (Ελληνική) --> {new_bet_category}')
    return new_bet_category

def bet365_english(bet_category):
    status_logger.info(f'Μετάφραση από stoiximan (Αγγλικά) --> {bet_category}')
    return bet_category

def run(client, category):
    language_hints = ['en', 'el']
    directory = "/Users/jimmyntak/Downloads/blade/runs/detect/predict/crops"
    data_stoiximan = None
    new_bet_category1_stoiximan = None
    new_bet_category2_stoiximan = None
    new_bet_category_stoiximan = None

    try:
        # -------------------------------------------------------------------------
        # CASE 1: BET BUILDER
        # -------------------------------------------------------------------------
        if os.path.isdir(os.path.join(directory, "bet_builder")):
            bet1_directory = os.path.join(directory, "bet1")
            bet_category1_directory = os.path.join(directory, "bet_category1")
            bet2_directory = os.path.join(directory, "bet2")
            bet_category2_directory = os.path.join(directory, "bet_category2")
            teamA_directory = os.path.join(directory, "teamA")
            teamB_directory = os.path.join(directory, "teamB")

            ocr_failed = False
            try:
                bet1 = (text_recognition.export_text(
                    client=client, directory=bet1_directory, language_hints=language_hints) or "")
                bet_category1 = (text_recognition.export_text(
                    client=client, directory=bet_category1_directory, language_hints=language_hints) or "")
                bet2 = (text_recognition.export_text(
                    client=client, directory=bet2_directory, language_hints=language_hints) or "")
                bet_category2 = (text_recognition.export_text(
                    client=client, directory=bet_category2_directory, language_hints=language_hints) or "")
                teamA = (text_recognition.export_text(
                    client=client, directory=teamA_directory, language_hints=language_hints) or "")
                teamB = (text_recognition.export_text(
                    client=client, directory=teamB_directory, language_hints=language_hints) or "")
            except Exception as e:
                error_logger.warning(f"Primary OCR failed (bet_builder): {e}")
                ocr_failed = True
                bet1 = bet2 = bet_category1 = bet_category2 = teamA = teamB = ""

            # Optional: force OpenAI fallback for testing (set FORCE_OCR_FALLBACK=1)
            if os.environ.get("FORCE_OCR_FALLBACK") == "1":
                ocr_failed = True

            if ocr_failed or _is_ocr_failure(1, teamA=teamA, teamB=teamB, bet1=bet1, bet_category1=bet_category1, bet2=bet2, bet_category2=bet_category2):
                field_dirs = {
                    "bet1": bet1_directory,
                    "bet2": bet2_directory,
                    "bet_category1": bet_category1_directory,
                    "bet_category2": bet_category2_directory,
                    "teamA": teamA_directory,
                    "teamB": teamB_directory,
                }
                fallback_raw = openai_ocr_fallback(field_dirs)
                if fallback_raw is not None:
                    bet1 = fallback_raw.get("bet1", bet1) or ""
                    bet2 = fallback_raw.get("bet2", bet2) or ""
                    bet_category1 = fallback_raw.get("bet_category1", bet_category1) or ""
                    bet_category2 = fallback_raw.get("bet_category2", bet_category2) or ""
                    teamA = fallback_raw.get("teamA", teamA) or ""
                    teamB = fallback_raw.get("teamB", teamB) or ""
                    status_logger.info("Using OpenAI OCR fallback for bet_builder fields.")
                if _is_ocr_failure(1, teamA=teamA, teamB=teamB, bet1=bet1, bet_category1=bet_category1, bet2=bet2, bet_category2=bet_category2):
                    error_logger.error("OCR fallback still missing required bet_builder fields.")
                    return "error"

            status_logger.info(f"Ai Model read -> Team A: {teamA}")
            status_logger.info(f"Ai Model read -> Team B: {teamB}")
            status_logger.info(f"Ai Model read -> First Selection: {bet_category1} | {bet1}")
            status_logger.info(f"Ai Model read -> Second Selection: {bet_category2} | {bet2}")

            exported = False   # Initialize the exported flag
            bet_builder = 1    # We are in bet_builder directory
            has_latin = 0      # Default value

            # ---------------------------------------------------------------------
            # STOIXIMAN branch
            # ---------------------------------------------------------------------
            if os.path.isdir(os.path.join(directory, "stoiximan")):
                # 1. Export as-is to data.json
                if has_latin_characters(bet_category1) and has_latin_characters(bet_category2):
                    has_latin = 1
                else:
                    has_latin = 0

                data = {
                    "bet1": bet1,
                    "bet2": bet2,
                    "teamA": teamA,
                    "teamB": teamB,
                    "bet_category1": bet_category1,
                    "bet_category2": bet_category2,
                    "has_latin": has_latin,
                    "bet_builder": bet_builder,
                    "category": category
                }
                data = _validate_bet_data_schema(data)
                with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
                    json.dump(data, f)
                status_logger.info("ΕΞΑΓΑΜΕ BET BUILDER (Stoiximan) AS IS -> data.json")
                exported = True

                # 2. Transform bet categories and export to novidata.json
                if has_latin == 1:
                    new_bet_category1_stoiximan, new_bet_category2_stoiximan = (
                        stoiximan_bet_builder_english(bet_category1, bet_category2)
                    )
                else:
                    new_bet_category1_stoiximan, new_bet_category2_stoiximan = (
                        stoiximan_bet_builder_no_english(bet_category1, bet_category2)
                    )

                data_stoiximan = {
                    "bet1": bet1,
                    "bet2": bet2,
                    "teamA": teamA,
                    "teamB": teamB,
                    "bet_category1": new_bet_category1_stoiximan,
                    "bet_category2": new_bet_category2_stoiximan,
                    "has_latin": has_latin,
                    "bet_builder": bet_builder,
                    "category": category
                }
                data_stoiximan = _validate_bet_data_schema(data_stoiximan)
                with open('/Users/jimmyntak/Downloads/blade/novidata.json', 'w') as f:
                    json.dump(data_stoiximan, f)
                status_logger.info("ΕΞΑΓΑΜΕ BET BUILDER (Stoiximan) TRANSFORMED -> novidata.json")

            # ---------------------------------------------------------------------
            # BET365 branch
            # ---------------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "bet365")):
                bet_category1, bet_category2 = bet365_bet_builder_no_english(
                    bet_category1, bet_category2)
                has_latin = 0
                new_bet_category1_stoiximan, new_bet_category2_stoiximan = novibet_bet_builder_no_english(
                    bet_category1, bet_category2)

            # ---------------------------------------------------------------------
            # NOVIBET branch
            # ---------------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "novibet")):
                if has_latin_characters(bet_category1) and has_latin_characters(bet_category2):
                    has_latin = 1
                    new_bet_category1_stoiximan, new_bet_category2_stoiximan = (
                        novibet_bet_builder_english(bet_category1, bet_category2)
                    )
                else:
                    has_latin = 0
                    new_bet_category1_stoiximan, new_bet_category2_stoiximan = (
                        novibet_bet_builder_no_english(bet_category1, bet_category2)
                    )

            # Final data (after any transformations)
            data = {
                "bet1": bet1,
                "bet2": bet2,
                "teamA": teamA,
                "teamB": teamB,
                "bet_category1": bet_category1,
                "bet_category2": bet_category2,
                "has_latin": has_latin,
                "bet_builder": bet_builder,
                "category": category
            }

            if new_bet_category1_stoiximan is not None:
                data_stoiximan = {
                    "bet1": bet1,
                    "bet2": bet2,
                    "teamA": teamA,
                    "teamB": teamB,
                    "bet_category1": new_bet_category1_stoiximan,
                    "bet_category2": new_bet_category2_stoiximan,
                    "has_latin": has_latin,
                    "bet_builder": bet_builder,
                    "category": category
                }

            status_logger.info("---------------------------------------------------------------------------")
            status_logger.info(f"Processed Data -> Team A: {teamA}")
            status_logger.info(f"Processed Data -> Team B: {teamB}")
            status_logger.info(f"Processed Data -> First Selection: {bet_category1} | {bet1}")
            status_logger.info(f"Processed Data -> Second Selection: {bet_category2} | {bet2}")
            if new_bet_category1_stoiximan is not None:
                status_logger.info(
                    f"(Stoiximan) First Selection: {new_bet_category1_stoiximan} | {bet1}")
                status_logger.info(
                    f"(Stoiximan) Second Selection: {new_bet_category2_stoiximan} | {bet2}")
            status_logger.info("---------------------------------------------------------------------------")

            # -------------------------------------------------------------
            # NEW: Translate processed bet builder data to English and export to JSON
            # -------------------------------------------------------------
            try:
                # Translate first selection values
                translated_bet_category1 = translate_text(bet_category1)
                translated_bet1 = translate_text(bet1)
                # Translate second selection values
                translated_bet_category2 = translate_text(bet_category2)
                translated_bet2 = translate_text(bet2)
                
                translated_data = {
                    "First Selection": f"{translated_bet_category1} | {translated_bet1}",
                    "Second Selection": f"{translated_bet_category2} | {translated_bet2}"
                }
                
                translated_json_path = '/Users/jimmyntak/Downloads/forPerumal/translated_data.json'
                with open(translated_json_path, 'w') as f:
                    json.dump(translated_data, f, ensure_ascii=False, indent=4)
                status_logger.info(f"Exported translated bet builder data to {translated_json_path}")
            except Exception as e:
                error_logger.error(f"Error during bet builder translation export: {e}", exc_info=True)

            # -------------------------------------------------------------
            # Export final data to 'novidata.json'
            # -------------------------------------------------------------
            if os.path.isdir(os.path.join(directory, "stoiximan")):
                pass  # Already exported transformed data above
            else:
                data = _validate_bet_data_schema(data)
                with open('/Users/jimmyntak/Downloads/blade/novidata.json', 'w') as f:
                    json.dump(data, f)
                status_logger.info("ΕΞΑΓΑΜΕ BET BUILDER -> novidata.json")

        # -------------------------------------------------------------------------
        # CASE 2: SIMPLE BET (NOT BET_BUILDER)
        # -------------------------------------------------------------------------
        else:
            bet_directory = os.path.join(directory, "bet")
            bet_category_directory = os.path.join(directory, "bet_category")
            teamA_directory = os.path.join(directory, "teamA")
            teamB_directory = os.path.join(directory, "teamB")

            ocr_failed = False
            try:
                bet = (text_recognition.export_text(
                    client=client, directory=bet_directory, language_hints=language_hints) or "")
                bet_category = (text_recognition.export_text(
                    client=client, directory=bet_category_directory, language_hints=language_hints) or "")
                teamA = (text_recognition.export_text(
                    client=client, directory=teamA_directory, language_hints=language_hints) or "")
                teamB = (text_recognition.export_text(
                    client=client, directory=teamB_directory, language_hints=language_hints) or "")
            except Exception as e:
                error_logger.warning(f"Primary OCR failed (simple bet): {e}")
                ocr_failed = True
                bet = bet_category = teamA = teamB = ""

            # Optional: force OpenAI fallback for testing (set FORCE_OCR_FALLBACK=1)
            if os.environ.get("FORCE_OCR_FALLBACK") == "1":
                ocr_failed = True

            if ocr_failed or _is_ocr_failure(0, teamA=teamA, teamB=teamB, bet=bet, bet_category=bet_category):
                field_dirs = {
                    "bet": bet_directory,
                    "bet_category": bet_category_directory,
                    "teamA": teamA_directory,
                    "teamB": teamB_directory,
                }
                fallback_raw = openai_ocr_fallback(field_dirs)
                if fallback_raw is not None:
                    bet = fallback_raw.get("bet", bet) or ""
                    bet_category = fallback_raw.get("bet_category", bet_category) or ""
                    teamA = fallback_raw.get("teamA", teamA) or ""
                    teamB = fallback_raw.get("teamB", teamB) or ""
                    status_logger.info("Using OpenAI OCR fallback for simple bet fields.")
                if _is_ocr_failure(0, teamA=teamA, teamB=teamB, bet=bet, bet_category=bet_category):
                    error_logger.error("OCR fallback still missing required simple bet fields.")
                    return "error"

            status_logger.info(f"Ai Model read -> Team A: {teamA}")
            status_logger.info(f"Ai Model read -> Team B: {teamB}")
            status_logger.info(f"Ai Model read -> First Selection: {bet_category} | {bet}")

            exported = False
            bet_builder = 0
            has_latin = 0
            new_bet_category_stoiximan = None

            # -------------------------------------------------------------
            # STOIXIMAN
            # -------------------------------------------------------------
            if os.path.isdir(os.path.join(directory, "stoiximan")):
                if has_latin_characters(bet_category):
                    has_latin = 1
                else:
                    has_latin = 0

                data = {
                    "bet": bet,
                    "teamA": teamA,
                    "teamB": teamB,
                    "has_latin": has_latin,
                    "bet_category": bet_category,
                    "bet_builder": bet_builder,
                    "category": category
                }
                data = _validate_bet_data_schema(data)
                with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
                    json.dump(data, f)
                status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA (Stoiximan) -> data.json")
                exported = True

                if has_latin == 1:
                    transformed_bet_category = stoiximan_english(bet_category)
                else:
                    transformed_bet_category = stoiximan_no_english(bet_category)

                data_stoiximan = {
                    "bet": bet,
                    "teamA": teamA,
                    "teamB": teamB,
                    "bet_category": transformed_bet_category,
                    "has_latin": has_latin,
                    "bet_builder": bet_builder,
                    "category": category
                }
                data_stoiximan = _validate_bet_data_schema(data_stoiximan)
                with open('/Users/jimmyntak/Downloads/blade/novidata.json', 'w') as f:
                    json.dump(data_stoiximan, f)
                status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA (Stoiximan) -> novidata.json")

            # -------------------------------------------------------------
            # BET365
            # -------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "bet365")):
                if has_latin_characters(bet_category):
                    bet_category = bet365_english(bet_category)
                    has_latin = 1
                    new_bet_category_stoiximan = novibet_english(bet_category)
                else:
                    bet_category = bet365_no_english(bet_category)
                    has_latin = 0
                    new_bet_category_stoiximan = novibet_no_english(bet_category)

            # -------------------------------------------------------------
            # NOVIBET
            # -------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "novibet")):
                if has_latin_characters(bet_category):
                    has_latin = 1
                    new_bet_category_stoiximan = novibet_english(bet_category)
                else:
                    has_latin = 0
                    new_bet_category_stoiximan = novibet_no_english(bet_category)

            # -------------------------------------------------------------
            # FONBET
            # -------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "fonbet")):
                if has_latin_characters(bet_category):
                    has_latin = 1
                    new_bet_category_stoiximan = novibet_english(bet_category)
                else:
                    bet_category = fonbet_no_english(bet_category)
                    has_latin = 0
                    new_bet_category_stoiximan = novibet_no_english(bet_category)

            # -------------------------------------------------------------
            # BETSSON
            # -------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "betsson")):
                if has_latin_characters(bet_category):
                    has_latin = 1
                    new_bet_category_stoiximan = novibet_english(bet_category)
                else:
                    has_latin = 0
                    new_bet_category_stoiximan = novibet_no_english(bet_category)

            # -------------------------------------------------------------
            # BWIN
            # -------------------------------------------------------------
            elif os.path.isdir(os.path.join(directory, "bwin")):
                if has_latin_characters(bet_category):
                    has_latin = 1
                    new_bet_category_stoiximan = novibet_english(bet_category)
                else:
                    has_latin = 0
                    new_bet_category_stoiximan = novibet_no_english(bet_category)

            # -------------------------------------------------------------
            # Prepare final data dictionary
            # -------------------------------------------------------------
            data = {
                "bet": bet,
                "teamA": teamA,
                "teamB": teamB,
                "bet_category": bet_category,
                "has_latin": has_latin,
                "bet_builder": bet_builder,
                "category": category
            }

            if new_bet_category_stoiximan is not None:
                data_stoiximan = {
                    "bet": bet,
                    "teamA": teamA,
                    "teamB": teamB,
                    "bet_category": new_bet_category_stoiximan,
                    "has_latin": has_latin,
                    "bet_builder": bet_builder,
                    "category": category
                }
            else:
                data_stoiximan = None

            status_logger.info("---------------------------------------------------------------------------")
            status_logger.info(f"Processed Data -> Team A: {teamA}")
            status_logger.info(f"Processed Data -> Team B: {teamB}")
            status_logger.info(f"Processed Data -> Selection: {bet_category} - {bet}")
            if data_stoiximan is not None:
                status_logger.info(
                    f"Processed Data For Stoiximan -> Selection: {data_stoiximan['bet_category']} - {bet}")
            status_logger.info("---------------------------------------------------------------------------")

            # -------------------------------------------------------------
            # NEW: Translate processed data to English and export to JSON
            # -------------------------------------------------------------
            try:
                translated_bet_category = translate_text(bet_category)
                translated_bet = translate_text(bet)
                
                translated_data = {
                    "Selection": f"{translated_bet_category} - {translated_bet}"
                }
                
                translated_json_path = '/Users/jimmyntak/Downloads/forPerumal/translated_data.json'
                with open(translated_json_path, 'w') as f:
                    json.dump(translated_data, f, ensure_ascii=False, indent=4)
                status_logger.info(f"Exported translated data to {translated_json_path}")
            except Exception as e:
                error_logger.error(f"Error during translation export: {e}", exc_info=True)

            # If not stoiximan (because stoiximan already exported above) -> export
            if (not exported) and (data_stoiximan is not None):
                data_stoiximan = _validate_bet_data_schema(data_stoiximan)
                with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
                    json.dump(data_stoiximan, f)
                status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA -> data.json")
                exported = True
            elif not exported:
                data = _validate_bet_data_schema(data)
                with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
                    json.dump(data, f)
                status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA -> data.json")
                exported = True

            # Export to 'novidata.json'
            if os.path.isdir(os.path.join(directory, "stoiximan")):
                pass
            else:
                data = _validate_bet_data_schema(data)
                with open('/Users/jimmyntak/Downloads/blade/novidata.json', 'w') as f:
                    json.dump(data, f)

    except Exception as e:
        error_logger.error(f'An error occurred: {e}', exc_info=True)
        return 'error'