"""
模板工具 - 提供邮件、简历等模板渲染能力
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

TEMPLATES = {
    "mentor_contact_email": {
        "name": "导师套磁邮件模板",
        "description": "首次联系目标导师的邮件模板",
        "template": """主题：{major}专业推免咨询 - {university}{name}

尊敬的{mentor_name}教授：

您好！

我是{university}{major}专业{grade}的本科生{name}，{rank_info}。
我对您在{research_direction}方向的研究非常感兴趣，特别是您近期发表的论文《{paper_title}》中关于{paper_highlight}的工作，与我之前的科研经历有很好的衔接。

我在本科期间的科研经历如下：
{research_experience}

基于以上背景，我非常希望能有机会加入您的课题组攻读{degree_type}研究生。
随信附上我的简历和成绩单，供您参考。

如果您方便的话，希望能有机会与您面谈或线上交流。
感谢您在百忙之中阅读这封邮件，期待您的回复！

此致
敬礼

{name}
{university}{major}
邮箱：{email}
电话：{phone}
""",
        "variables": [
            "name", "university", "major", "grade", "rank_info",
            "mentor_name", "research_direction", "paper_title",
            "paper_highlight", "research_experience", "degree_type",
            "email", "phone",
        ],
    },
    "follow_up_email": {
        "name": "套磁跟进邮件模板",
        "description": "首次联系后2周无回复的跟进邮件",
        "template": """主题：Re: {major}专业推免咨询 - {university}{name}

尊敬的{mentor_name}教授：

您好！冒昧再次打扰。

我于{first_contact_date}给您发过一封关于推免咨询的邮件，不知您是否方便查阅。
我对您的{research_direction}方向的研究热情不减，近期又阅读了您课题组的新作《{new_paper}》，更加坚定了希望加入您课题组的想法。

如果目前课题组还有招生名额，恳请您能给予回复。
如不便回复也完全理解，感谢您的时间！

此致
敬礼

{name}
""",
        "variables": [
            "name", "university", "major", "mentor_name",
            "first_contact_date", "research_direction", "new_paper",
        ],
    },
    "recommendation_request": {
        "name": "推荐信请求邮件模板",
        "description": "向老师请求撰写推荐信的邮件",
        "template": """主题：恳请{teacher_name}老师撰写推免推荐信 - {name}

尊敬的{teacher_name}老师：

您好！

我是{university}{major}专业{grade}的{name}，曾选修您的{course_name}课程并取得了{grade_in_course}的成绩。

目前我正在准备保研申请，目标院校包括{target_schools}。
鉴于您对我的学习情况比较了解，冒昧恳请您能作为我的推荐人，为我撰写一封推荐信。

为减轻您的工作量，我已准备了以下材料供您参考：
1. 个人简历
2. 个人陈述草稿
3. 目标院校及专业列表
4. 成绩单

如果您同意，我可以将以上材料发送给您，并在您方便时当面沟通。
推荐信的截止日期为{deadline}。

非常感谢您在百忙中考虑我的请求！

此致
敬礼

{name}
{email}
""",
        "variables": [
            "name", "university", "major", "grade",
            "teacher_name", "course_name", "grade_in_course",
            "target_schools", "deadline", "email",
        ],
    },
    "self_introduction_en": {
        "name": "英文自我介绍模板",
        "description": "面试用3分钟英文自我介绍",
        "template": """Good morning/afternoon, professors.

My name is {name}, and I am a senior student majoring in {major} at {university}.
It is my great honor to be here for this interview.

During my undergraduate studies, I have maintained a GPA of {gpa} out of {gpa_scale},
ranking in the top {rank}% of my department.
I have developed a strong interest in {research_interest},
which motivated me to engage in research projects during my junior year.

In my research experience, I worked on {research_topic},
where I was responsible for {responsibilities}.
This experience led to {achievements},
and it deepened my understanding of {key_learning}.

I am particularly drawn to your program because of {reason}.
I believe my background in {background} and my passion for {passion}
make me a strong candidate for your graduate program.

Thank you for your time and consideration.
I am happy to answer any questions you may have.
""",
        "variables": [
            "name", "major", "university", "gpa", "gpa_scale", "rank",
            "research_interest", "research_topic", "responsibilities",
            "achievements", "key_learning", "reason", "background", "passion",
        ],
    },
}


def template_render(template_name: str, variables: dict[str, str]) -> str:
    """渲染模板"""
    if template_name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        return f"[错误] 模板'{template_name}'不存在。可用模板: {available}"

    tmpl = TEMPLATES[template_name]
    content = tmpl["template"]

    for var in tmpl["variables"]:
        placeholder = "{" + var + "}"
        value = variables.get(var, f"[待填写:{var}]")
        content = content.replace(placeholder, str(value))

    return content


def template_list() -> list[dict]:
    """列出所有可用模板"""
    return [
        {"name": key, "description": value["description"]}
        for key, value in TEMPLATES.items()
    ]
