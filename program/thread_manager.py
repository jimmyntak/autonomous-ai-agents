import os
import shutil
import threading
import gc
import psutil
import time
from google.cloud import vision
from ultralytics import YOLO
from playwright.sync_api import sync_playwright
from logger_config import performance_logger, status_logger
import novibet as nv_module
import stoiximan as sx_module
from config_manager import ConfigManager
from novibet import browser_closed_event
import bet_data_processor as bet_data_processor
import openai_fallback
import subprocess
import traceback
import torch  # Make sure torch is imported


# Φόρτωση των ρυθμίσεων από το config.json
config_manager = ConfigManager('/Users/jimmyntak/Downloads/blade/config/config.json')
betting_config = config_manager.get_betting_config()
general_config = config_manager.get_general_config()

betting_companies = betting_config.betting_companies
path_to_model = general_config.path_to_model
google_credentials = general_config.google_credentials

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials
client = vision.ImageAnnotatorClient()

category = ''
main_thread_trigger = threading.Event()
main_thread_data = {}

def log_system_resources():
    """Λειτουργία για περιοδική καταγραφή της χρήσης πόρων του συστήματος."""
    status_logger.info(f'-----------------------------------------SYSTEM RESOURCE MONITOR-----------------------------------------')

    while True:
        cpu_usage = psutil.cpu_percent(interval=1)  # Χρήση CPU για όλο το σύστημα
        memory_info = psutil.virtual_memory()  # Πληροφορίες μνήμης για όλο το σύστημα
        
        performance_logger.info(f'System CPU Usage: {cpu_usage}%')
        performance_logger.info(f'System Memory Usage: {memory_info.used / (1024 * 1024):.2f} MB')  # Χρήση μνήμης σε MB

        time.sleep(10)  # Καταγραφή κάθε 60 δευτερόλεπτα

def process_data(instance, company_name):
    global main_thread_data

    if len(main_thread_data) == 9:
        instance.bet1 = main_thread_data["bet1"]
        instance.bet2 = main_thread_data["bet2"]
        instance.bet_category1 = main_thread_data["bet_category1"]
        instance.bet_category2 = main_thread_data["bet_category2"]
        instance.teamA = main_thread_data["teamA"]
        instance.teamB = main_thread_data["teamB"]
        instance.bet_builder = main_thread_data["bet_builder"]
        instance.has_latin = main_thread_data["has_latin"]
    else:
        instance.bet = main_thread_data["bet"]
        instance.bet_category = main_thread_data["bet_category"]
        instance.teamA = main_thread_data["teamA"]
        instance.teamB = main_thread_data["teamB"]
        instance.bet_builder = 0
        instance.has_latin = main_thread_data["has_latin"]

    instance.amount = betting_companies[company_name].bet_amounts.get(category, 0.1)
    status_logger.info(f'Amount for {company_name}: {instance.amount}')
    return instance

