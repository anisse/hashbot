#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import requests
import ujson as json
import time
import re

# For error handling
import sys
import traceback

from oauth_hook import OAuthHook


try:
    import config
    credentials = config.oauth_credentials
    r_config = config.r_config
except:
    print("Can't find a config.py file. Consider creating one !")
    credentials = { 'access_token' : "", 'access_token_secret': "",
            'consumer_key' : "", 'consumer_secret' : "", }
    r_config = {}


oauth_hook = OAuthHook(credentials['access_token'], credentials['access_token_secret'],
        credentials['consumer_key'], credentials['consumer_secret'], True)


matcher = re.compile(r"""
            (   \s| # Space
                \A ) # or beginning of string
            (
                ([a-f0-9]{32})| # md5
                ([a-f0-9]{40})| # sha1
                ([a-f0-9]{64}) # sha256
            )
            (   (
                    \Z| #end of string
                    [\s,] # or space or ,
                ) | (
                    [\.] # if ends with point
                    (\Z|\s) #point should be followed by space or end of string
                )
            )
            """, re.VERBOSE|re.UNICODE|re.IGNORECASE)
nonmatcher = re.compile(r"""
            (
                ([0-9]{32,})| # only numbers
                ([a-z]{32,})| # or only letters
                (pussy)  # or forbidden keywords…
            )
            """, re.VERBOSE|re.UNICODE|re.IGNORECASE)
simplematcher = re.compile("[a-f0-9]{32,64}", re.UNICODE|re.IGNORECASE)

# not yet sure how to measure if a pre filter would be efficient
def pre_filter(json_text):
    if simplematcher.search(json_text):
        return True
    return False

def filter_tweet(tweet_text):
    """
    Filter a tweet to find a hash
    """
    if matcher.search(tweet_text):
        if not nonmatcher.search(tweet_text):
            return True
    return False

def retweet(tweet_id):
    """
    Retweet the given tweet id using the global OAuth hook
    """
    r = requests.post("https://api.twitter.com/1/statuses/retweet/"+tweet_id+".json",
            config=r_config,
            hooks={'pre_request': oauth_hook })
    if r.status_code != 200:
        print("Attempted to retweet tweet %s"%tweet_id)
        print("Response status: %s"%r.status_code)
        print("Response error: %s"%r.error)
        print("Response text: %s"%json.dumps(json.loads(str(r.text)), indent=4))
    else:
        print("Successfully retweeted tweet %s."%tweet_id)

def dump_list_of_rts():
    """
    Output list of already retweeted tweets in suitable format for the test function,
    using the global OAuth hook.

    Use in a standalone, one-shot manner, like that:
    python -c 'import hashbot; hashbot.dump_list_of_rts()'
    """
    r = requests.get("https://api.twitter.com/1/statuses/retweeted_by_me.json?include_entities=false&count=100",
            config=r_config,
            hooks={'pre_request': oauth_hook })
    if r.status_code != 200:
        print("Response status: %s"%r.status_code)
        print("Response error: %s"%r.error)
        print("Response text: %s"%json.dumps(json.loads(str(r.text)), indent=4))
    else:
        for tweet in json.loads(str(r.text)):
            print('            # Extracted from https://twitter.com/#!/%s/status/%s'%
                    (tweet['retweeted_status']['user']['screen_name'], tweet['retweeted_status']['id_str']))
            print('            (ur"""%s""", False),'%tweet['retweeted_status']['text'])

def dump_json_lines_from_stream(n, output_name):
    """
    Dump a few lines

    Use in a standalone, one-shot manner, like that:
    python -c 'import hashbot; hashbot.dump_json_lines_from_stream(4000, "json_test_file.txt")'
    """
    file_output = open(output_name, "w")
    stream = open_twitter_sample_stream()
    for i in stream.iter_lines():
        file_output.write(str(i))
        file_output.write("\n")
        n -= 1
        if n <= 0:
            break
    file_output.close()



