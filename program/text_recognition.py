import os
import shutil
import sys
from google.cloud import vision
import unicodedata


stoiximan_bets = ['Επόμενο Γκολ', 'Ασιατικό (Over/Under) Γκολ', 'Ασιατικό Χάντικαπ (Τρέχον σκόρ -)', 'Ασιατικό (Over/Under) - 1ο Ημίχρονο - Συνολικά Γκολ', 'Πόντοι', 'Χάντικαπ - Τελικό Αποτέλεσμα', 'Τελικό Αποτέλεσμα']

stoiximan_english_bets = ['Match Result', 'Over/Under Total Goals (extra)', 'Current Score', 'Over/Under Total Goals','First-Half Result',
                          'Next Team to score (Goal )', 'Over/Under First Half Goals','Double chance', 'Both teams to score',
                          'Asian Handicap (Current Score - )', 'Asian Handicap (Current Score - ) (extra)','Asian (Over/Under) Goals', 
                          'Asian (Over/Under) Goals (extra)', 'Asian Handicap - First Half (Current Score - )','Halftime/Full time']

bet365_bets = ['Τελικό Σκόρ', 'Επόμενο Γκολ ος γκολ', 'γκολ αγώνα', '1ο ημίχρονο σύνολο γκολ', '( - ) Ασιατικό Χάντικαπ', '( - ) Στοίχημα Γκολ', '( - ) 1ο ημίχρονο - ασιατικό χάντικαπ', 'Χάντικαπ']

def jaccard_similarity(str1, str2):
  str1_set = set(str1.lower()) 
  str2_set = set(str2.lower())

  intersection = str1_set & str2_set  # Κοινά στοιχεία
  union = str1_set | str2_set       # Ένωση

  if len(union) == 0:
      return 0.0

  return len(intersection) / len(union)

def new_bet_category(bet_category,bet,teamA=None,teamB=None):
  if bet_category.lower() == 'Ακριβές Σκορ'.lower():
    bet_category1,bet1,bet_category2,bet2 = final_score(bet,teamA,teamB)
    return bet_category1,bet1,bet_category2,bet2
  elif bet_category.lower() == '1ο Ημίχρονο - Ακριβές Σκορ'.lower():
    bet_category1,bet1,bet_category2,bet2 = first_half_final_score(bet,teamA,teamB)
    return bet_category1,bet1,bet_category2,bet2
  elif bet_category == 'Correct Score':
    bet_category1,bet1,bet_category2,bet2 = final_score_english(bet,teamA,teamB)
    return bet_category1,bet1,bet_category2,bet2
  elif bet_category.lower() == '1st Half - Correct Score':
    bet_category1,bet1,bet_category2,bet2 = first_half_final_score_english(bet,teamA,teamB)
    return bet_category1,bet1,bet_category2,bet2
       
def translate_from_bet365(bet_category, bet365_bets):
  jac_bet = {}
  for i, bet_title in enumerate(bet365_bets):
    jac = jaccard_similarity(bet_category,bet_title)
    jac_bet[i] = jac

  max_jac_index = max(jac_bet, key=jac_bet.get)

  if jac_bet[max_jac_index] > 0.85:
    if max_jac_index == 0:
        return "Ακριβές Σκορ"
    elif max_jac_index == 1:
        return "Να σκοράρει το Γκολ ()"
    elif max_jac_index == 2:
      return "Γκολ Over/Under"
    elif max_jac_index == 3:
        return '1o Ημίχρονο - Γκολ Over/Under'
    elif max_jac_index == 4:
        return "Ασιατικά Χάντικαπ"
    elif max_jac_index == 5:
       return "Ασιατικό Γκολ Over/Under" 
    elif max_jac_index == 6:
        return '1o Ημίχρονο - Χάντικαπ'
    elif max_jac_index == 7 or max_jac_index == 8:
        return 'Χάντικαπ'

  else:
    return bet_category 
   
