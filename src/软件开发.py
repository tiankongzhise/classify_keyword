import pandas as pd
import re

# # 分类规则配置
# CLASS_RULES = {
#     "成交意向": {
#         "高意向": ["培训费", "学费", "价格表", "收费", "多少钱", "包分配"],
#         "中意向": ["哪家好", "推荐", "对比", "哪里好", "哪个好", "如何选"],
#         "低意向": ["是什么", "学什么", "课程", "需要学", "学习内容"]
#     },
#     "词性": {
#         "机构类": ["机构", "学校", "中心", "学院"],
#         "课程类": ["课程", "学习", "学什么", "技术"],
#         "地域类": ["深圳", "成都", "北京", "上海", "广州"],
#         "疑问类": ["好吗", "怎么样", "靠谱吗", "如何"],
#         "技术类": ["Python", "编程", "Java", "C++", "移动开发"],
#         "费用类": ["多少钱", "收费", "价格", "学费"],
#         "职业类": ["就业", "工程师", "程序员", "职业发展"]
#     }
# }
# 分类规则配置
CLASS_RULES = {
    "成交意向":{
    "高意向": ["培训", "机构", "学校", "学费", "课程表", "推荐", "排名", "正规", "深圳", "成都"],
    "中意向": ["课程", "学什么", "工程师", "认证", "比较", "哪个好"],
    "低意向": ["哪里学", "怎么学", "什么是", "零基础", "就业", "前景"]
    },
    "词性": {
    "需求词": ["学", "培训", "开发", "课程", "实训"],
    "决策词": ["哪家", "推荐", "排名", "对比", "比较"],
    "价值词": ["就业", "项目", "高薪", "实战", "晋升"],
    "信任词": ["正规", "老牌", "上市", "名师", "认证"],
    "地域词": ["深圳", "北京", "上海", "广州", "成都"]
    }
}

def classify_keywords(keywords):
    results = []
    for keyword in keywords:
        # 处理空格和特殊字符
        cleaned_kw = re.sub(r'\s+', '', keyword)
        
        record = {"关键词": keyword}
        
        # 成交意向分类
        intention = "未分类"
        for level, terms in CLASS_RULES["成交意向"].items():
            if any(term in cleaned_kw for term in terms):
                intention = level
                break
        record["成交意向"] = intention
        
        # 词性分类（允许多标签）
        word_types = []
        for w_type, terms in CLASS_RULES["词性"].items():
            if any(term in cleaned_kw for term in terms):
                word_types.append(w_type)
        record["词性分类"] = "|".join(word_types) if word_types else "其他"
        
        results.append(record)
    return pd.DataFrame(results)

# 读取数据
df = pd.read_excel("./keyword/软件开发.xlsx")
keywords = df["关键词"].tolist()

# 执行分类
classified_df = classify_keywords(keywords)

# 保存结果
classified_df.to_excel("./result/软件开发.xlsx", index=False)
print("分类完成，结果已保存到 软件开发.xlsx")
