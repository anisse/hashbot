#!/usr/bin/env python3

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

twitter_search_parameters = {
        'track': 'home,love,<3,like,twitter,google,ipad,iphone,android,bieber,the,i,he,a', #what we're searching for
        'stall_warnings': 'true',
        }

r = requests.post('https://stream.twitter.com/1/statuses/filter.json',
        data=twitter_search_parameters,
        auth=(credentials['username'], credentials['password']),
        config=r_config)

i=0
t=time.clock()
for line in r.iter_lines():
    if line: # filter out keep-alive new lines
        text = str(line, encoding="utf-8")
        tweet = json.loads(text)
        #print(json.dumps(tweet, indent=4))
        #print(tweet['user']['screen_name'] +": " + tweet['text'])
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