def translate_from_stoiximan_english(bet_category, stoiximan_english_bets):
  jac_bet = {}
  for i, bet_title in enumerate(stoiximan_english_bets):
    jac = jaccard_similarity(bet_category,bet_title)
    jac_bet[i] = jac

  max_jac_index = max(jac_bet, key=jac_bet.get)

  if jac_bet[max_jac_index] > 0.85:
    if max_jac_index == 0:
        return "Full Time Result"
    elif max_jac_index == 1:
        return "Goals Over/Under (extra)"
    elif max_jac_index == 2:
      return "Correct Score"
    elif max_jac_index == 3:
        return 'Goals Over/Under'
    elif max_jac_index == 4:
        return "Half Time Result" 
    elif max_jac_index == 5:
      return "Team to Score Goal ( )"
    elif max_jac_index == 6:
        return '1st Half - Goals Over/Under'
    elif max_jac_index == 7:
        return "Double Chance" 
    elif max_jac_index == 8:
      return "Both teams to score"
    elif max_jac_index == 9:
        return 'Asian Handicap'
    elif max_jac_index == 10:
        return "Asian Handicap (extra)" 
    elif max_jac_index == 11:
      return "Asian Goals Over/Under"
    elif max_jac_index == 12:
        return 'Asian Goals Over/Under (extra)'
    elif max_jac_index == 13:
        return "1st Half - Handicap" 
    else:
        return 'Halftime/Fulltime'

  else:
    return bet_category 

def translate_from_stoiximan(bet_category, stoiximan_bets):
  jac_bet = {}
  for i, bet_title in enumerate(stoiximan_bets):
    jac = jaccard_similarity(bet_category,bet_title)
    jac_bet[i] = jac

  max_jac_index = max(jac_bet, key=jac_bet.get)

  if jac_bet[max_jac_index] > 0.7:
    if max_jac_index == 0:
      return "Να σκοράρει το Γκολ ()"
    elif max_jac_index == 1:
      return "Ασιατικό Γκολ Over/Under"
    elif max_jac_index == 2:
      return "Ασιατικό Χάντικαπ"
    elif max_jac_index == 3:
      return '1ο Ημίχρονο - Ασιατικό Γκολ Over/Under'
    elif max_jac_index == 4:
      return 'Συνολικοί Πόντοι Αγώνα'
    elif max_jac_index == 5:
      return 'Χάντικαπ'
    else:
        return 'Τελικό Αποτέλεσμα'

  else:
    return bet_category 

def is_mostly_greek(word):
    # Επιστρέφει True αν η πλειοψηφία των χαρακτήρων είναι ελληνικά
    greek_count = sum(1 for char in word if 'Α' <= char <= 'Ω' or 'α' <= char <= 'ω')
    total_letters = sum(1 for char in word if char.isalpha())
    return greek_count > total_letters / 2  # Πλειοψηφία ελληνικών γραμμάτων

def clean_text(text):
    # Διορθώσεις για συχνά μπερδέματα
    corrections = {
        'M': 'Μ',  # Αγγλικό κεφαλαίο 'M' -> Ελληνικό κεφαλαίο 'Μ'
        'A': 'Α',  # Αγγλικό κεφαλαίο 'A' -> Ελληνικό κεφαλαίο 'Α'
        'E': 'Ε',  # Αγγλικό κεφαλαίο 'E' -> Ελληνικό κεφαλαίο 'Ε'
        'T': 'Τ',  # Αγγλικό κεφαλαίο 'T' -> Ελληνικό κεφαλαίο 'Τ'
        'H': 'Η',  # Αγγλικό κεφαλαίο 'H' -> Ελληνικό κεφαλαίο 'Η'
        'P': 'Ρ',  # Αγγλικό κεφαλαίο 'P' -> Ελληνικό κεφαλαίο 'Ρ'
        'N': 'Ν',  # Αγγλικό κεφαλαίο 'N' -> Ελληνικό κεφαλαίο 'Ν'
        'I': 'Ι',  # Αγγλικό κεφαλαίο 'I' -> Ελληνικό κεφαλαίο 'Ι'
        'O': 'Ο',  # Αγγλικό κεφαλαίο 'O' -> Ελληνικό κεφαλαίο 'Ο'
    }

    for eng_char, gr_char in corrections.items():
        text = text.replace(eng_char, gr_char)

    return text

