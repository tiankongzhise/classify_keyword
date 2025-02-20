# -*- coding: utf-8 -*-
import re

# 详细词根字典（新增行业扩展词）
KEYWORD_ROOTS = {
    # 课程类（扩展技术栈维度）
    "course": {
        "languages": ["java", "python", "c#", "php", "前端", "全栈"],
        "tech_stack": ["web开发", "小程序", "app开发", "数据库", "云计算"],
        "course_type": ["就业班", "实战班", "周末班", "网课", "全日制"]
    },
    
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

def build_regex_patterns():
    """构建正则表达式匹配模式"""
    patterns = {}
    
    # 课程类匹配（技术栈+课程类型）
    course_terms = [
        r"(?i)({lang})".format(lang="|".join(KEYWORD_ROOTS["course"]["languages"])),
        r"(?i)({tech})".format(tech="|".join(KEYWORD_ROOTS["course"]["tech_stack"])),
        r"(?i)({types})".format(types="|".join(KEYWORD_ROOTS["course"]["course_type"]))
    ]
    patterns["course"] = re.compile("|".join(course_terms))
    
    # 费用类匹配（支付方式+金融方案）
    cost_terms = [
        r"(?i)({payment})".format(payment="|".join(KEYWORD_ROOTS["cost"]["payment"])),
        r"(?i)(分期\d{0,3}期?)",  # 匹配分期相关数字组合
        r"(?i)({financial})".format(financial="|".join(KEYWORD_ROOTS["cost"]["financial"]))
    ]
    patterns["cost"] = re.compile("|".join(cost_terms))
    
    # 地域类智能匹配（城市+后缀组合）
    geo_terms = [
        r"(?i)({city})[市]?{suffix}".format(city=city, suffix=suffix)
        for city in KEYWORD_ROOTS["geo"]["cities"]
        for suffix in KEYWORD_ROOTS["geo"]["suffix"]
    ]
    patterns["geo"] = re.compile("|".join(geo_terms))
    
    # 竞品对比匹配（品牌词+对比词）
    comp_terms = [
        r"(?i)({brand})".format(brand="|".join(KEYWORD_ROOTS["competitor"]["brands"])),
        r"(?i)({comp})".format(comp="|".join(KEYWORD_ROOTS["competitor"]["comparison"]))
    ]
    patterns["competitor"] = re.compile("|".join(comp_terms))
    
    # 资质类匹配（教育背景+经验要求）
    qual_terms = [
        r"(?i)(高中|中专|学历)(.{0,3}要求|限制|可以)?",
        r"(?i)(零基础|无经验)",
        r"(?i)年龄[^\d]{0,2}(\d{2})?岁?"
    ]
    patterns["qualification"] = re.compile("|".join(qual_terms))

    # 否定词匹配（全匹配模式）
    negative_terms = [
        r"(?i)({})".format("|".join(
            [w for sublist in KEYWORD_ROOTS["negative"].values() for w in sublist]
        ))
    ]
    patterns["negative"] = re.compile("|".join(negative_terms))
    
    # 强化年龄检测（支持数字和中文写法）
    age_pattern = r"(?i)(?:年龄|岁|年纪)[^\d]{0,3}(?P<age>\d{1,2})岁?"
    patterns["age_check"] = re.compile(age_pattern)
    
    return patterns

def classify_keyword(keyword, patterns):
    """多维度分类关键词"""
    classifications = []
    # 优先检测否定词
    if patterns["negative"].search(keyword):
        return ["negative"]
    
    # 年龄合规检查
    age_match = patterns["age_check"].search(keyword)
    if age_match:
        age = int(age_match.group("age"))
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
    "30岁学前端开发难吗"
]

# 执行分类
patterns = build_regex_patterns()
for kw in test_keywords:
    print(f"关键词：{kw}")
    print(f"分类结果：{classify_keyword(kw, patterns)}")
    print("-"*50)

# 可继续扩展的维度示例
"course": {
    "frameworks": ["spring", "django", "vue", "react"],
    "certification": ["软考", "华为认证", "红帽认证"]
},
"cost": {
    "refund": ["退费", "违约金", "试听"]
}

# 如需支持"三十五岁"的识别，可添加以下处理：
from cn2an import cn2an

def convert_chinese_number(text):
    try:
        return cn2an(text, smart=True)
    except:
        return None
    
# 可从文件或数据库加载最新否定词
def load_negative_words():
    with open('negative_words.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]
    
# 处理"30多岁"类表述
age_range_pattern = r"(?i)(\d{2})多?岁"