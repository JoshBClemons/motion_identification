import pdb
from keras.models import load_model
import json
import numpy as np
import time
from config import Config
import os

# Import model
model = load_model(Config.MODEL_PATH)

# Import gesture map
with open(Config.GESTURES_MAP_PATH, 'r') as fp:
    gestures_map = json.load(fp)

def predict_gesture(frame, true_gest, session):
    """Predict user gesture from procesed frame 
    
    Args:
        frame (array): Array containing processed imaged
        true_gest (str): Ground-truth gesture inputted by user
        session (dict): Client session data

    Returns:
        label (str): Message returned to client 
        pred_gest (str): Predicted gesture
        pred_conf (float): Prediction confidence, percentage
        pred_time (float): Prediction time, seconds
    """
    
    if true_gest not in list(gestures_map.values()) and session['start_countdown'] == True:
        label = "No gesture predicted. Please input gesture."
        pred_gest = 'NA'
        pred_conf = pred_time = 0
    elif true_gest in list(gestures_map.values()) and session['start_countdown'] == True and session['pause_count'] < 2:
        label = "Saving background. One moment please."
        pred_gest = 'NA'
        pred_conf = pred_time = 0
    elif session['pause_count'] >= 2:
        start_time = time.time()
        pred = model.predict(frame)
        pred_time = round(time.time()-start_time, 2)
        pred_index = np.argmax(pred, axis=1)
        pred_gest = gestures_map[str(pred_index[0])]
        pred_conf = round(np.max(pred)*100,4)
        label = f'{pred_conf}% confident that gesture is {pred_gest}. Result predicted in {pred_time} seconds.'
    else: 
        label = "No gesture predicted. Please exit camera's field of view then press 'b' to save background and commence predictions."
        pred_gest = 'NA'
        pred_conf = pred_time = 0
        
    return [label, pred_gest, pred_conf, pred_time]