def export_text(client, directory, language_hints):
    # Συλλογή εικόνων από τον φάκελο
    image_files = [f for f in os.listdir(directory) if f.endswith(('.jpg', '.jpeg', '.png'))]

    if image_files:
        text = ''
        for image in image_files:
            image_path = os.path.join(directory, image)
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            
            response = client.text_detection(image=image, image_context={"language_hints": language_hints})
            texts = response.text_annotations
            
            if texts:
                extracted_text = texts[0].description
                # Εφαρμογή διορθώσεων μόνο για ελληνικές λέξεις
                words = extracted_text.split()
                cleaned_words = [
                    clean_text(word) if is_mostly_greek(word) else word
                    for word in words
                ]
                cleaned_text = ' '.join(cleaned_words)
                text += cleaned_text

        return text

def get_new_photo_path(folder_path):
  filenames = os.listdir(folder_path)

  photo_paths = []

  for filename in filenames:
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path) and filename.endswith(('.jpg', '.jpeg', '.png')):
      photo_paths.append(file_path)

  if not photo_paths:
    return None

  photo_timestamps = []

  for photo_path in photo_paths:
    photo_timestamps.append(os.path.getmtime(photo_path))

  newest_photo_index = photo_timestamps.index(max(photo_timestamps))

  return photo_paths[newest_photo_index]

def handicaps(bet,current_score):
  score = current_score.split(" - ")
  score = [int(x) for x in score]
  current_goals = score[0]+score[1]
  
  bet = bet.split(" ")
  if "-" in bet[-1]:
    handicap = float(bet[-1][1:].replace(",","."))
    if handicap == 0.25 or handicap == 0.5 or handicap == 0.75 or handicap == 1.0 or handicap == 1.25:
      current_goals+=1
    elif handicap == 1.5 or handicap == 1.75 or handicap == 2.0 or handicap == 2.25:
      current_goals += 2
    else:
      current_goals += 3
    return "Over/Under Γκολ", f"Over {current_goals-0.5}"
  else:
    return False, False

'''x,y = handicaps("Φίλκιρ/Ελίντι U19 +1,25","3 - 1")
if x == False:
  print("right")
else:
  print(x,y)'''

def final_score(bet,teamA,teamB):
  bet = bet.strip()
  print(bet)
  score = bet.split("-")
  print(score)
  score = [int(x) for x in score]
  print(score)

  over = score[0]+score[1]-0.5

  if score[0] > score[1]:
    return "Τελικό Αποτέλεσμα", teamA, "Over/Under Γκολ", f"Over {over}"
  elif score[0] < score[1]:
    return "Τελικό Αποτέλεσμα", teamB, "Over/Under Γκολ", f"Over {over}"
  else:
    return "Τελικό Αποτέλεσμα", "Ισοπαλία", "Over/Under Γκολ", f"Over {over}"

def final_score_english(bet,teamA,teamB):
  score = bet.split(" - ")
  score = [int(x) for x in score]
  over = score[0]+score[1]-0.5

  if score[0] > score[1]:
    return "Full Time Result", teamA, "Goals Over/Under", f"Over {over}"
  elif score[0] < score[1]:
    return "Full Time Result", teamB, "Goals Over/Under Γκολ", f"Over {over}"
  else:
    return "Full Time Result", "Draw", "Goals Over/Under Γκολ", f"Over {over}"



'''bet_cat1,bet1,bet_cat2,bet2 = final_score("1 - 0","pao","osfp")
print(f"Bet Category1 = {bet_cat1}")
print(f"Bet1 = {bet1}")
print(f"Bet Category2 = {bet_cat2}")
print(f"Bet2 = {bet2}")'''

def first_half_final_score(bet,teamA,teamB):
  score = bet.split(" - ")
  score = [int(x) for x in score]
  over = score[0]+score[1]-0.5

  if score[0] > score[1]:
    return "1ο Ημίχρονο - Αποτέλεσμα ", teamA, " 1o Ημίχρονο - Γκολ Over/Under ", f"Over {over}"
  elif score[0] < score[1]:
    return "1ο Ημίχρονο - Αποτέλεσμα ", teamB, " 1o Ημίχρονο - Γκολ Over/Under ", f"Over {over}"
  else:
    return "1ο Ημίχρονο - Αποτέλεσμα ", "Ισοπαλία", " 1o Ημίχρονο - Γκολ Over/Under ", f"Over {over}"
  
