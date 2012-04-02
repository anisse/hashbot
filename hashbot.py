#!/usr/bin/env python

from __future__ import print_function

import requests
import json
import time

try:
    import config
    credentials = config.credentials
    r_config = config.r_config
except:
    print("Can't find a config.py file. Consider creating one !")
    credentials = {'username': 'username', 'password' : 'password'}
    r_config = {}

twitter_sample_parameters = {
        'stall_warnings': 'true',
        }

r = requests.post('https://stream.twitter.com/1/statuses/sample.json',
        data=twitter_sample_parameters,
        auth=(credentials['username'], credentials['password']),
        config=r_config)

i=0
t=time.clock()
for line in r.iter_lines():
    if line: # filter out keep-alive new lines
        text = str(line)
        tweet = json.loads(text)
        #print(json.dumps(tweet, indent=4))
        print(tweet['user']['screen_name'] +": " + tweet['text'])
        if 'warning' in tweet:
            print("==== WARNING !!! ====")
            print(json.dumps(tweet, indent=4))
            print("==== WARNING !!! ====")
        i+=1
        #print(".", end="")
        if (i%100 == 0):
            t1=time.clock()
            print("%d tweets per second"%(100./(t1-t),))
            t=t1