def run_main(save_path):
    start = time.time()
    global main_thread_data, category
    
    # Remove the existing runs directory if it exists.
    if os.path.exists("/Users/jimmyntak/Downloads/blade/runs"):
        shutil.rmtree("/Users/jimmyntak/Downloads/blade/runs")
    
    # Initialize the YOLO model.
    model = YOLO(path_to_model)
    
    # Determine the device to use (MPS for Apple devices if available, otherwise CPU).
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device)
    print(f"Using device: {device}")
    
    # Run prediction with the model.
    model.predict(source=save_path, save_crop=True)
    
    # Process the data after prediction.
    main_thread_data = bet_data_processor.run(client, category)
    if main_thread_data != 'error':
        main_thread_trigger.set()
        elapsed_time = time.time() - start
        performance_logger.info(f"ΧΡΟΝΟΣ YOLO+TEXT RECOGNITION: {elapsed_time:.2f} seconds")
    else:
        status_logger.error("Error in bet_data_processor.run - attempting OpenAI fallback")
        # Fallback to OpenAI API when YOLO crops are missing or bet_data_processor fails
        try:
            status_logger.info("Starting OpenAI Vision API fallback analysis")
            main_thread_data = openai_fallback.process_with_openai_fallback(save_path, category)
            
            if main_thread_data != 'error':
                status_logger.info("OpenAI fallback successful - extracting data structure")
                # Extract the main data for thread processing (matching bet_data_processor output format)
                if main_thread_data.get('bet_builder', False):
                    # Bet builder case - return main_data with 9 fields 
                    extracted_data = main_thread_data['main_data']
                    main_thread_data = {
                        "bet1": extracted_data.get('bet1', ''),
                        "bet2": extracted_data.get('bet2', ''),
                        "bet_category1": extracted_data.get('bet_category1', ''),
                        "bet_category2": extracted_data.get('bet_category2', ''),
                        "teamA": extracted_data.get('teamA', ''),
                        "teamB": extracted_data.get('teamB', ''),
                        "bet_builder": extracted_data.get('bet_builder', 1),
                        "has_latin": extracted_data.get('has_latin', 0),
                        "category": category
                    }
                else:
                    # Simple bet case - return main_data with 6 fields
                    extracted_data = main_thread_data['main_data']
                    main_thread_data = {
                        "bet": extracted_data.get('bet', ''),
                        "bet_category": extracted_data.get('bet_category', ''),
                        "teamA": extracted_data.get('teamA', ''),
                        "teamB": extracted_data.get('teamB', ''),
                        "bet_builder": 0,
                        "has_latin": extracted_data.get('has_latin', 0)
                    }
                
                main_thread_trigger.set()
                elapsed_time = time.time() - start
                performance_logger.info(f"ΧΡΟΝΟΣ YOLO+OPENAI FALLBACK: {elapsed_time:.2f} seconds")
                status_logger.info("OpenAI fallback completed successfully")
            else:
                status_logger.error("OpenAI fallback also failed")
        except Exception as e:
            status_logger.error(f"OpenAI fallback error: {e}")
            status_logger.error(traceback.format_exc())

def run_novibet(url):
    flag = 0
    while True:
        if flag == 0:
            novibet_instance = nv_module.Novibet(url=url, username=betting_companies['novibet'].username, password=betting_companies['novibet'].password)
        try:
            novibet_instance.start()
            
            if not main_thread_trigger.wait(timeout=900):
                novibet_instance.novibetDriver.refresh()
                novibet_instance.flag_refreshed = True
                status_logger.info('Refreshed the page after 15 minutes')
                flag = 1
                continue

            main_thread_trigger.clear()
            
            novibet_instance = process_data(novibet_instance, 'novibet')
            result = novibet_instance.run()
            if result == 'closed':
                browser_closed_event.wait()  # Περιμένει μέχρι να λάβει το σήμα ότι μπορεί να συνεχίσει
                browser_closed_event.clear()
            flag = 0
        except Exception as e:
            status_logger.error(f"Error in run_novibet: {e}")
            # Print full stack trace
            status_logger.error(traceback.format_exc())
        finally:
            time.sleep(1)
            gc.collect()

def run_stoiximan(url):
    while True:
        try:
            stoiximan_instance = sx_module.Stoiximan(url=url, username=betting_companies['stoiximan'].username, password=betting_companies['stoiximan'].password)
            
            with sync_playwright() as playwright:
                stoiximan_instance.set_playwright(playwright)
                stoiximan_instance.start()

                main_thread_trigger.wait()
                main_thread_trigger.clear()

                stoiximan_instance = process_data(stoiximan_instance, 'stoiximan')
                stoiximan_instance.run()
        except Exception as e:
            status_logger.error(f"Error in run_stoiximan: {e}")

def run_threads():
    threading.Thread(target=log_system_resources, daemon=True).start()

    for company, info in betting_companies.items():
        urls = info.urls
        for url in urls:
            if company == "novibetttt":
                threading.Thread(target=run_novibet, args=(url,), daemon=True).start()
            if company == "stoiximan":
                threading.Thread(target=run_stoiximan, args=(url,), daemon=True).start()

def trigger_event(save_path, bet_category):
    global category
    category = bet_category
    
    # Thread to run the main functionality
    main_thread = threading.Thread(target=run_main, args=(save_path,))
    
    
    # Start both threads
    main_thread.start()


    # Wait for both threads to complete
    main_thread.join()
