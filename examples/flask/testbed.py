#! /usr/bin/env python

import requests
from datetime import datetime


def test_list(total):
    r = requests.get('http://localhost:5000/users')
    assert r.status_code == 200, r.status_code
    data = r.json()
    assert data['_total'] == total, 'expected %s, got %s' % (total, data['_total'])
    assert len(data['_items']) == total, 'expected %s, got %s' % (total, len(data['_items']))
    return data

data = test_list(7)

# Get by id
user = data['_items'][0]
r = requests.get('http://localhost:5000/users/%s' % user['id'])
assert r.status_code == 200, r.status_code
data = r.json()
assert user == data, 'user: %s, data: %s' % (user, data)

# Get by nick
r = requests.get('http://localhost:5000/users/%s' % user['nick'])
assert r.status_code == 200, r.status_code
assert data == r.json(), 'data: %s, nick_data: %s' % (data, r.json())

# Create user
payload = {
    'nick': 'n00b',
    'birthday': '2016-05-18T11:40:32+00:00',
    'password': '123456'
}
r = requests.post('http://localhost:5000/users', json=payload)
assert r.status_code == 200, r.status_code
data = r.json()
new_user_id = data.pop('id')
expected = {
    'nick': 'n00b',
    'birthday': '2016-05-18T11:40:32+00:00',
}
assert data == expected, 'data: %s, expected: %s' % (payload, expected)
test_list(8)

# Change password
r = requests.put('http://localhost:5000/users/%s/password' % new_user_id,
                 json={'password': 'abcdef'})
assert r.status_code == 200, r.status_code
data = r.json()
assert new_user_id == data.pop('id')
assert data == expected, 'data: %s, expected: %s' % (r.json(), expected)

# Delete user
r = requests.delete('http://localhost:5000/users/%s' % new_user_id)
assert r.status_code == 200, r.status_code
test_list(7)