def first_half_final_score_english(bet,teamA,teamB):
  score = bet.split(" - ")
  score = [int(x) for x in score]
  over = score[0]+score[1]-0.5

  if score[0] > score[1]:
    return "Half Time Result", teamA, "1st Half - Goals Over/Under", f"Over {over}"
  elif score[0] < score[1]:
    return "Half Time Result", teamB, "1st Half - Goals Over/Under", f"Over {over}"
  else:
    return "Half Time Result", "Draw", "1st Half - Goals Over/Under", f"Over {over}"

def first_half_handicaps(bet,current_score):
  score = current_score.split(" - ")
  score = [int(x) for x in score]
  current_goals = score[0]+score[1]
  
  bet = bet.split(" ")
  if "-" in bet[-1]:
    handicap = float(bet[-1][1:].replace(",","."))
    if handicap == 0.25 or handicap == 0.5 or handicap == 0.75 or handicap == 1.0 or handicap == 1.25:
      current_goals+=1
    elif handicap == 1.5 or handicap == 1.75 or handicap == 2.0 or handicap == 2.25:
      current_goals += 2
    else:
      current_goals += 3
    return " 1o Ημίχρονο - Γκολ Over/Under", f"Over {current_goals-0.5}"
  else:
    return False, False

def asian_over_under(bet,current_score):

  score = current_score.split(" - ")
  score = [int(x) for x in score]
  current_goals = score[0]+score[1]
  
  bet = bet.split(" ")
  if bet[0].lower == 'over':
    if bet[1] == 1.0 or bet[1] == 1.25 or bet[1] == 1.5 or bet[1] == 1.75:
      current_goals+=1
    elif bet[1] == 2.0 or bet[1] == 2.25 or bet[1] == 2.5 or bet[1] == 2.75:
      current_goals+=2
    elif bet[1] == 3.0 or bet[1] == 3.25 or bet[1] == 3.5 or bet[1] == 3.75:
      current_goals+=3
    elif bet[1] == 4.0 or bet[1] == 4.25 or bet[1] == 4.5 or bet[1] == 4.75:
      current_goals+=4
    elif bet[1] == 5.0 or bet[1] == 5.25 or bet[1] == 5.5 or bet[1] == 5.75:
      current_goals+=5
    elif bet[1] == 6.0 or bet[1] == 6.25 or bet[1] == 6.5 or bet[1] == 6.75:
      current_goals+=6
    else:
      return False,False
  else:
    return False,False 
  return "Over/Under Γκολ", f"Over {current_goals-0.5}"
  
def first_half_asian_over_under(bet,current_score):

  score = current_score.split(" - ")
  score = [int(x) for x in score]
  current_goals = score[0]+score[1]
  
  bet = bet.split(" ")
  if bet[0].lower == 'over':
    if bet[1] == 1.0 or bet[1] == 1.25 or bet[1] == 1.5 or bet[1] == 1.75:
      current_goals+=1
    elif bet[1] == 2.0 or bet[1] == 2.25 or bet[1] == 2.5 or bet[1] == 2.75:
      current_goals+=2
    elif bet[1] == 3.0 or bet[1] == 3.25 or bet[1] == 3.5 or bet[1] == 3.75:
      current_goals+=3
    elif bet[1] == 4.0 or bet[1] == 4.25 or bet[1] == 4.5 or bet[1] == 4.75:
      current_goals+=4
    elif bet[1] == 5.0 or bet[1] == 5.25 or bet[1] == 5.5 or bet[1] == 5.75:
      current_goals+=5
    elif bet[1] == 6.0 or bet[1] == 6.25 or bet[1] == 6.5 or bet[1] == 6.75:
      current_goals+=6
    else:
      return False,False
  else:
    return False,False 
  return "1o Ημίχρονο - Γκολ Over/Under", f"Over {current_goals-0.5}"


fonbet_bets = ['Αποτέλεσμα','Συνολικά','1ο Ημίχρονο Συνολικά', '1ο Ημίχρονο Αποτέλεσμα']

