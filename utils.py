# -*- coding: utf-8 -*-

import os

LANG_SLUG_TRANSFORM = {
    "cpp": "C++", "java": "JAVA", "python": "Python", "python3": "Python3",
    "c": "C", "csharp": "C#", "javascript": "JavaScript", "ruby": "Ruby",
    "swift": "Swift", "golang": "Go", "scala": "Scala", "kotlin": "Kotlin",
    "rust": "Rust", "php": "PHP", "typescript": "TypeScript",
    "racket": "Racket", "mysql": "MySQL"
}

LANG_FILE_FORMAT = {
    "C++": ".cpp", "Python3": ".py", "Python": ".py", "MySQL": ".sql",
    "Go": ".go", "Java": ".java", "C": ".c", "JavaScript": ".js",
    "PHP": ".php", "C#": ".cs", "Ruby": ".rb", "Swift": ".swift",
    "Scala": ".scl", "Kotlin": ".kt", "Rust": ".rs",
    "TypeScript": ".ts", "Racket": ".rkt"
}

DIFFICULTY_TRANSFORM = {
    "Default": "<font color='#595959'>难度</font>",
    "Easy": "<font color='#5AB726'>简单</font>",
    "Medium": "<font color='#FFA119'>中等</font>",
    "Hard": "<font color='#EF4743'>困难</font>"
}

BOOK_TRANSFORM = {
    "all": "所有",
    "algorithms": "算法",
    "database": "数据库",
    "shell": "Shell",
    "concurrency": "多线程",
    "lcci": "程序员面试金典",
    "lcof": "剑指Offer",
}


def saveListFile(file_path, file_name, book_name, problems_info):
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    with open(os.path.join(file_path, file_name+".html"), "w", encoding="utf-8") as f:
        f.write(
            "<title>{:s} 题目与题解汇总</title>\n".format(BOOK_TRANSFORM[book_name])+
            "<style>\n"+
            "    .table_list table { width: 100%; margin: 15px 0; border: 0; }\n"+
            "    .table_list th { background-color: #96C7ED; color: #FFFFFF; }\n"+
            "    .table_list,.table_list th,.table_list td { font-size: 0.95em; text-align: center; padding: 4px; border-collapse: collapse; }\n"+
            "    .table_list th,.table_list td { border: 1px solid #73b4e7; border-width: 1px 0 1px 0; border: 2px inset #ffffff; }\n"+
            "    .table_list tr { border: 1px solid #ffffff; }\n"+
            "    .table_list tr:nth-child(odd){ background-color: #dcecf9; }\n"+
            "    .table_list tr:nth-child(even){ background-color: #ffffff; }\n"+
            "</style>\n"+
            "<h2 style=\"text-align:center;\">{:s} 题目与题解汇总</h2>\n".format(BOOK_TRANSFORM[book_name])+
            "<table class=table_list align=\"center\">\n"+
            "<tr>\n"+
            "    <th>题目ID</th><th>题目名称</th><th>题目链接</th><th>题解链接</th>\n"+
            "</tr>\n")
        
        sorted_problems_info = sorted(problems_info, key=lambda k: k["qid"])
        for info in sorted_problems_info:
            problem_dir = "{:s} - {:s}".format(info["qid"], info["translated_title"])
            file_list = os.listdir(os.path.join(file_path, problem_dir))  # to get code file name
            for file in file_list:
                if file[-5:] == ".html":
                    file_list.remove(file)
                    break
            problem_path = os.path.join(problem_dir, info["translated_title"]+".html")
            code_path = os.path.join(problem_dir, file_list[0])

            f.write("<tr>\n")
            f.write("<td>{:s}</td>".format(info["qid"]) +
                    "<td>{:s}</td>".format(info["translated_title"]) +
                    "<td><a href=\"{:s}\">题目</a></td>".format(problem_path) +
                    "<td><a href=\"{:s}\">题解</a></td>\n".format(code_path)
            )
            f.write("</tr>\n")

        f.write("</table>\n")


def saveProblemFile(file_path, file_name, file_title, difficulty, content):
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    with open(os.path.join(file_path, file_name+".html"), "w", encoding="utf-8") as f:
        f.write("<title>{:s}</title>\n".format(file_title))
        f.write("<h2>{:s}</h2>\n".format(file_title))  # write problem title

        f.write("<h4>{:s} {:s}</h4>\n".format(
                DIFFICULTY_TRANSFORM["Default"], DIFFICULTY_TRANSFORM[difficulty]))  # write difficulty

        f.write(content)


def saveCodeFile(file_path, file_name, lang, content):
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_format = LANG_FILE_FORMAT[LANG_SLUG_TRANSFORM[lang]]
    with open(os.path.join(file_path, file_name+file_format), "w", encoding="utf-8") as f:
        f.write(content)

