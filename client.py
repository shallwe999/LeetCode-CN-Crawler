# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import glob
import requests
from tqdm import tqdm

import utils

class LeetCodeClient:
    """
    LeetCode Client
    """ 
    def __init__(self, username, password, save_path, args):
        self.__username = username
        self.__password = password
        self.__save_path = save_path
        self.__debug_mode = args.debug
        self.__force_mode = args.force

        self.__client = requests.session()
        self.__client.encoding = "utf-8"
        self.__problems_info = []  # { qid, title, url, grasped, 
                                   #   translated_title(if grasped) }
        self.__account_name = None
        self.__signed_in = False
        self.__book_name = ""

        self.__login_retry_times = 3  # >= 1
        self.__submission_retry_times = 20  # >= 3

        self.__leetcode_url = "https://leetcode-cn.com/"
        self.__query_url = self.__leetcode_url + "graphql/"
        self.__sign_in_url = self.__leetcode_url + "accounts/login/"
        self.__problem_list_url = self.__leetcode_url + "api/problems/"
        self.__problem_url = self.__leetcode_url + "problems/"
        self.__submissions_url = self.__leetcode_url + "submissions/"

        self.__valid_book_list = ["algorithms", "database", "shell", "concurrency", "lcci", "lcof"]


    def login(self, retry_time_interval=5.0):
        """
        Web Client Login
        """
        retry_times = self.__login_retry_times
        
        while retry_times > 0:
            try:
                # Login
                login_data = {"login": self.__username, "password": self.__password}            
                login_response = self.__client.post(self.__sign_in_url, data=login_data, headers=dict(Referer=self.__sign_in_url))

                # Get account name, check if signed in.
                # If not signed in, account name will not be received.
                account_name_headers = self.__postHTTPJSONHeader(Referer=self.__query_url)

                json_query = "query userStatus {\n  userStatus {\n    userSlug\n  }\n}\n"
                account_name_param = self.__postHTTPJSONParam("userStatus", {}, json_query)

                param_json = json.dumps(account_name_param).encode("utf-8")
                account_name_response = self.__client.post(self.__query_url, data=param_json, headers=account_name_headers)
                self.__account_name = account_name_response.json()["data"]["userStatus"]["userSlug"]
                self.__signed_in = (self.__account_name != None)

                # Check results
                if not login_response.ok:
                    print(" >> Login failed. Not OK response from server. Retry in {:.1f} seconds...")
                    retry_times = retry_times - 1
                    time.sleep(retry_time_interval)
                elif not self.__signed_in:
                    print(" >> Login failed. Wrong password.")
                    return False
                else:
                    print(" >> Login successfully.\n >> Welcome, {:s}!".format(self.__account_name))
                    return True

            except:
                print(" >> Login failed. Connection failed. Retry in {:.1f} seconds...".format(retry_time_interval))
                retry_times = retry_times - 1
                time.sleep(retry_time_interval)
        return False


    def graspAllProblems(self, book_name):
        if not self.__signed_in:
            print(" >> Not signed in yet. Please login first.")
            return

        if book_name == "all":  # grasp all the books in the list
            print(" >> All books will be grasped.")
            for book in self.__valid_book_list:
                self.graspAllProblems(book)
            return
        elif book_name in self.__valid_book_list:
            self.__book_name = book_name
        else:
            print(" >> Grasp failed. Book name not found.")
            return

        self.__getProblemsList()
        length = len(self.__problems_info)
        if length == 0:
            print(" >> No AC submissions found.")
            print(" >> Grasp BOOK [{:s}] finished.".format(self.__book_name))
            return

        print(" >> Start grasping.")
        if self.__debug_mode:  # not use tqdm
            idx = 1
            for problem_info in self.__problems_info:
                # Skip grasping this problem if found
                if not self.__force_mode:
                    file_path = os.path.join(self.__save_path, self.__book_name, problem_info["qid"])
                    check_file_paths = glob.glob("{:s} - *".format(file_path))
                    check_existed = len(check_file_paths)
                    if check_existed != 0:
                        # get translated_title and save to problem info
                        title_start_idx = check_file_paths[0].find("{:s} - ".format(file_path)) + len(file_path) + 3
                        problem_info["translated_title"] = check_file_paths[0][title_start_idx:]
                        problem_info["grasped"] = True
                        print(" >> Problem [{:s}] has been grasped, skip it.".format(problem_info["title"]))
                        continue

                print(" >> Processing problem [{:s} - {:s}]. ({:d}/{:d})"
                        .format(problem_info["qid"], problem_info["title"], idx, length))
                idx = idx + 1

                status_ok = self.__getLatestACSubmission(problem_info)
                if not status_ok:
                    print(" >> Problem [{:s}] grasp failed, skip it.".format(problem_info["title"]))
                    continue
                self.__getProblemDiscription(problem_info)
                problem_info["grasped"] = True
        else:
            tqdm_desc = "BOOK {:s}".format(self.__book_name)
            with tqdm(total=len(self.__problems_info), ncols=80, desc=tqdm_desc, 
                    bar_format=" >> {l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}{postfix}]") as pbar:
                for problem_info in self.__problems_info:
                    # Skip grasping this problem if found
                    if not self.__force_mode:
                        file_path = os.path.join(self.__save_path, self.__book_name, problem_info["qid"])
                        check_file_paths = glob.glob("{:s} - *".format(file_path))
                        check_existed = len(check_file_paths)
                        if check_existed != 0:
                            # get translated_title and save to problem info
                            title_start_idx = check_file_paths[0].find("{:s} - ".format(file_path)) + len(file_path) + 3
                            problem_info["translated_title"] = check_file_paths[0][title_start_idx:]
                            problem_info["grasped"] = True
                            pbar.update(1)
                            continue

                    status_ok = self.__getLatestACSubmission(problem_info)
                    if not status_ok:
                        print(" >> Problem [{:s}] grasp failed, skip it.".format(problem_info["title"]))
                        pbar.update(1)
                        continue
                    self.__getProblemDiscription(problem_info)
                    problem_info["grasped"] = True
                    pbar.update(1)

        self.__generateListFile(book_name)

        print(" >> Grasp BOOK [{:s}] finished.".format(self.__book_name))


    def __getProblemsList(self):
        html = self.__client.get(self.__problem_list_url + self.__book_name + "/", verify=False)
        html = json.loads(html.text)
        problems_origin = html["stat_status_pairs"]

        self.__problems_info = []  # reset
        for problem in problems_origin:
            if problem["status"] == "ac":  # only collect AC problems
                self.__problems_info.append({"qid": problem["stat"]["frontend_question_id"],
                                             "title": problem["stat"]["question__title"],
                                             "url": problem["stat"]["question__title_slug"],
                                             "grasped": False})

        print(" >> Get BOOK [{:s}] list successfully. Collect {:d} problems.".format(self.__book_name, len(self.__problems_info)))


    def __getProblemDiscription(self, problem_info):
        this_problem_url = self.__problem_url + problem_info["url"] + "/"
        headers = self.__postHTTPJSONHeader(Referer=this_problem_url)

        json_query = "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    categoryTitle\n    title\n    titleSlug\n    translatedTitle\n    translatedContent\n    difficulty\n    status\n  }\n}\n"
        if self.__debug_mode:  # grasp all the content in debug mode
            json_query = "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    categoryTitle\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    langToValidPlayground\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    envInfo\n    book {\n      id\n      bookName\n      pressName\n      source\n      shortDescription\n      fullDescription\n      bookImgUrl\n      pressImgUrl\n      productUrl\n      __typename\n    }\n    isSubscribed\n    isDailyQuestion\n    dailyRecordStatus\n    editorType\n    ugcQuestionId\n    style\n    exampleTestcases\n    __typename\n  }\n}\n"
        param = self.__postHTTPJSONParam("questionData", {"titleSlug": problem_info["url"]}, json_query)

        param_json = json.dumps(param).encode("utf-8")
        response = self.__client.post(self.__query_url, data=param_json, headers=headers)
        problem_details = response.json()["data"]["question"]
        difficulty = problem_details["difficulty"]

        translated_title = problem_details["translatedTitle"]
        problem_info["translated_title"] = translated_title  # save to problem info
        problem_name = "{:s} - {:s}".format(problem_info["qid"], translated_title)
        file_path = os.path.join(self.__save_path, self.__book_name, problem_name)
        utils.saveProblemFile(file_path, translated_title, problem_name, difficulty, problem_details["translatedContent"])

        if self.__debug_mode:
            print(" >> Get problem [{:s}] discription.".format(problem_info["title"]))
        return True


    def __getLatestACSubmission(self, problem_info):
        this_problem_url = self.__problem_url + problem_info["url"] + "submissions/"
        headers = self.__postHTTPJSONHeader(Referer=this_problem_url)

        json_query = "query submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $markedOnly: Boolean, $lang: String) {\n  submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug, markedOnly: $markedOnly, lang: $lang) {\n    lastKey\n    submissions {\n      id\n      statusDisplay\n      lang\n      timestamp\n      url\n    }\n  }\n}\n"
        if self.__debug_mode:  # grasp all the content in debug mode
            json_query = "query submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $markedOnly: Boolean, $lang: String) {\n  submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug, markedOnly: $markedOnly, lang: $lang) {\n    lastKey\n    hasNext\n    submissions {\n      id\n      statusDisplay\n      lang\n      runtime\n      timestamp\n      url\n      isPending\n      memory\n      submissionComment {\n        comment\n        flagType\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
        param = self.__postHTTPJSONParam("submissions", {"offset":0, "limit":50, "lastKey":"null", "questionSlug": problem_info["url"]}, json_query)

        param_json = json.dumps(param).encode("utf-8")
        response = self.__client.post(self.__query_url, data=param_json, headers=headers)
        submission_details = response.json()["data"]["submissionList"]["submissions"]

        submission_idx = -1
        for idx in range(len(submission_details)):  # default have time order
            if submission_details[idx]["statusDisplay"] == "Accepted":  # AC
                submission_idx = idx
                break
        if submission_idx == -1:
            print(" >> No accepted soulution found. Skip this problem")
            return False


        # get latest submission id, then we can get the code
        lang = submission_details[submission_idx]["lang"]
        latest_submission_id = submission_details[submission_idx]["id"]
        latest_submission_url = submission_details[submission_idx]["url"][1:]  # remove '/'
        latest_submission_url = self.__leetcode_url + latest_submission_url
        headers = self.__postHTTPJSONHeader(Referer=latest_submission_url)

        json_query = "query mySubmissionDetail($id: ID!) {\n  submissionDetail(submissionId: $id) {\n    id\n    code\n    lang\n    question {\n      translatedTitle\n    }\n  }\n}\n"
        if self.__debug_mode:  # grasp all the content in debug mode
            json_query = "query mySubmissionDetail($id: ID!) {\n  submissionDetail(submissionId: $id) {\n    id\n    code\n    runtime\n    memory\n    rawMemory\n    statusDisplay\n    timestamp\n    lang\n    passedTestCaseCnt\n    totalTestCaseCnt\n    sourceUrl\n    question {\n      titleSlug\n      title\n      translatedTitle\n      questionId\n      __typename\n    }\n    ... on GeneralSubmissionNode {\n      outputDetail {\n        codeOutput\n        expectedOutput\n        input\n        compileError\n        runtimeError\n        lastTestcase\n        __typename\n      }\n      __typename\n    }\n    submissionComment {\n      comment\n      flagType\n      __typename\n    }\n    __typename\n  }\n}\n"
        param = self.__postHTTPJSONParam("mySubmissionDetail", {"id": latest_submission_id}, json_query)

        # Post this query may be failed, so it will retry
        retry_times = self.__submission_retry_times
        while retry_times > 0:
            param_json = json.dumps(param).encode("utf-8")
            response = self.__client.post(self.__query_url, data=param_json, headers=headers)
            code_details = response.json()["data"]["submissionDetail"]
            if code_details != None:
                break
            else:
                if retry_times == self.__submission_retry_times - 2:  # only hint once
                    print(" >> Get submission error. Retrying...")
                retry_times = retry_times - 1
                time.sleep(3.0)  # wait and retry

        if code_details == None:
            print(" >> Get submission error.")
            return False

        file_name = code_details["question"]["translatedTitle"]
        problem_name = "{:s} - {:s}".format(problem_info["qid"], file_name)
        file_path = os.path.join(self.__save_path, self.__book_name, problem_name)
        code_content = code_details["code"]
        utils.saveCodeFile(file_path, file_name, lang, code_details["code"])

        if self.__debug_mode:
            print(" >> Get problem [{:s}] latest AC submission.".format(problem_info["title"]))
        return True


    def __generateListFile(self, book_name):
        file_path = os.path.join(self.__save_path, book_name)
        file_name = "题目与题解汇总"

        valid_problems_info = []
        for problem_info in self.__problems_info:
            if problem_info["grasped"]:
                valid_problems_info.append(problem_info)

        utils.saveListFile(file_path, file_name, book_name, valid_problems_info)


    def __postHTTPJSONHeader(self, Referer):
        return {
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Referer": Referer
        }
    
    
    def __postHTTPJSONParam(self, operationName, variables, query):
        return {
            "operationName": operationName,
            "variables": variables,
            "query": query
        }

