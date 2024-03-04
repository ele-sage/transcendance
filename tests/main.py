#!/usr/bin/env python
import urllib3
import warnings
warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)

from auth import auth_tests
from friend import friend_tests, init_friends, init_friend_requests
# from user import user_tests

if __name__ == "__main__":
    # print("\n-- Auth tests --")
    # auth_tests()
    print("\n-- Friend tests --")
    init_friend_requests()
    # print("\n-- User tests --")
    # init_friends()
