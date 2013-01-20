#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import requests
import requests_oauthlib
import ujson as json
import time
import re
import argparse
import cPickle as pickle

# For error handling
import sys
import traceback
from httplib import IncompleteRead
import signal


# TODO:
# - remote commands directly from twitter master by dm:
#    - to ban user and remove its previous RTs
#    - to follow user and RT last matching tweet
# - watch user stream for tweets as well as sample stream
# - auto-follow when match
# - rate-limit RT at 1 per week
# - auto-ban when one posts lots of hashes (above a threshold)
# - caching of timeline


try:
    import config
    credentials = config.credentials
except:
    print("Can't find a config.py file. Consider creating one !")
    credentials = {'username': "", 'access_token': u"", 'access_token_secret': u"",
            'consumer_key': u"", 'consumer_secret': u"", }


oauth_credentials = requests_oauthlib.OAuth1(credentials['consumer_key'],
        credentials['consumer_secret'],
        credentials['access_token'],
        credentials['access_token_secret'],
        signature_type='auth_header')


twitter_api_base = "https://api.twitter.com/1.1/statuses"

simplematcher = re.compile("[a-f0-9]{32,64}", re.UNICODE | re.IGNORECASE)
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
            """, re.VERBOSE | re.UNICODE | re.IGNORECASE)
nonmatcher = re.compile(r"""
            (
                ([0-9]{32,})| # only numbers
                ([a-z]{32,})| # or only letters
                (pussy)  # or forbidden keywords…
            )
            """, re.VERBOSE | re.UNICODE | re.IGNORECASE)


banlist = []
with open("banlist", "r") as f:
    banlist = pickle.load(f)

bannedusers = re.compile("(" + "|".join(banlist) + ")",
            re.VERBOSE | re.UNICODE | re.IGNORECASE)

def get_banned_users_list():
    print("List of banned users: %s" % banlist)

def ban_user(screen_name):
    global banlist
    global bannedusers
    if screen_name in banlist:
        return
    banlist.append(screen_name)
    bannedusers = re.compile("(" + "|".join(banlist) + ")",
                re.VERBOSE | re.UNICODE | re.IGNORECASE)
    with open("banlist", "w") as f:
        pickle.dump(banlist, f)


#bannedusers = re.compile(r"""
#        (
#        filestamp|
#        sha1yourtweet|
#        skykingbalogna|
#        OnlineHashCrack|
#        md5cracktk|
#        enigion|
#        Stupersticious|
#        myserviceangel|
#        sharebdmv|
#        svenkaths|
#        sieunhanyt|
#        sieunhanyt001|
#        LoggieLogs
#        #r_bomber
#        )
#        """, re.VERBOSE | re.UNICODE | re.IGNORECASE)
bannedclients = re.compile(r"""
        (
        Bitbucket|
        enigio.com|
        twittbot.net|
        FloodAPP|
        Checktrip|
        SMM Hostserver|
        md5_answer|
        BizCaf|
        CormyBot|
        Insane-Limits|
        123_spark|
        vmcqa|
        hoge.com|
        onlinehashcrack.com|
        splashcube
        )
        """, re.VERBOSE | re.UNICODE | re.IGNORECASE)


def filter_tweet_text(tweet_text):
    searches = (
            (simplematcher, True),
            (matcher, True),
            (nonmatcher, False),
            )
    for regex, result in searches:
        if (regex.search(tweet_text) == None) == result:
            return False
    return True

def filter_tweet(tweet):
    """
    Filter a tweet to find a hash
    """
    if not filter_tweet_text(tweet['text']):
        return False
    if bannedclients.search(tweet['source']):
        return False
    if bannedusers.search(tweet['user']['screen_name']):
        return False
    if tweet['user']['screen_name'] == credentials['username']: # Do not match self tweets :-)
        return False
    return True

def received_error(r):
    print("Response status: %s" % r.status_code)
    print("Response error: %s" % r.error)
    try:
        print("Response text: %s" % json.dumps(json.loads(str(r.text)),
                                            indent=4))
    except:
        print("Response text: " + r.text)

def delete_tweet(tweet_id):
    """
    Delete the given tweet id using the global OAuth hook
    """
    r = requests.post(twitter_api_base + "/destroy/" +
            tweet_id + ".json",
            auth=oauth_credentials)
    if r.status_code != 200:
        print("Attempted to delete tweet %s" % tweet_id)
        received_error(r)
    else:
        print("Successfully deleted tweet %s." % tweet_id)

def retweet(tweet_id):
    """
    Retweet the given tweet id using the global OAuth hook
    """
    r = requests.post(twitter_api_base + "/retweet/" +
            tweet_id + ".json",
            auth=oauth_credentials)
    if r.status_code != 200:
        print("Attempted to retweet tweet %s" % tweet_id)
        received_error(r)
    else:
        print("Successfully retweeted tweet %s." % tweet_id)

def get_list_of_rts():
    """
    Get list of previours RTs, using the global OAuth hook.
    """
    r = requests.get(twitter_api_base +
            "/retweeted_by_me.json?include_entities=false&count=100",
            auth=oauth_credentials)
    if r.status_code != 200:
        received_error(r)
        return None
    else:
        return json.loads(str(r.text))

def dump_list_of_rts():
    """
    Output list of already retweeted tweets in suitable format for the test
    function.

    Use in a standalone, one-shot manner, like that:
    python -c 'import hashbot; hashbot.dump_list_of_rts()'
    """
    rtlist = get_list_of_rts()
    if rtlist:
        for tweet in rtlist:
            print('            # Extracted from https://twitter.com/#!/%s/status/%s' %
                    (tweet['retweeted_status']['user']['screen_name'],
                        tweet['retweeted_status']['id_str']))
            print('            (ur"""%s""", False),' %
                    tweet['retweeted_status']['text'])