def translate_from_fonbet(bet_category, fonbet_bets):
  jac_bet = {}
  for i, bet_title in enumerate(fonbet_bets):
    jac = jaccard_similarity(bet_category,bet_title)
    jac_bet[i] = jac

  max_jac_index = max(jac_bet, key=jac_bet.get)

  if jac_bet[max_jac_index] > 0.85:
    if max_jac_index == 0:
        return "Τελικό Αποτέλεσμα"
    elif max_jac_index == 1:
        return "Γκολ Over/Under"
    elif max_jac_index == 2:
      return "1o Ημίχρονο - Γκολ Over/Under"
    elif max_jac_index == 3:
        return '1o Ημίχρονο - Αποτέλεσμα'
  else:
    return bet_category
  


novibet_bets = ['Να σκοράρει το Γκολ ()', 'Ασιατικό Γκολ Over/Under', 'Ασιατικό Χάντικαπ', '1ο Ημίχρονο - Ασιατικό Γκολ Over/Under', 'Πόντοι Over/Under', 'Χάντικαπ (3-Way)', 'Γκολ Over/Under', 'Τελικό Αποτέλεσμα']


def translate_from_novibet(bet_category, novibet_bets):
  jac_bet = {}
  for i, bet_title in enumerate(novibet_bets):
    jac = jaccard_similarity(bet_category,bet_title)
    jac_bet[i] = jac

  max_jac_index = max(jac_bet, key=jac_bet.get)

  if jac_bet[max_jac_index] > 0.7:
    if max_jac_index == 0:
      return "Επόμενο Γκολ"
    elif max_jac_index == 1:
      return "Ασιατικό (Over/Under) Γκολ"
    elif max_jac_index == 2:
      return "Ασιατικό Χάντικαπ (Τρέχον σκόρ -)"
    elif max_jac_index == 3:
      return 'Ασιατικό (Over/Under) - 1ο Ημίχρονο - Συνολικά Γκολ'
    elif max_jac_index == 4:
      return 'Πόντοι'
    elif max_jac_index == 5:
      return 'Χάντικαπ - Τελικό Αποτέλεσμα'
    elif max_jac_index == 6:
      return 'Γκολ Over/Under'
    else:
      return 'Τελικό Αποτέλεσμα'

  else:
    return bet_category 
  

novibet_english_bets = ['Full Time Result', 'Goals Over/Under (extra)', 'Correct Score', 'Goals Over/Under','Half Time Result',
                          'Team to Score Goal ( )', '1st Half - Goals Over/Under','Double chance', 'Both teams to score',
                          'Asian Handicap', 'Asian Handicap (extra)','Asian Goals Over/Under', 
                          'Asian Goals Over/Under (extra)', '1st Half - Handicap','Halftime/Fulltime']

def translate_from_novibet_english(bet_category, novibet_english_bets):
  jac_bet = {}
  for i, bet_title in enumerate(novibet_english_bets):
    jac = jaccard_similarity(bet_category,bet_title)
    jac_bet[i] = jac

  max_jac_index = max(jac_bet, key=jac_bet.get)

  if jac_bet[max_jac_index] > 0.85:
    if max_jac_index == 0:
        return "Match Result"
    elif max_jac_index == 1:
        return "Over/Under Total Goals (extra)"
    elif max_jac_index == 2:
      return "Correct Score"
    elif max_jac_index == 3:
        return 'Over/Under Total Goals'
    elif max_jac_index == 4:
        return "First-Half Result" 
    elif max_jac_index == 5:
      return "Next Team to score (Goal )"
    elif max_jac_index == 6:
        return 'Over/Under First Half Goals'
    elif max_jac_index == 7:
        return "Double Chance" 
    elif max_jac_index == 8:
      return "Both teams to score"
    elif max_jac_index == 9:
        return 'Asian Handicap (Current Score - )'
    elif max_jac_index == 10:
        return "Asian Handicap (Current Score - ) (extra)" 
    elif max_jac_index == 11:
      return "Asian (Over/Under) Goals"
    elif max_jac_index == 12:
        return 'Asian (Over/Under) Goals (extra)'
    elif max_jac_index == 13:
        return "Asian Handicap - First Half (Current Score - )" 
    else:
        return 'Halftime/Full time'

  else:
    return bet_category 