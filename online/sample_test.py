 #!/usr/bin/env python -W ignore::DeprecationWarning

import pdb
import base64
import json
import time
import unittest
import mock

import requests

from gesture_recognition import create_app, db, socketio
from gesture_recognition.models import User, Frame


class FlackTests(unittest.TestCase):
    # setup application (executes at beginning of unit testing)
    def setUp(self):
        self.app = create_app('testing')

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()  
        db.create_all()
        self.client = self.app.test_client() # used to process all API and socketio calls 

    # teardown application (executes at end of unit testing)
    def tearDown(self):
        db.drop_all()
        self.ctx.pop()

    # configure request header compatibility
    def get_headers(self, basic_auth=None, token_auth=None):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if basic_auth is not None:
            headers['Authorization'] = 'Basic ' + base64.b64encode(basic_auth.encode('utf-8')).decode('utf-8')
        if token_auth is not None: # need to test 
            headers['Authorization'] = 'Bearer ' + token_auth
        return headers

    # configure GET API compatibility
    def get(self, url, basic_auth=None, token_auth=None):
        response = self.client.get(url, headers=self.get_headers(basic_auth, token_auth))
        # clean up the database session, since this only occurs when the app
        # context is popped.
        db.session.remove()
        body = response.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, response.status_code, response.headers

    # configure POST API compatibility
    def post(self, url, data=None, basic_auth=None, token_auth=None):
        data = data if data is None else json.dumps(data)
        response = self.client.post(url, data=data, headers=self.get_headers(basic_auth, token_auth))
        pdb.set_trace()
        # clean up the database session, since this only occurs when the app context is popped.
        db.session.remove() # investigate why necessary
        body = response.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, response.status_code, response.headers

    # test api/users endpoint
    def test_users(self):
        # successful registration - return 200, token
        response, status, headers = self.post('/api/users', data={'username': 'foo', 'password': 'bar'})
        self.assertEqual(status, 200)
        self.assertIn('token', list(response.keys()))

        # register duplicate user - return 400
        response, status, headers = self.post('/api/users', data={'username': 'foo', 'password': 'bar'})
        self.assertEqual(status, 400)

        # blank or no username or password - return 400
        response, status, headers = self.post('/api/users', data={'username': '', 'password': 'bar'})
        self.assertEqual(status, 400)
        response, status, headers = self.post('/api/users', data={'username': 'foo', 'password': ''})
        self.assertEqual(status, 400)
        response, status, headers = self.post('/api/users', data={'username': None, 'password': 'bar'})
        self.assertEqual(status, 400)
        response, status, headers = self.post('/api/users', data={'username': 'foo', 'password': None})
        self.assertEqual(status, 400)

        # get user list - return 200, dictionary with 'users' where each user dictionary includes only 'online' and 'username'
        response, status, headers = self.get('/api/users')
        self.assertEqual(status, 200)
        self.assertIn('users', list(response.keys()))
        self.assertEqual(2, len(list(response['users'][0].keys())))
        self.assertIn('online', list(response['users'][0].keys()))
        self.assertIn('username', list(response['users'][0].keys()))

    # test api/tokens endpoint
    def test_tokens(self):
        # blank or no username or password - return 401    
        response, status, headers = self.post('/api/tokens', basic_auth="'':bar")
        self.assertEqual(status, 401)
        response, status, headers = self.post('/api/tokens', basic_auth="foo:''")
        self.assertEqual(status, 401)
        response, status, headers = self.post('/api/tokens', basic_auth=":bar")
        self.assertEqual(status, 401)
        response, status, headers = self.post('/api/tokens', basic_auth="foo:")
        self.assertEqual(status, 401)        

        # incorrect password - return 401
        response, status, headers = self.post('/api/users', data={'username': 'foo', 'password': 'bar'})
        self.assertEqual(status, 200)
        response, status, headers = self.post('/api/tokens', basic_auth="foo:baz")
        self.assertEqual(status, 401)

        # successful authentication - return 200, token
        response, status, headers = self.post('/api/tokens', basic_auth="foo:bar")
        self.assertEqual(status, 200)
        self.assertIn('token', list(response.keys()))

    # test socketio connections
    def test_socketio(self):
        client = socketio.test_client(self.app)

        # create a user and a token
        response, status, headers = self.post('/api/users', data={'username': 'foo', 'password': 'bar'})
        self.assertEqual(status, 200)
        token = response['token']
        pdb.set_trace()
        # clear old socket.io notifications
        client.get_received()

        # artificially make user be offline
        user = User.query.filter_by(token=token).first()
        user.online = False
        db.session.add(user)
        db.session.commit()

        # ping user via socketio to make it be back online - YOU ARE HERE. user.ping()
        client.emit('ping_user', token)
        self.assertEqual(user.online, True)
        recvd = client.get_received()
        self.assertEqual(len(recvd), 1)
        self.assertEqual(recvd[0]['args'][0]['class'], 'User')
        self.assertEqual(recvd[0]['args'][0]['model']['nickname'], 'foo')
        self.assertEqual(recvd[0]['args'][0]['model']['online'], True)

        # post a message via socketio
        client.emit('post_message', {'source': 'foo'}, token)
        recvd = client.get_received()
        self.assertEqual(len(recvd), 1)
        self.assertEqual(recvd[0]['args'][0]['class'], 'Message')
        self.assertEqual(recvd[0]['args'][0]['model']['source'], 'foo')
        self.assertEqual(recvd[0]['args'][0]['model']['html'], 'foo')

        # disconnect the user
        client.disconnect()
        recvd = client.get_received()
        self.assertEqual(len(recvd), 1)
        self.assertEqual(recvd[0]['args'][0]['class'], 'User')
        self.assertEqual(recvd[0]['args'][0]['model']['nickname'], 'foo')
        self.assertEqual(recvd[0]['args'][0]['model']['online'], False)

# frame_uneven = frame_nobg[0::2, 0::3]
# frame_small = frame_nobg[0::6, 0::6]

# test_object = FlackTests()
# test_object.setUp()
# test_object.tearDown()
# test_object.setUp()
# test_object.test_user()

if __name__ == '__main__':
    unittest.main()