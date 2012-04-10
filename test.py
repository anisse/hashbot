#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from hashbot import filter_tweet

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
            ("SHA1:AB840554A8158026C5788C5312ADF030B51CFFAC ", True),
            ]
    for i in filter_tests_strings:
        if filter_tweet(i[0]) != i[1]:
            print("Test failed:\n\t \"%s\" should %smatch!"%(i[0], ("" if i[1] else "not ")))
            return False

    return True


def run_tests():
    for test in (test_filter,):
        if not test():
            print("Stopping\n")
            return
    print("Every test ran successfully")


if __name__ == '__main__':
    run_tests()

