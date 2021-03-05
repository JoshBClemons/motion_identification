import pdb
from flask import jsonify, g, request # temp
from .. import db
from ..auth import basic_auth, token_auth
from . import api

@api.route('/tokens', methods=['POST'])
@basic_auth.login_required
def new_token():
    """
    Request a user token.
    This endpoint is requires basic auth with username and password.
    """
    if g.current_user.token is None:
        g.current_user.generate_token()
        db.session.add(g.current_user)
        db.session.commit()
    return jsonify({'token': g.current_user.token})