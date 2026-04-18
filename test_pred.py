import sys
import os
sys.path.append(os.path.abspath("e:/SLIIT/2Y 2S/IT2021 - Artificial Intelligence and Machine Learning Project/tourist-forecast-kandy"))

from utils.theme import get_current_week_prediction, get_next_week_prediction

print("Current:", get_current_week_prediction())
print("Next:", get_next_week_prediction())
