# -*- coding: utf-8 -*-
import re
# 如需支持"三十五岁"的识别，可添加以下处理：
from cn2an import cn2an
from typing import Dict, List, Optional
# 详细词根字典（新增行业扩展词）
KEYWORD_ROOTS = {
    # 课程类（扩展技术栈维度）
    "course": {
        "languages": ["java", "python", "c#", "php", "前端", "全栈"],
        "tech_stack": ["web开发", "小程序", "app开发", "数据库", "云计算"],
        "course_type": ["就业班", "实战班", "周末班", "网课", "全日制"]
    },

    # # 可继续扩展的维度示例
    # "course": {
    #     "frameworks": ["spring", "django", "vue", "react"],
    #     "certification": ["软考", "华为认证", "红帽认证"]
    # },
    # "cost": {
    #     "refund": ["退费", "违约金", "试听"]
    # },

    
    # 费用类（增加金融方案维度）
    "cost": {
        "payment": ["学费", "价格", "费用", "多少钱", "贵吗"],
        "financial": ["分期", "贷款", "助学", "首付", "月供"],
        "discount": ["优惠", "减免", "补贴", "奖学金", "立减"]
    },
    
    # 资质类（扩展准入维度）
    "qualification": {
        "education": ["学历", "中专", "高中", "初中", "毕业"],
        "experience": ["零基础", "转行", "小白", "入门", "无经验"],
        "age": ["年龄", "多大", "岁数", "限制"]
    },
    
    # 地域类（TOP50城市+类型词）
    "geo": {
        "cities": ["北京", "上海", "广州", "深圳", "成都", "武汉", "杭州", "南京", "郑州", "西安"],
        "suffix": ["培训", "机构", "学校", "基地", "面授"]
    },
    
    # 竞品类（常见竞品词库）
    "competitor": {
        "brands": ["达内", "北大青鸟", "传智", "黑马", "千锋", "蜗牛", "尚硅谷"],
        "comparison": ["哪家好", "对比", "区别", "怎么样", "靠谱吗"]
    },

    # 新增否定词分类
    "negative": {
        "fraud": ["骗局", "诈骗", "跑路", "坑人", "黑心"],
        "complaint": ["投诉", "维权", "退费难", "虚假宣传", "差评"],
        "doubt": ["靠谱吗", "后悔", "没用", "被骗", "太坑"]
    },
    
    # 年龄限制参数
    "age_limit": 35  # 最大允许年龄
}

def build_keyword_regex(
    keyword_roots: Dict[str, List[str]] = {},
    categories: Optional[List[str]] = None,
    special_regex: List[str] = [],
    word_boundary: bool = False,
    escape: bool = True,
    flags: re.RegexFlag = re.IGNORECASE
) -> str:
    """
    通用关键词正则表达式构建函数
    
    参数：
    keyword_roots - 关键词字典 {类别: [关键词列表]}
    categories    - 指定要处理的类别列表（默认全部处理）
    special_regex  - 特殊正则表达式列表（默认为空列表）
    word_boundary - 是否精确匹配（默认False）
    escape        - 是否转义特殊字符（默认True）
    flags         - 正则表达式标志（默认忽略大小写）
    
    返回：编译好的正则表达式对象
    """
    # 处理可选类别筛选
    selected_categories = categories or keyword_roots.keys()
    
    # 构建正则部分
    patterns = []
    for category in selected_categories:
        terms = keyword_roots.get(category, [])
        if not terms:
            continue
            
        # 处理特殊字符转义
        processed_terms = [
            re.escape(term) if escape else term
            for term in terms
        ]
        
        # 添加词边界
        if word_boundary:
            processed_terms = [rf"\b{term}\b" for term in processed_terms]
            
        # 组合同类项
        if processed_terms:
            patterns.append(r"(?:{})".format("|".join(processed_terms)))
    
    # 处理无有效模式的情况
    if not patterns:
        return re.compile(r'(?!a)a')  # 永远不匹配的表达式
    
    # 构建完整正则
    full_pattern = "|".join(filter(None, ["|".join(patterns), "|".join(special_regex)]))
    if len(full_pattern) > 1:
        full_pattern = f"(?:{full_pattern})"
        
    return re.compile(full_pattern, flags=flags)

