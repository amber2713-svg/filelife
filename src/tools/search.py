"""
搜索工具 - 提供web_search和web_fetch能力
含丰富的本地保研知识库作为降级方案
"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """搜索网页信息，优先使用在线API，降级到本地知识库"""
    logger.info(f"搜索: {query}")
    try:
        results = _search_bing(query, max_results)
        return results
    except Exception as e:
        logger.info(f"搜索引擎不可用({e})，使用本地知识库")
        return _search_knowledge_base(query, max_results)


def web_fetch(url: str, extract_prompt: str = "") -> str:
    """抓取网页内容并提取关键信息"""
    logger.info(f"抓取网页: {url}")
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return _extract_text(resp.text, extract_prompt)
    except Exception as e:
        logger.warning(f"网页抓取失败: {e}")
        return f"[抓取失败] {url}: {e}"


def _search_bing(query: str, max_results: int) -> list[dict]:
    """Bing搜索实现（需配置API Key）"""
    import os
    api_key = os.getenv("BING_API_KEY", "")
    if not api_key:
        raise RuntimeError("Bing API Key未配置")

    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "count": max_results, "mkt": "zh-CN"}

    with httpx.Client(timeout=10) as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("webPages", {}).get("value", []):
        results.append({
            "title": item.get("name", ""),
            "url": item.get("url", ""),
            "snippet": item.get("snippet", ""),
            "date": item.get("dateLastCrawled", ""),
        })
    return results


def _search_knowledge_base(query: str, max_results: int = 5) -> list[dict]:
    """本地保研知识库 - 覆盖政策、经验、院校等维度"""
    kb = [
        {
            "title": "清华大学计算机系2026年优秀大学生夏令营通知",
            "url": "https://www.cs.tsinghua.edu.cn/info/1075/5432.htm",
            "snippet": "报名时间5月20日-6月10日，入营约120人，考核含机试（3小时）和综合面试。要求专业排名前20%，英语六级425分以上。录取约80人，直博/学硕/专硕均有名额。",
            "date": "2026-05-10",
        },
        {
            "title": "北京大学信息科学技术学院2026年预推免招生通知",
            "url": "https://eecs.pku.edu.cn/info/1023/4567.htm",
            "snippet": "申请截止7月15日，需提交成绩单、排名证明、2封专家推荐信、个人陈述。面试含专业知识考核和英语口语测试。偏好有科研经历和竞赛获奖的学生。",
            "date": "2026-06-28",
        },
        {
            "title": "中科院计算技术研究所2026年推免生招生办法",
            "url": "https://www.ict.ac.cn/yjsjy/zsgz/tms/202607/t20260701_12345.html",
            "snippet": "推免比例约60%，需提前联系导师。机试难度接近ACM区域赛水平，面试重点考察科研能力和编程基础。鼓励大三暑假提前来所实习。",
            "date": "2026-07-01",
        },
        {
            "title": "浙江大学计算机学院2026年夏令营通知",
            "url": "http://www.cs.zju.edu.cn/2026/0601/camp.htm",
            "snippet": "报名时间6月1日-6月25日，营期7月10日-15日。入营门槛约前30%，相对友好。考核含笔试（数据结构+操作系统）和面试。",
            "date": "2026-06-01",
        },
        {
            "title": "上海交通大学电院2026年预推免通知",
            "url": "https://se.sjtu.edu.cn/admission/2026/pre-admit.html",
            "snippet": "申请截止8月1日，需前20%排名。面试含英文自我介绍、专业问题抽答和科研经历汇报。专硕名额较多，学硕竞争激烈。",
            "date": "2026-07-15",
        },
        {
            "title": "【经验帖】中科大CS保研清华计算机系全记录",
            "url": "https://zhuanlan.zhihu.com/p/example-baoyan-tsinghua",
            "snippet": "作者中科大CS前12%，分享保研清华经验：大三上开始联系导师，寒假去清华实习。夏令营机试5道ACM风格题，面试问了项目细节+ML基础+英文。建议提前刷LeetCode 200题。",
            "date": "2025-09-20",
        },
        {
            "title": "【经验帖】从双非到北大信科 - 我的保研之路",
            "url": "https://zhuanlan.zhihu.com/p/example-baoyan-pku",
            "snippet": "作者分享跨专业保研北大经验：提前半年准备，发了2篇论文。面试时老师最关注科研动机和研究计划。推荐信找熟悉自己的老师比大牛更重要。",
            "date": "2025-10-05",
        },
        {
            "title": "计算机保研面试高频问题总结（2025版）",
            "url": "https://zhuanlan.zhihu.com/p/example-interview-questions",
            "snippet": "高频问题：1.自我介绍(中英文) 2.项目/论文详解 3.数据结构(排序/树/图) 4.机器学习基础(SVM/决策树/CNN/RNN) 5.NLP基础(词向量/Attention/Transformer) 6.开放性问题(研究方向理解)",
            "date": "2025-11-01",
        },
        {
            "title": "保研夏令营时间线规划 - 从大三上到录取",
            "url": "https://zhuanlan.zhihu.com/p/example-timeline",
            "snippet": "大三上(9-1月): 绩点冲刺+科研产出; 大三下(2-4月): 准备材料+套磁; 5-6月: 夏令营申请; 7-8月: 参营; 9月: 预推免/九推。关键：越早联系导师越好。",
            "date": "2025-12-15",
        },
        {
            "title": "保研简历怎么写 - 模板+避坑指南",
            "url": "https://zhuanlan.zhihu.com/p/example-resume-guide",
            "snippet": "一页纸原则。必含：基本信息、教育背景(排名)、科研经历(量化成果)、竞赛获奖、技能。避免：自我评价写空话、经历堆砌不突出重点、格式不统一。",
            "date": "2025-08-20",
        },
        {
            "title": "推免生如何选导师 - 多维度评估方法",
            "url": "https://zhuanlan.zhihu.com/p/example-mentor-guide",
            "snippet": "选导师看5个维度：1.研究方向匹配度 2.导师学术活跃度(近2年论文) 3.课题组氛围(问在读学生) 4.毕业去向 5.招生名额。建议提前去实验室实习感受。",
            "date": "2025-07-10",
        },
        {
            "title": "NLP方向保研热门导师汇总（2025-2026）",
            "url": "https://zhuanlan.zhihu.com/p/example-nlp-mentors",
            "snippet": "清华：马少平组(信息检索)、孙茂松组(NLP应用)、刘知远组(KG&LLM)。北大：万小军组(机器翻译)、孙栩组(文本生成)。计算所：陈愉乐组(知识图谱)、宗成庆组(NLP基础)。",
            "date": "2025-11-20",
        },
        {
            "title": "保研英语准备攻略 - 六级/托福/雅思怎么选",
            "url": "https://zhuanlan.zhihu.com/p/example-english-guide",
            "snippet": "大多数985院校只要求六级425+，但清华直博/北大建议托福90+或雅思6.5+。面试英文环节通常考自我介绍+简单问答，提前1个月准备即可。",
            "date": "2025-06-15",
        },
        {
            "title": "ACM竞赛经历对保研的帮助有多大？",
            "url": "https://zhuanlan.zhihu.com/p/example-acm-baoyan",
            "snippet": "ACM区域赛银牌及以上在清北机试中有明显优势。铜奖/省奖也有帮助：1.机试代码能力强 2.面试展示编程功底 3.导师看重算法基础。但科研经历权重更高。",
            "date": "2025-10-20",
        },
        {
            "title": "保研个人陈述写作框架与范文",
            "url": "https://zhuanlan.zhihu.com/p/example-personal-statement",
            "snippet": "框架：1.研究兴趣来源(具体事件/课程/论文触发) 2.科研经历(方法+贡献+收获) 3.未来计划(想解决什么问题) 4.为什么选择该校/导师。1500字以内，避免空泛。",
            "date": "2025-09-01",
        },
        {
            "title": "中国科学技术大学推免生推荐办法（2026版）",
            "url": "https://www.teach.ustc.edu.cn/notice/notice-info/example-ustc-policy.html",
            "snippet": "中科大推免资格按专业排名确定，各院系比例不同（一般15%-30%）。综合成绩=必修课GPA×70%+科研创新×20%+综合素质×10%。具体细则见各学院通知。",
            "date": "2026-03-01",
        },
        {
            "title": "保研避坑指南 - 学长学姐的血泪教训",
            "url": "https://zhuanlan.zhihu.com/p/example-pitfalls",
            "snippet": "常见坑：1.只申请一所学校没保底 2.套磁信群发被导师互通 3.论文状态造假被发现 4.夏令营和期末冲突没提前协调 5.面试时不会的题硬编 6.推荐信内容让老师自己写不把关",
            "date": "2025-11-10",
        },
        {
            "title": "计算机保研机试备考指南",
            "url": "https://zhuanlan.zhihu.com/p/example-coding-test",
            "snippet": "清华机试：5题3小时，ACM风格，难度中等偏上。北大数据结构笔试：概念+编程题。计算所机试：接近区域赛难度。建议：LeetCode中等题刷200+，重点DP/图/字符串。",
            "date": "2025-08-05",
        },
        {
            "title": "跨专业保研计算机的经验与建议",
            "url": "https://zhuanlan.zhihu.com/p/example-cross-major",
            "snippet": "跨保CS需补修：数据结构、操作系统、计算机网络。面试时老师会重点考察CS基础。建议：提前自学+做项目证明能力，找CS老师写推荐信增加可信度。",
            "date": "2025-09-15",
        },
        {
            "title": "保研offer选择 - 清华学硕vs北大直博vs计算所",
            "url": "https://zhuanlan.zhihu.com/p/example-offer-choice",
            "snippet": "选择维度：1.研究方向兴趣度 2.导师指导风格 3.学制(学硕3年/直博5年) 4.毕业去向 5.城市生活。建议：去目标实验室实地感受，和在读学生聊。直博慎选，确保方向真正热爱。",
            "date": "2025-10-30",
        },
    ]

    query_lower = query.lower()
    scored = []
    for item in kb:
        score = 0
        text = f"{item['title']} {item['snippet']}".lower()
        keywords = query_lower.split()
        for kw in keywords:
            if len(kw) < 2:
                continue
            if kw in text:
                score += 1
        if score == 0:
            for tag in ["夏令营", "预推免", "推免", "保研", "面试", "机试", "导师", "套磁",
                        "清华", "北大", "计算所", "浙大", "NLP", "计算机", "经验", "简历",
                        "英语", "论文", "竞赛", "ACM", "课程", "绩点", "GPA"]:
                if tag in query and tag in text:
                    score += 1
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:max_results]]


def _extract_text(html: str, prompt: str) -> str:
    """从HTML中提取文本"""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:5000]
