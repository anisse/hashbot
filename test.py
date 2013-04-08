#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import time
import cStringIO

from hashbot import filter_tweet_text,\
        process_json_line,simplematcher,\
        run_forever, filter_tweet_entropy
import ujson as json

def test_filter():
    filter_tests_strings = [
            ("hello", False),
            ("this is my home", False),
            # md5 hashes
            ("hello ce114e4501d2f4e2dcea3e17b546f339", True),
            ("ce114e4501d2f4e2dcea3e17b546f339", True),
            ("ce114e4501d2f4e2dcea3e17b546f339 hello", True),
            ("Hello ce114e4501d2f4e2dcea3e17b546f339 sum", True),
            ("Hello ce114e4501d2f4e2dcea3e17b546f339. ", True),
            ("Hello ce1144501d2f4e2dcea3e17b546f339", False), #incorrect length
            ("Hello ce11231144501d2f4e2dcea3e17b546f339", False), #incorrect length
            # sha1sum
            ("a54d88e06612d820bc3be72877c74f257b561b19", True),
            ("a8e06612d820bc3be72877c74f257b561b19", False), #incorrect length
            # sha256
            ("c7be1ed902fb8dd4d48997c6452f5d7e509fbcdbe2808b16bcf4edce4c07d14e", True),
            ("ce1ed902fb8dd4d48997c6452f5d7e509fbcdbe2808b16bcf4edce4c07d14e", False), # incorrect length
            # this is another bot we don't want to match
            ("SHA1:AB840554A8158026C5788C5312ADF030B51CFFAC:PiSHaoFzwYDxQ5", False),
            # simpler tests
            ("SHA1:AB840554A8158026C5788C5312ADF030B51CFFAC:", False),
            ("AB840554A8158026C5788C5312ADF030B51CFFAC", True),
            ("SHA1:AB840554A8158026C5788C5312ADF030B51CFFAC ", False),


            # list of extracted tweets
            # Extracted from https://twitter.com/#!/jonoberheide/status/26912068460355584
            (ur"""da6a36097a2b3383db1aaf98cea0ad1cd8973bce""", True),
            # Extracted from https://twitter.com/#!/KZENIKzx/status/189769476756090880
            (ur"""@dRacokim เค้าพูดความจริงไง อาจพึ่งรู้ตัวไรเง้5555555555555555555555555555555555555555""", False),
            # Extracted from https://twitter.com/#!/mjg59/status/184651598373457920
            (ur"""ad23d1317c1230c72a1a8b88b442f516""", True),
            # Extracted from https://twitter.com/#!/Aissn/status/189475112267956225
            (ur"""Future proofing ba351eaa0880baaa8482edc021c872c2""", True),
            # Extracted from https://twitter.com/#!/super_ttoon/status/189766242930925568
            (ur"""เอลฟ์อย่าทำร้ายมิน เราต้องบอกว่ามินผอม มินผอม เอารูปนี้ไปดูแล้วท่อง http://t.co/ByHSqGjV 55555555555555555555555555555555""", False),
            # Extracted from https://twitter.com/#!/Larissa_Ferrari/status/189763441156829184
            (ur"""@ericacasmartins @LineTheodoro EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE \õ/ HAUAHAUAHUAUAHAUAHAUHAUAHAUAHAUA""", False),
            # Extracted from https://twitter.com/#!/js_yuri125/status/189720096615305218
            (ur"""120410 사랑비 Love Rain E06 윤아 Cut TP (by Moonlight) magnet:?xt=urn:btih:89333B05CE1E7C2736B321CDACE48926CD69069D #loverain #yoona #윤아""", False),
            # Extracted from https://twitter.com/#!/_SilviaFromMars/status/189740926145544193
            (ur"""Mi piacciono i numeri [cit] 3287619519265713204635687603651657675617 #ITALIANDIRECTIONERSLOVEONED""", False),
            # Extracted from https://twitter.com/#!/kookai4825/status/189733313475383297
            (ur"""I downloaded video af5806f9ba73d87fc6dc1244ca11d447.flv - http://t.co/ySGC5BZl""", False),
            # Extracted from https://twitter.com/#!/HounamHazza/status/189729748308590592
            (ur"""#1DMerda ☺☻♥♠○◘•☼◙ 46373684268237986278428024892479 +7yu7ey3r4es= #1DMerda #1DMerda #1DMerda #1DMerda dysjhkdfhjsdhjkhjdvgh7643389893zz""", False),
            # Extracted from https://twitter.com/#!/_rlaxodus/status/189719615469924353
            (ur"""120410 Love Rain full by moonlight magnet:?xt=urn:btih:FC56D0914827363AEB15115161EBE915A8BDE19F""", False),
            # Extracted from https://twitter.com/#!/_yearn/status/189725676830597121
            (ur"""패션왕 E08.720p mp4 (748MB) magnet:?xt=urn:btih:DB31676546FE4F421F4196F336EFDBDB3209A0AF""", False),
            # Extracted from https://twitter.com/#!/yuldori/status/189718589958406145
            (ur"""120410 Fashion King - Ep. 08 (Moonlight) magnet:?xt=urn:btih:83C04E6894809029BEC2D37CB5F30A32114DF1ED""", False),
            # Extracted from https://twitter.com/#!/BlackDahliaDie/status/189700505268793344
            (ur"""1000000100000001001100010000000110000001011100010011000100110000 esta, por ejemplo. Os acabo de llamar gilipollas y ni os habéis enterado.""", False),
            # Extracted from https://twitter.com/#!/stephanietamp/status/189716523655512064
            (ur"""RT @mentarimamonto RT @sarahndrk adaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa aja cobaan nya kl lg bnr2 syg sm orang. haduuuh""", False),
            # Extracted from https://twitter.com/#!/Lastbyezzz/status/189715877745262592
            (ur"""63ce1f16518ff4702f942cc212d2628a""", True),
            # Extracted from https://twitter.com/#!/ljmiolleh/status/189712249651331073
            (ur"""@zniiperr ขำเลยกูเจอคำว่าฟิน 55555555555555555555555555555555""", False),
            # Extracted from https://twitter.com/#!/1DandJBFansTR/status/189711515648147456
            (ur"""@Jawaad_S I love you &lt;33333333333333333333333333333333""", False),
            # Extracted from https://twitter.com/#!/balliiteeee/status/189692649698111489
            (ur"""@lauravizla :DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD DAUNE! :DDDDDDDDDDDDD Es te bļeģ smejos par tevi. :DDD Es Endiju pasaukšu. :DDD""", False),
            # Extracted from https://twitter.com/#!/Mr3bhom/status/189687893340598273
            (ur"""يــــوم الجمعـــــة 25 /4/ 1433 . http://184.105.234.34/50/58/5058810dbe16d51106541a530410c875/ba64807/5058_w_1.3gp?PIN:26D3655E""", False),
            # Extracted from https://twitter.com/#!/planpan/status/189671049338691585
            (ur"""เยดดดดดดดดด มาดามอังแคแนดังล๊าวววววววววววว ดอกกกก เกิดเชี่ยอะไรกับประเทศนี้กันนนนน 555555555555555555555555555555555555555555555555555555555""", False),
            # Extracted from https://twitter.com/#!/_0386580450682/status/189670407304003585
            (ur"""محشش طرباان يصلي ورالامام  http://64.71.156.132/d4/3e/d43e48ca0736f96c2fbc98fb57fea4cd/ba124807/d43e_w_1.3gp?c=141232906&u=615244077&s=BLs5m""", False),
            # Extracted from https://twitter.com/#!/StickleA/status/189659556614373376
            (ur"""(2012Q2) 這いよれ！ニャル子さん 第01話 「第三種接近遭遇、的な」 (TX 1280x720 x264 AAC).mp4 JpazsuDaqe 320,716,998 e94265e3e0cb639d72c53a64c2b63341a953370a""", True),
            # Extracted from https://twitter.com/#!/malwr/status/189649305731203072
            (ur"""[66ebf239705ed81bae9a0c9763a6b42b] Analysis at http://t.co/Mn2BXBfO""", False),
            # Extracted from https://twitter.com/#!/bofarj/status/189648588534587392
            (ur"""أغنى خمسه أشخاص في العالم 🏧

http://65.49.33.119/5a/20/5a209bd5013f5d3d40bff80c1552cf5d/ba64807/5a20_w_1.3gp?c=315130915&u=804745""", False),
            # Extracted from https://twitter.com/#!/Asura206218/status/189622262947786753
            (ur"""이거 ㅅㅈ 없는 어제 슴타운 마그넷이에여~~
magnet:?xt=urn:btih:9A4EEE8E0650EAD3A0F269040E1CEEC47904435C""", False),
            # Extracted from https://twitter.com/#!/eyadbo50/status/189606523834601472
            (ur"""الشعب السعودي والمزح
http://184.105.234.76/01/bc/01bc8b2a578c542fe9ad1ac9b5a5037f/ba64807/2011_01bc_w_1.3gp?c=280758399&u=636763085&s=BLxL_p""", False),
            # Extracted from https://twitter.com/#!/b7aral3yoon/status/189596444926296064
            (ur"""الشوته عجيبه

http://184.105.234.201/41/6e/416ef1cd2ebb81097c502223eb3c600c/ba123207/416e_w_2.3gp?c=123959570&u=793686681&s=BMTtpH""", False),
            # Extracted from https://twitter.com/#!/wantKYU/status/189578269631328256
            (ur"""เอสเจจะรู้มั้ยว่านางฟ้าของพวกมึงตอนนี้เป็นควายกันไปหมดเเล้ว 55555555555555555555555555555555""", False),
            # Extracted from https://twitter.com/#!/Moni_Lovo/status/189579491541135360
            (ur"""Ignorada como por 96541254523654525541587863999954 vez :)""", False),
            # Extracted from https://twitter.com/#!/Faii__JB/status/189567944659959808
            (ur"""ด่าตีนกาอิทึกดิไม่มีใครว่าหรอก 55555555555555555555555555555555""", False),
            # Extracted from https://twitter.com/#!/_mperla/status/189564203332415488
            (ur"""diz : foi bom ter te visto , vou sentir saudades :/ AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA qero morrer ))))))):""", False),
            # Extracted from https://twitter.com/#!/AleBrausin/status/189535447188385792
            (ur"""@LauraAyalaS AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA♥""", False),
            # Extracted from https://twitter.com/#!/fcLRDSpe/status/189500470891515905
            (ur"""[AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA] Q ORGULHO, Q ORGULHO MEU DEUS [AAAAAAAAAAAA]""", False),
            # Extracted from https://twitter.com/#!/Maaria_Laaura/status/189495739712417792
            (ur"""FATO: podem ter 5678765434567898765434567876543456787654 pessoas online no meu tumblr, mais nenhuma delas... http://t.co/w9fjrWn9""", False),
            # Extracted from https://twitter.com/#!/YoDrupi/status/189493424456613890
            (ur"""AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA Esto no puede estar pasando, no otra vez u_u""", False),
            # Extracted from https://twitter.com/#!/raichanxd/status/189389693589258241
            (ur"""[HD] 120409 MBC K-Pop special - SM Town Live in Tokyo (SJ cut) magnet:?xt=urn:btih:AABF5E400DCD21A3898889DC12A67CFB71E5A0A7""", False),
            # Extracted from https://twitter.com/#!/liviasi__/status/189488613568950273
            (ur"""@laurabacaxi AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA PALPITACAO NO CORACAAAAAAAAAO""", False),
            # Extracted from https://twitter.com/#!/ob_talal/status/189475556725760001
            (ur"""أحلى فيديو 
 
http://184.105.234.78/d3/97/d397213b67dcca421165cb5fef885dc9/ba64807/wmv_d397_w_1.3gp?c=165544791&u=705416530&s=BMCTOC&z=1108""", False),

            # so the spam fight has begun
            # Extracted from https://twitter.com/#!/dread55rancorou/status/191368915883012097
            (ur"""161429e21aa120cf4455fd7db285280d ... shaved teen pussy close up, young teen http://t.co/TN388cio""", False),
            ]
    for i in filter_tests_strings:
        if filter_tweet_text(i[0]) != i[1]:
            print("Test failed:\n\t \"%s\" should %smatch!"%(i[0], ("" if i[1] else "not ")))
            return False

    return True

