# -*- coding: utf-8 -*-
import re
from cn2an import cn2an
from typing import Dict, List, Optional

# 详细词根字典（包含二级分类）
KEYWORD_ROOTS = {
    "course": {
        "languages": ["java", "python", "c#", "php", "前端", "全栈"],
        "tech_stack": ["web开发", "小程序", "app开发", "数据库", "云计算"],
        "course_type": ["就业班", "实战班", "周末班", "网课", "全日制"]
    },
    "cost": {
        "payment": ["学费", "价格", "费用", "多少钱", "贵吗"],
        "financial": ["分期", "贷款", "助学", "首付", "月供"],
        "discount": ["优惠", "减免", "补贴", "奖学金", "立减"]
    },
    "qualification": {
        "education": ["学历", "中专", "高中", "初中", "毕业"],
        "experience": ["零基础", "转行", "小白", "入门", "无经验"],
        "age": ["年龄", "多大", "岁数", "限制"]
    },
    "geo": {
        "cities": ["北京", "上海", "广州", "深圳", "成都", "武汉", "杭州", "南京", "郑州", "西安"],
        "suffix": ["培训", "机构", "学校", "基地", "面授"]
    },
    "competitor": {
        "brands": ["达内", "北大青鸟", "传智", "黑马", "千锋", "蜗牛", "尚硅谷"],
        "comparison": ["哪家好", "对比", "区别", "怎么样", "靠谱吗"]
    },
    "negative": {
        "fraud": ["骗局", "诈骗", "跑路", "坑人", "黑心"],
        "complaint": ["投诉", "维权", "退费难", "虚假宣传", "差评"],
        "doubt": ["靠谱吗", "后悔", "没用", "被骗", "太坑"]
    },
    "age_limit": 35
}

def build_keyword_regex(
    keyword_roots: Dict[str, List[str]] = {},
    categories: Optional[List[str]] = None,
    special_regex: List[str] = [],
    word_boundary: bool = False,
    escape: bool = True,
    flags: re.RegexFlag = re.IGNORECASE
) -> re.Pattern:
    """构建正则表达式模式"""
    selected_categories = categories or keyword_roots.keys()
    patterns = []
    for category in selected_categories:
        terms = keyword_roots.get(category, [])
        processed_terms = [re.escape(term) if escape else term for term in terms]
        if word_boundary:
            processed_terms = [rf"\b{term}\b" for term in processed_terms]
        if processed_terms:
            patterns.append(r"(?:{})".format("|".join(processed_terms)))
    if not patterns:
        return re.compile(r'(?!a)a')
    full_pattern = "|".join(filter(None, ["|".join(patterns), "|".join(special_regex)]))
    if len(full_pattern) > 1:
        full_pattern = f"(?:{full_pattern})"
    return re.compile(full_pattern, flags=flags)

def build_regex_patterns():
    """构建所有正则表达式模式，包含二级分类"""
    patterns = {}
    
    # 为每个主类及其子类构建正则
    for main_category, sub_dict in KEYWORD_ROOTS.items():
        if main_category == "age_limit":
            continue
        if isinstance(sub_dict, dict):
            # 主类正则：合并所有子类关键词
            all_terms = []
            for sub_terms in sub_dict.values():
                all_terms.extend(sub_terms)
            patterns[main_category] = build_keyword_regex({main_category: all_terms})
            # 子类正则
            for sub_name, terms in sub_dict.items():
                sub_key = f"{main_category}.{sub_name}"
                patterns[sub_key] = build_keyword_regex({sub_name: terms})
        else:
            # 处理非字典结构（如negative）
            patterns[main_category] = build_keyword_regex({main_category: sub_dict})
    
    # 地域类特殊处理（城市+后缀组合）
    geo_terms = [
        rf"{city}{suffix}" 
        for city in KEYWORD_ROOTS["geo"]["cities"] 
        for suffix in KEYWORD_ROOTS["geo"]["suffix"]
    ]
    patterns["geo"] = build_keyword_regex(special_regex=geo_terms)
    
    # 年龄检测正则
    age_pattern = r"""(?xi)
    (?:年[龄纪]|岁)[\s：:]*(?:约|大概)?(\d{1,2}|[零一二两三四五六七八九十廿卅]+)|
    (\d{1,2}|[零一二两三四五六七八九十廿卅]+)[\s：:]*(?:约|大概)?(?:个?[周岁]|岁)
    """
    patterns["age_check"] = re.compile(age_pattern)
    
    return patterns

def parse_age(match):
    """解析年龄匹配结果"""
    groups = match.groups()
    for g in groups:
        if g and g.isdigit():
            return int(g)
        elif g:
            return cn2an(g, mode="smart")
    return 0

def classify_keyword(keyword: str, patterns: Dict[str, re.Pattern]) -> List[str]:
    """多级分类关键词"""
    # 否定词优先
    if patterns["negative"].search(keyword):
        return ["negative"]
    
    # 年龄检查
    age_match = patterns["age_check"].search(keyword)
    if age_match:
        age = parse_age(age_match)
        if age > KEYWORD_ROOTS["age_limit"]:
            return ["age_limit"]
    
    # 竞品类处理
    if patterns["competitor"].search(keyword):
        return ["competitor"]
    
    classifications = []
    matched_parents = set()
    
    # 检查所有可能的子类
    for pattern_key in patterns:
        if '.' in pattern_key and patterns[pattern_key].search(keyword):
            classifications.append(pattern_key)
            main_cat = pattern_key.split('.')[0]
            matched_parents.add(main_cat)
    
    # 检查未被子类覆盖的主类
    main_categories = ["geo", "course", "cost", "qualification"]
    for main_cat in main_categories:
        if main_cat not in matched_parents and patterns[main_cat].search(keyword):
            classifications.append(main_cat)
    
    # 弱意向处理
    if not classifications and any(q in keyword for q in ["好吗", "难吗", "前景"]):
        classifications.append("qualification")
    
    return classifications if classifications else ["other"]

# 测试用例
test_keywords = [
    "Java编程就业班",
    "北京web开发培训",
    "学费分期付款",
    "高中毕业学Python",
    "达内对比黑马",
    "三十五岁学前端",
    "大数据开发课程"
]

patterns = build_regex_patterns()
for kw in test_keywords:
    print(f"关键词：{kw}")
    print(f"分类结果：{classify_keyword(kw, patterns)}")
    print("-" * 50)