class RateCounter:
    """
    Simple rate measurement
    """
    def __init__(self):
        self._interval=5000.
        self._i=0
        self._t=time.clock()
    def increment(self):
        self._i+=1
        #print(".", end="")
        if (self._i%self._interval== 0):
            self._t1=time.clock()
            print("%d tweets per second"%(self._interval/(self._t1-self._t),))
            self._t=self._t1

def process_json_line(jline):
    """
    Core of the bot. That's here that we parse and decide what to do with what the server is sending us.
    """
    if jline: # filter out keep-alive new lines
        text = str(jline)
        tweet = json.loads(text)
        if 'user' in tweet and 'screen_name' in tweet['user'] and 'text' in tweet:
            #print(tweet['user']['screen_name'] +": " + tweet['text'])
            if filter_tweet(tweet['text']): # we could be (much?) faster by filtering before loading json
                print("Matched tweet!")
                print(tweet['text'])
                #print(json.dumps(tweet, indent=4))
                retweet(tweet['id_str'])
            pass
        else:
            #print(json.dumps(tweet, indent=4))
            pass
        if 'warning' in tweet:
            print("==== WARNING !!! ====")
            print(json.dumps(tweet, indent=4))
            print("==== WARNING !!! ====")

def process_json_line_prefilter(jline):
    if jline: # filter out keep-alive new lines
        text = str(jline)
        if pre_filter(text):
            print(".", end="")
            tweet = json.loads(text)
            if 'user' in tweet and 'screen_name' in tweet['user'] and 'text' in tweet:
                if filter_tweet(tweet['text']):
                    print("Matched tweet!")
                    print(tweet['text'])
                    retweet(tweet['id_str'])

def process_json_line_prefilter_2(jline):
    if jline: # filter out keep-alive new lines
        text = str(jline)
        tweet = json.loads(text)
        if 'user' in tweet and 'screen_name' in tweet['user'] and 'text' in tweet:
            if pre_filter(tweet['text']) and filter_tweet(tweet['text']):
                print("Matched tweet!")
                print(tweet['text'])
                retweet(tweet['id_str'])

def process_json_line_load_only(jline):
    if jline: # filter out keep-alive new lines
        text = str(jline)
        tweet = json.loads(text)
        if 'user' in tweet and 'screen_name' in tweet['user'] and 'text' in tweet:
            pass

def open_twitter_sample_stream():
    """
    Return a requests Response object on success or None on failure
    """
    twitter_sample_parameters = { 'stall_warnings': 'true', }

    r = requests.post('https://stream.twitter.com/1/statuses/sample.json',
            data=twitter_sample_parameters,
            config=r_config,
            hooks={'pre_request': oauth_hook} )

    if r.status_code != 200:
        print("Response status: %s"%r.status_code)
        print("Response error: %s"%r.error)
        print("Response text: %s"%r.text)
        return None

    return r


def run_forever(func):
    """
    Run function passed in argument forever with exponential backoff
    """
    def forever_wrapped():
        waittime = 1.
        lastwait = time.clock()
        while True:
            try:
                func()
            except KeyboardInterrupt: # we allow user to interrupt us ;-
                print("User abort")
                return
            except IOError as ioe:
                print("Connection was closed: %s"%str(ioe))
            except BaseException as e:
                traceback.print_exception(type(e), e, sys.exc_traceback)
            else:
                print("Terminated... ", end="")

            now = time.clock()
            # reset waittime when we ran for at least 10 minute without issues
            if lastwait + waittime + 600 < now:
                waittime = 1.
            lastwait = now

            print("Restarting in %.0f seconds"%waittime)
            time.sleep(waittime)

            # max wait time is 20min
            if waittime < 20*60:
                waittime *= 2 # exponential backoff
    return forever_wrapped

@run_forever
def hashbot():

    # Twitter stream API on the "sample" feed
    # twitter pretends it gives ~1% of the tweet at a given time, I think it's much lower
    # they must adapt its verbosity/rate level to load.
    stream = open_twitter_sample_stream()
    if stream == None:
        return

    c = RateCounter()

    for line in stream.iter_lines():
        process_json_line(line)
        c.increment()

if  __name__ == '__main__':
    hashbot()