# Alternative implementations
def process_json_line_prefilter_2(jline):
    if jline:  # filter out keep-alive new lines
        text = str(jline)
        if simplematcher.search(text):
            #print(".", end="")
            tweet = json.loads(text)
            if 'user' in tweet and 'screen_name' in tweet['user'] \
                    and 'text' in tweet:
                #if filter_tweet(tweet):
                if filter_tweet_text(tweet['text']):
                    print("Matched tweet!")
                    print(tweet['text'])
                    #print(json.dumps(tweet, indent=4))
                    #retweet(tweet['id_str'])

def process_json_line_load_only(jline):
    if jline:  # filter out keep-alive new lines
        text = str(jline)
        tweet = json.loads(text)
        if 'user' in tweet and 'screen_name' in tweet['user'] \
                and 'text' in tweet:
            pass

def process_json_line_naive(jline):
    if jline:  # filter out keep-alive new lines
        text = str(jline)
        tweet = json.loads(text)
        if 'user' in tweet and 'screen_name' in tweet['user'] \
                and 'text' in tweet:
            # we could be (much?) faster by filtering before loading json
            if filter_tweet_text(tweet['text']):
                print("Matched tweet!")
                print(tweet['text'])
                #retweet(tweet['id_str'])

def test_processing_speed():
    # load it all in RAM
    testdata = cStringIO.StringIO(open("json_test_file.txt", "r").read())
    # test multiple implementations
    for testfunc in (process_json_line_load_only,process_json_line,process_json_line_prefilter_2,):
        testdata.seek(0)
        t1 = time.clock()
        for line in testdata:
            testfunc(line)
        t2 = time.clock()
        print("Test with function %s took %f seconds"%(testfunc.__name__, t2 - t1))
    testdata.close()
    return True


