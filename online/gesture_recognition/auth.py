import pdb
from flask import g, jsonify, session
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from . import db
from .models import User

# Authentication objects for username/password auth, token auth, and a
# token optional auth that is used for open endpoints.
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')
token_optional_auth = HTTPTokenAuth('Bearer')

@basic_auth.verify_password
def verify_password(username, password): # nickname, password
    """Password verification callback."""
    if not username or not password or username == "''" or password == "''":
        return False
    user = User.query.filter_by(username=username).first()
    if user is None: # if not a user, create the user 
        user_dict = {'username': username, 'password': password}
        user = User.create(user_dict)
    elif not user.verify_password(password):
        return False
    else:
        user.new_login()       
    user.ping() # mark user as online   
    db.session.add(user)
    db.session.commit()
    g.current_user = user
    return True

@basic_auth.error_handler
def password_error(user):
    """Return a 401 error to the client."""
    # To avoid login prompts in the browser, use the "Bearer" realm.
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})

@token_auth.verify_token
def verify_token(token, add_to_session=False):
    """Token verification callback."""
    if add_to_session:
        # clear the session in case auth fails
        if 'username' in session:
            del session['username']
    user = User.query.filter_by(token=token).first()
    if user is None:
        return False
    user.ping()
    db.session.add(user)
    db.session.commit()
    g.current_user = user
    if add_to_session:
        session['username'] = user.username
    return True

@token_auth.error_handler
def token_error():
    """Return a 401 error to the client."""
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})

@token_optional_auth.verify_token
def verify_optional_token(token):
    """Alternative token authentication that allows anonymous logins."""
    pdb.set_trace()
    if token == '':
        # no token provided, mark the logged in users as None and continue
        g.current_user = None
        return True
    # but if a token was provided, make sure it is valid
    return verify_token(token)
