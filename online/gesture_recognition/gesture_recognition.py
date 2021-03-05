#!/usr/bin/env python

# TO DO

## ONLINE
# on start, search for image directories, users and frames db and raise error if not yet initiated 
# develop unit tests

## OFFLINE
# modify motion_identification to render high-level basics (run first page, run /stats/)
# create simple rendering for monitoring page (use sketch to design monitoring dashboard)
# verify monitoring works while application runs with single user  
# enable timing between systems --> sleep 
    # setup model builder to run once a day
    # setup evaluator to compare models once a day 
# ? setup using flask/gunicorn/nginx

## DEPLOYMENT
# replicate model on AWS using EC2
# login from multiple users and see how poorly latency is impacted. see if improvement with celery
# deploy using SageMaker, Data Lake, etc. 
# verify monitoring works while application runs with multiple users 
# ? test using Swagger
# reduce text on website. add link to more information
    # include instructions and basic contact info 

## MAYBE
# don't process image entries if user opts out of saving images (no paths exist)
# replace print statements with logging
# implement airflow


import pdb
from .models import Frame, User
from . import db, image_directory#, stats
from flask import Blueprint, Response, current_app #, jsonify
import os
import threading
import time

main = Blueprint('main', __name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

@main.before_app_first_request
def before_first_request():
    """Start a background thread that looks for users that leave."""
    def find_offline_users(app):
        with app.app_context():
            while True:
                users = User.find_offline_users()
                db.session.remove() 
                time.sleep(5)
    if not current_app.config['TESTING']:
        thread = threading.Thread(target=find_offline_users,
                                  args=(current_app._get_current_object(),))
        thread.start()

# @main.before_app_request
# def before_request():
#     """Update requests per second stats."""
#     stats.add_request()

# @main.route('/stats', methods=['GET'])
# def get_stats():
#     return jsonify({'requests_per_second': stats.requests_per_second()})

@main.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response

@main.route('/')
def index():
    global dir_path
    path = os.path.join(dir_path,'static/local.html')
    return Response(open(path).read(), mimetype="text/html")

"""Hand Gesture Prediction Application by Josh Clemons

This script records a client's hand gesture from streamed video and forwards the video frames to a server that predicts the hand gesture and returns the prediction to the client.

This script must be executed concurrently with server.py, which runs on a client's computer and sends webcam streaming video as frame arrays

Please refer to requirements.txt for a listing of all required packages.

To execute this script, input the following:
python client.py --server-ip SERVER_IP

Currently, this program executes and receives streaming frames from a webcam connected to my Windows 10 machine. Eventually, this application will be scaled such that individuals will be able to navigate to a publicly hosted website, stream their web camera footage and perform hand gestures, and receive a prediction of their hand gesture.

NOTE: This script is currently incomplete.
"""