def test_running_loop():
    def forevertest(func):
        def wrap():
            if not hasattr(func, "stop"):
                func.stop = True
                func()
            else:
                raise KeyboardInterrupt() # break forever run
        return wrap

    @forevertest
    def _test1():
        print("Empty run")
    @forevertest
    def _test2():
        import socket
        raise socket.error("Can't connect to the testing area. Running in circles")
    @forevertest
    def _test3():
        raise MemoryError("memory bug")
    @forevertest
    def _test4():
        raise BaseException()
# TODO: write a function to measure backoff time.
# TODO: write another function to see if backoff time is correctly reset after 10min of correct run
#    def _test5():
#        """
#        This test should measure backoff time
#        """

    print("Testing auto-restart. You will see backtraces")
    for testfunc in (_test1, _test2, _test3, _test4):
        run_forever(testfunc)()
    print("End of backtrace testing")
    return True


def test_entropy():
    teststrings = [
            ("Hello you 68b329da9893e34099c7d8ad5cb9c940", True),
            ("adc83b19e793491b1c6ea0fd8b46cd9f32e592fc", True),
            ("01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b", True),
            ("be688838ca8686e5c90689bf2ab585cef1137c999b48c70b92f67a5c34dc15697b5d11c982ed6d71be1e1e7f7b4e0733884aa97c3f7a339a8ed03577cf74be09", True),
            ("I'm so happy !!! bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbaa", False),
            ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", False),
            ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbab", False),
            ]
    for s in teststrings:
        if filter_tweet_entropy(s[0]) != s[1]:
            print("String %s failed the entropy test. Should have returned %s"%(s[0], s[1]))
            return False
    return True

def run_tests():
    for test in (test_filter,test_processing_speed,test_running_loop,test_entropy,):
        if not test():
            print("Stopping\n")
            return
    print("Every test ran successfully")


if __name__ == '__main__':
    run_tests()

