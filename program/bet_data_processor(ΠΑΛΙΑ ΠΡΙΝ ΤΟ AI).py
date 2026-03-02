import text_recognition as text_recognition
import os
import re
from logger_config import status_logger, error_logger
import json
from google.cloud import translate_v3
from google.oauth2 import service_account

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
            
            bet1 = text_recognition.export_text(
                client=client, directory=bet1_directory, language_hints=language_hints)
            bet_category1 = text_recognition.export_text(
                client=client, directory=bet_category1_directory, language_hints=language_hints)
            bet2 = text_recognition.export_text(
                client=client, directory=bet2_directory, language_hints=language_hints)
            bet_category2 = text_recognition.export_text(
                client=client, directory=bet_category2_directory, language_hints=language_hints)
            teamA = text_recognition.export_text(
                client=client, directory=teamA_directory, language_hints=language_hints)
            teamB = text_recognition.export_text(
                client=client, directory=teamB_directory, language_hints=language_hints)

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

            bet = text_recognition.export_text(
                client=client, directory=bet_directory, language_hints=language_hints)
            bet_category = text_recognition.export_text(
                client=client, directory=bet_category_directory, language_hints=language_hints)
            teamA = text_recognition.export_text(
                client=client, directory=teamA_directory, language_hints=language_hints)
            teamB = text_recognition.export_text(
                client=client, directory=teamB_directory, language_hints=language_hints)

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
                with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
                    json.dump(data_stoiximan, f)
                status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA -> data.json")
                exported = True
            elif not exported:
                with open('/Users/jimmyntak/Downloads/blade/data.json', 'w') as f:
                    json.dump(data, f)
                status_logger.info("ΕΞΑΓΑΜΕ ΑPLO STOIXIMA -> data.json")
                exported = True

            # Export to 'novidata.json'
            if os.path.isdir(os.path.join(directory, "stoiximan")):
                pass
            else:
                with open('/Users/jimmyntak/Downloads/blade/novidata.json', 'w') as f:
                    json.dump(data, f)

    except Exception as e:
        error_logger.error(f'An error occurred: {e}', exc_info=True)
        return 'error'