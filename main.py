# -*- coding: utf-8 -*-

import os
import sys
import argparse
import requests

from client import LeetCodeClient


def parseArgs():
    parser = argparse.ArgumentParser(description=" === LeetCode CN Crawler ===",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-b", "--book", type=str, default="all", 
                                        help="select the book list as follows \n" + 
                                             "[ all(default) -- 所有(默认) , \n" + 
                                             "  algorithms   -- 算法 , \n" + 
                                             "  database     -- 数据库 , \n" + 
                                             "  shell        -- Shell , \n" + 
                                             "  concurrency  -- 多线程 , \n" + 
                                             "  lcci         -- 程序员面试金典 , \n" + 
                                             "  lcof         -- 剑指Offer ]")
    parser.add_argument("-d", "--debug", default=False, action="store_true",
                        help="debug mode, querying the unecessary content, and may be slower")
    parser.add_argument("-f", "--force", default=False, action="store_true",
                        help="force mode, force cover grasped problems and submissions")
    args = parser.parse_args()
    return args


def main():
    args = parseArgs()

    username = input(" >> Please input your username: ")
    password = input(" >> Please input your password: ")
    # Or, you can write your username and password here, and comment above.
    # Not recommanded. It's not safe.
    # username = "your_username"
    # password = "your_password"

    requests.packages.urllib3.disable_warnings()

    save_path = os.path.join(os.getcwd(), "problems")

    lc_client = LeetCodeClient(username, password, save_path, args=args)

    ret = lc_client.login(retry_time_interval=5.0)
    if not ret:
        return

    lc_client.graspAllProblems(args.book)




if __name__ == "__main__":
    main()
    print(" >> Program finished.")

