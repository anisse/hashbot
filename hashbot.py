#!/usr/bin/env python3

import requests
import json

try:
    import config
    credentials = config.credentials
    r_config = config.r_config
except:
    print("Can't find a config.py file. Consider creating one !")
    credentials = {'username': 'username', 'password' : 'password'}
    r_config = {}


r = requests.post('https://stream.twitter.com/1/statuses/filter.json',
        data={'track': 'requests'}, auth=(credentials['username'], credentials['password']), config=r_config)

for line in r.iter_lines():
    if line: # filter out keep-alive new lines
        text = str(line, encoding="utf-8")
        tweet = json.loads(text)
        print(tweet['text'])
