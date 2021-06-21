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


def saveProblemFile(file_path, file_name, file_title, difficulty, content):
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    with open(os.path.join(file_path, file_name+".html"), "w", encoding="utf-8") as f:
        f.write("<h2>{:s}</h2>".format(file_title))  # write problem title

        f.write("<h4>{:s} {:s}</h4>".format(
                DIFFICULTY_TRANSFORM["Default"], DIFFICULTY_TRANSFORM[difficulty]))  # write difficulty

        f.write(content)


def saveCodeFile(file_path, file_name, lang, content):
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_format = LANG_FILE_FORMAT[LANG_SLUG_TRANSFORM[lang]]
    with open(os.path.join(file_path, file_name+file_format), "w", encoding="utf-8") as f:
        f.write(content)