def refilter_previous_rts():
    """
    Rerun filter_tweet on previous RTs in order to keep a clean timeline after
    we've added more filter rules.

    Use in a standalone, one-shot manner, like that:
    python -c 'import hashbot; hashbot.refilter_previous_rts()'
    """
    rtlist = get_list_of_rts()
    if rtlist == None:
        return
    for tweet in rtlist:
        if not filter_tweet(tweet['retweeted_status']):
            print("Previous tweet does not pass the filter anymore !")
            print("@%s (%s) : %s" % (
                tweet['retweeted_status']['user']['screen_name'],
                tweet['retweeted_status']['source'],
                tweet['retweeted_status']['text']))
            answer = raw_input("Delete ? [y/N] ")
            if answer == 'y':
                delete_tweet(tweet['id_str'])


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


class RateCounterWatchdog:
    """
    Simple rate measurement
    """
    def __init__(self):
        self._interval = 5000
        self._i = 0
        self._t = time.time()
        # This is the watchdog part
        # we need a watchdog to ensure that everything is running smoothly and
        # to occasionnaly reset the loop if requests (or anything else) fails us.
        signal.signal(signal.SIGALRM, self.unresponsive_handler)
        signal.alarm(600)

    def unresponsive_handler(self, signum, stackframe):
        raise RuntimeError("Unresponsive! Raising exception to reboot main loop.")

    def increment(self):
        self._i += 1
        #print(".", end="")
        if (self._i % self._interval == 0):
            self._t1 = time.time()
            print("%s : %d tweets per second" % (time.strftime("%c"),
                                self._interval / (self._t1 - self._t)))
            #print("interval = %f, t1 = %f, t = %f, diff = %f, i = %d" %
            #            (self._interval, self._t1, self._t, self._t1 - self._t, self._i))

            # time.time could go back. That's normal. Somehow (check NTP configuration)
            if ("%d" % (self._interval / (self._t1 - self._t))) == "-1":
                print("Something weird happenning interval = %f, t1 = %f, t = %f " %
                        (self._interval, self._t1, self._t))
            self._t = self._t1

            # Reset watchdog
            signal.alarm(600)


def process_json_line(jline):
    """
    Core of the bot. That's here that we parse and decide what to do with what
    the server is sending us.
    """
    if jline:  # filter out keep-alive new lines
        text = str(jline)
        try:
            tweet = json.loads(text)
        except:
            print("Unable to load text as json:")
            print(text)
            return # nothing to process after all
        if 'user' in tweet and 'screen_name' in tweet['user'] \
                and 'text' in tweet:
            if filter_tweet(tweet):
                print("Matched tweet!")
                print("@%s (%s) : %s" % (
                    tweet['user']['screen_name'],
                    tweet['source'],
                    tweet['text']))
                retweet(tweet['id_str'])
        else:
            #print(json.dumps(tweet, indent=4))
            pass
        if 'warning' in tweet:
            print("==== WARNING !!! ====")
            print(json.dumps(tweet, indent=4))
            print("==== WARNING !!! ====")

def open_twitter_sample_stream():
    """
    Return a requests Response object on success or None on failure
    """
    twitter_sample_parameters = {'stall_warnings': 'true', }

    r = requests.post('https://stream.twitter.com/1/statuses/sample.json',
            data=twitter_sample_parameters,
            auth=oauth_credentials,
            stream=True,
            timeout=300)

    if r.status_code != 200:
        print("Response status: %s" % r.status_code)
        print("Response error: %s" % r.error)
        print("Response text: %s" % r.text)
        return None

    return r


def run_forever(func):
    """
    Run function passed in argument forever with exponential backoff
    """
    def forever_wrapped():
        waittime = 1.
        lastwait = time.time()
        while True:
            try:
                func()
            except KeyboardInterrupt:  # we allow user to interrupt us ;-
                print("User abort")
                return
            except IOError as ioe:
                print("Connection was closed: %s" % str(ioe))
            except IncompleteRead as ire:
                print("Twitter sending us shit: %s" % str(ire))
            except RuntimeError as re:
                print("Problem during this run: %s" % str(re))
            except BaseException as e:
                traceback.print_exception(type(e), e, sys.exc_traceback)
            else:
                print("Terminated... ", end="")

            now = time.time()
            # reset waittime when we ran for at least 10 minute without issues
            if lastwait + waittime + 600 < now:
                waittime = 1.
            lastwait = now

            print("Restarting in %.0f seconds" % waittime)
            signal.alarm(0) # reset watchdog here :-/
            time.sleep(waittime)

            # max wait time is 20min
            waittime = min(20 * 60, waittime * 2)  # exponential backoff
    return forever_wrapped


@run_forever
def hashbot():
    # Twitter stream API on the "sample" feed
    # twitter pretends it gives ~1% of the tweet at a given time, I think it's
    # much lower; they must adapt its verbosity/rate level to load.
    stream = open_twitter_sample_stream()
    if stream == None:
        return

    c = RateCounterWatchdog()

    for line in stream.iter_lines():
        process_json_line(line)
        c.increment()


def main():
    actions = { "run": hashbot,
                "dumprts": dump_list_of_rts,
                "refilter": refilter_previous_rts,
                "listbanned": get_banned_users_list,
                #TODO: add subparsers for this command
                "testdata": dump_json_lines_from_stream }
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=actions.keys(), default="run", nargs='?', help="Running mode")
    args = parser.parse_args()
    actions[args.command]()

if  __name__ == '__main__':
    main()