def build_regex_patterns():
    """构建正则表达式匹配模式"""
    patterns = {}
    
    # 课程类匹配（技术栈+课程类型）
    patterns["course"] = build_keyword_regex(KEYWORD_ROOTS["course"])
    
    # 费用类匹配（支付方式+金融方案）
    cost_terms = [
        r"(分期\d{0,3}期?)",  # 匹配分期相关数字组合
    ]
    patterns["cost"] = build_keyword_regex(KEYWORD_ROOTS["cost"],
                                           special_regex=cost_terms)
    
    # 地域类智能匹配（城市+后缀组合）
    geo_terms = [
        r"({city})[市]?{suffix}".format(city=city, suffix=suffix)
        for city in KEYWORD_ROOTS["geo"]["cities"]
        for suffix in KEYWORD_ROOTS["geo"]["suffix"]
    ]
    patterns["geo"] = build_keyword_regex(special_regex=geo_terms)
    
    # 竞品对比匹配（品牌词+对比词）
    comp_terms = [
        r"(?i)({brand})".format(brand="|".join(KEYWORD_ROOTS["competitor"]["brands"])),
        r"(?i)({comp})".format(comp="|".join(KEYWORD_ROOTS["competitor"]["comparison"]))
    ]
    patterns["competitor"] = build_keyword_regex(KEYWORD_ROOTS["competitor"])
    
    # 资质类匹配（教育背景+经验要求）
    qual_terms = [
        r"(高中|中专|学历)(.{0,3}要求|限制|可以)?",
        r"(零基础|无经验)",
        r"年龄[^\d]{0,2}(\d{2})?岁?"
    ]
    patterns["qualification"] = build_keyword_regex(KEYWORD_ROOTS["qualification"],
                                                    special_regex=qual_terms)

    # 否定词匹配（全匹配模式）
    patterns["negative"] = build_keyword_regex(KEYWORD_ROOTS["negative"])
    
    # 强化年龄检测（支持数字和中文写法）
    # age_pattern = r"(?i)(?:年龄|岁|年纪)[^\d]{0,3}(?P<age>\d{1,2})岁?"
    # patterns["age_check"] = re.compile(age_pattern)
    # 强化年龄检测（支持数字和中文写法，包含"多"字处理）
    age_pattern = r"""(?xi)
    ^  # 确保修饰符生效
    (?:
        # 情况1: 关键词在前
        (?:年[龄纪]|岁)
        [\s：:]* 
        (?:约|大概)? 
        (
            (?P<num1>\d{1,2})
            | 
            (?P<cn1>[零一二两三四五六七八九十廿卅]+)
        )
        |
        # 情况2: 数值在前
        (
            (?P<num2>\d{1,2})
            | 
            (?P<cn2>[零一二两三四五六七八九十廿卅]+)
        )
        [\s：:]* 
        (?:约|大概)? 
        (?:个?[周岁]|岁)
    )
    (?:多|余|左右)?  # 模糊词统一放在最后
    """

    patterns["age_check"] = re.compile(age_pattern)
    
    return patterns
def parse_age(match):
    num1 = match.group('num1')
    cn1 = match.group('cn1')
    num2 = match.group('num2')
    cn2 = match.group('cn2')
    
    age = None
    if num1:
        age = int(num1)
    elif num2:
        age = int(num2)
    elif cn1:
        age = cn2an(cn1, mode="smart")
    elif cn2:
        age = cn2an(cn2, mode= "smart")
    else:
        raise ValueError("Failed to parse age")
    
    
    # # 处理模糊词
    # if match.group(0).endswith(('多', '余', '左右')):
    #     return f"{age}+"
    return age
def classify_keyword(keyword, patterns):
    """多维度分类关键词"""
    classifications = []
    # 优先检测否定词
    if patterns["negative"].search(keyword):
        return ["negative"]
    
    # 年龄合规检查
    age_match = patterns["age_check"].search(keyword)
    if age_match:
        print(f"Age match: {age_match.group(0)}")
        age = parse_age(age_match)
        if age > KEYWORD_ROOTS["age_limit"]:
            return ["age_limit"]


    # 检测竞品类优先（避免误判）
    if patterns["competitor"].search(keyword):
        classifications.append("competitor")
        return classifications  # 竞品类单独处理
    
    # 多维检测
    for category in ["geo", "course", "cost", "qualification"]:
        if patterns[category].search(keyword):
            classifications.append(category)
    
    # 弱意向逻辑处理
    if not classifications:
        if any(q in keyword for q in ["好吗", "难吗", "前景"]):
            classifications.append("qualification")
    
    return classifications if classifications else ["other"]

# 测试用例
test_keywords = [
    "北京Java培训班学费分期",
    "高中毕业学编程就业前景",
    "达内和北大青鸟哪个好",
    "Python全栈开发周末班",
    "30岁学前端开发难吗",
    "40岁能学软件开发吗",
    "三十五岁学软件会不会太晚了"
]

# 执行分类
patterns = build_regex_patterns()
for kw in test_keywords:
    print(f"关键词：{kw}")
    print(f"分类结果：{classify_keyword(kw, patterns)}")
    print("-"*50)



