# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import requests
from tqdm import tqdm

import utils

class LeetCodeClient:
    """
    LeetCode Client
    """ 
    def __init__(self, username, password, save_path, debug_mode=False):
        self.__username = username
        self.__password = password
        self.__save_path = save_path
        self.__debug_mode = debug_mode

        self.__client = requests.session()
        self.__client.encoding = "utf-8"
        self.__problems_info = []  # {qid, title, url}
        self.__signed_in = False
        self.__book_name = ""

        self.__login_retry_times = 3  # >= 1
        self.__submission_retry_times = 20  # >= 3

        self.__leetcode_url = "https://leetcode-cn.com/"
        self.__query_url = self.__leetcode_url + "graphql/"
        self.__sign_in_url = self.__leetcode_url + "accounts/login/"
        self.__list_url = self.__leetcode_url + "list/"
        self.__problem_list_url = self.__leetcode_url + "api/problems/"
        self.__problem_url = self.__leetcode_url + "problems/"
        self.__submissions_url = self.__leetcode_url + "submissions/"

        self.__valid_book_list = ["algorithms", "database", "shell", "concurrency", "lcci", "lcof"]


    def login(self, retry_time_interval=5.0):
        """
        Web Client Login
        """
        retry_times = self.__login_retry_times
        headers = {
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Referer": self.__sign_in_url
        }
        
        while retry_times > 0:
            try:
                # Login
                login_data = {'login': self.__username, 'password': self.__password}            
                login_response = self.__client.post(self.__sign_in_url, data=login_data, headers=dict(Referer=self.__sign_in_url))

                # Test a list website to check if signed in.
                # If not signed in, the list website will be redirected to login website.
                check_signed_in_response = self.__client.get(self.__list_url, verify=False)
                idx = check_signed_in_response.url.find("login")
                signed_in = (idx == -1)

                if not login_response.ok:
                    print(" >> Login failed. Not OK response from server. Retry in {:d} seconds...")
                    retry_times = retry_times - 1
                    time.sleep(retry_time_interval)
                elif not signed_in:
                    print(" >> Login failed. Wrong password.")
                    return False
                else:
                    self.__signed_in = True
                    print(" >> Login successfully.\n >> Welcome, {:s}!".format(self.__username))
                    return True

            except:
                print(" >> Login failed. Connection failed. Retry in {:d} seconds...".format(retry_time))
                retry_times = retry_times - 1
                time.sleep(retry_time)
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
            print(" >> No AC solutions found.")
            print(" >> Grasp BOOK [{:s}] finished.".format(self.__book_name))
            return

        print(" >> Start grasping.")
        if self.__debug_mode:  # not use tqdm
            idx = 1
            for problem_info in self.__problems_info:
                print(" >> Processing problem [{:s} - {:s}]. ({:d}/{:d})"
                        .format(problem_info["qid"], problem_info["title"], idx, length))
                idx = idx + 1
                status_ok = self.__getLatestACSubmission(problem_info)
                if not status_ok:
                    print(" >> Problem [{:s}] grasp failed, skip it.".format(problem_info["title"]))
                    continue
                self.__getProblemDiscription(problem_info)
        else:
            tqdm_desc = "BOOK {:s}".format(self.__book_name)
            with tqdm(total=len(self.__problems_info), ncols=80, desc=tqdm_desc, 
                    bar_format=" >> {l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}{postfix}]") as pbar:
                for problem_info in self.__problems_info:
                    status_ok = self.__getLatestACSubmission(problem_info)
                    if not status_ok:
                        print(" >> Problem [{:s}] grasp failed, skip it.".format(problem_info["title"]))
                        continue
                    self.__getProblemDiscription(problem_info)
                    pbar.update(1)

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
                                             "url": problem["stat"]["question__title_slug"]})

        print(" >> Get BOOK [{:s}] list successfully. Collect {:d} problems.".format(self.__book_name, len(self.__problems_info)))


    def __getProblemDiscription(self, problem_info):
        this_problem_url = self.__problem_url + problem_info["url"] + "/"
        headers = {
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Referer": this_problem_url
        }
        param = {
            "operationName": "questionData",
            "variables": {"titleSlug": problem_info["url"]},
            "query": "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    categoryTitle\n    title\n    titleSlug\n    translatedTitle\n    translatedContent\n    difficulty\n    status\n  }\n}\n"
        }
        if self.__debug_mode:  # grasp all the content in debug mode
            param["query"] = "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    questionId\n    questionFrontendId\n    categoryTitle\n    boundTopicId\n    title\n    titleSlug\n    content\n    translatedTitle\n    translatedContent\n    isPaidOnly\n    difficulty\n    likes\n    dislikes\n    isLiked\n    similarQuestions\n    contributors {\n      username\n      profileUrl\n      avatarUrl\n      __typename\n    }\n    langToValidPlayground\n    topicTags {\n      name\n      slug\n      translatedName\n      __typename\n    }\n    companyTagStats\n    codeSnippets {\n      lang\n      langSlug\n      code\n      __typename\n    }\n    stats\n    hints\n    solution {\n      id\n      canSeeDetail\n      __typename\n    }\n    status\n    sampleTestCase\n    metaData\n    judgerAvailable\n    judgeType\n    mysqlSchemas\n    enableRunCode\n    envInfo\n    book {\n      id\n      bookName\n      pressName\n      source\n      shortDescription\n      fullDescription\n      bookImgUrl\n      pressImgUrl\n      productUrl\n      __typename\n    }\n    isSubscribed\n    isDailyQuestion\n    dailyRecordStatus\n    editorType\n    ugcQuestionId\n    style\n    exampleTestcases\n    __typename\n  }\n}\n"

        param_json = json.dumps(param).encode("utf-8")
        response = self.__client.post(self.__query_url, data=param_json, headers=headers)
        problem_details = response.json()["data"]["question"]
        difficulty = problem_details["difficulty"]

        file_name = problem_details["translatedTitle"]
        problem_name = "{:s} - {:s}".format(problem_info["qid"], file_name)
        file_path = os.path.join(self.__save_path, self.__book_name, problem_name)
        utils.saveProblemFile(file_path, file_name, problem_name, difficulty, problem_details["translatedContent"])

        if self.__debug_mode:
            print(" >> Get problem [{:s}] discription.".format(problem_info["title"]))
        return True


    def __getLatestACSubmission(self, problem_info):
        this_problem_url = self.__problem_url + problem_info["url"] + "submissions/"
        headers = {
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Referer": this_problem_url
        }
        param = {
            "operationName": "submissions",
            "variables": {"offset":0, "limit":40, "lastKey":"null", "questionSlug": problem_info["url"]},
            "query": "query submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $markedOnly: Boolean, $lang: String) {\n  submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug, markedOnly: $markedOnly, lang: $lang) {\n    lastKey\n    submissions {\n      id\n      statusDisplay\n      lang\n      timestamp\n      url\n    }\n  }\n}\n"
        }
        if self.__debug_mode:  # grasp all the content in debug mode
            param["query"] = "query submissions($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $markedOnly: Boolean, $lang: String) {\n  submissionList(offset: $offset, limit: $limit, lastKey: $lastKey, questionSlug: $questionSlug, markedOnly: $markedOnly, lang: $lang) {\n    lastKey\n    hasNext\n    submissions {\n      id\n      statusDisplay\n      lang\n      runtime\n      timestamp\n      url\n      isPending\n      memory\n      submissionComment {\n        comment\n        flagType\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"

        param_json = json.dumps(param).encode("utf-8")
        response = self.__client.post(self.__query_url, data=param_json, headers=headers)
        submission_details = response.json()["data"]["submissionList"]['submissions']

        submission_idx = -1
        for idx in range(len(submission_details)):  # default have time order
            if submission_details[idx]['statusDisplay'] == "Accepted":  # AC
                submission_idx = idx
                break
        if submission_idx == -1:
            print(" >> No accepted soulution found. Skip this problem")
            return False


        # get latest submission id, then we can get the code
        lang = submission_details[submission_idx]['lang']
        latest_submission_id = submission_details[submission_idx]['id']
        latest_submission_url = submission_details[submission_idx]['url'][1:]  # remove '/'
        latest_submission_url = self.__leetcode_url + latest_submission_url
        headers = {
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Referer": latest_submission_url
        }
        param = {
            "operationName": "mySubmissionDetail",
            "variables": {"id": latest_submission_id},
            "query": "query mySubmissionDetail($id: ID!) {\n  submissionDetail(submissionId: $id) {\n    id\n    code\n    lang\n    question {\n      translatedTitle\n    }\n  }\n}\n"
        }
        if self.__debug_mode:  # grasp all the content in debug mode
            param["query"] = "query mySubmissionDetail($id: ID!) {\n  submissionDetail(submissionId: $id) {\n    id\n    code\n    runtime\n    memory\n    rawMemory\n    statusDisplay\n    timestamp\n    lang\n    passedTestCaseCnt\n    totalTestCaseCnt\n    sourceUrl\n    question {\n      titleSlug\n      title\n      translatedTitle\n      questionId\n      __typename\n    }\n    ... on GeneralSubmissionNode {\n      outputDetail {\n        codeOutput\n        expectedOutput\n        input\n        compileError\n        runtimeError\n        lastTestcase\n        __typename\n      }\n      __typename\n    }\n    submissionComment {\n      comment\n      flagType\n      __typename\n    }\n    __typename\n  }\n}\n"

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



