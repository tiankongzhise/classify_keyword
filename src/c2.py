import pandas as pd
import re

def classify_keyword(keyword):
    # 高成交-品牌词
    if re.search(r'(课程|培训|学费|招生|专业|就业)', keyword) and not re.search(r'(吗|么|怎么|如何|哪)', keyword):
        return '高成交-品牌词'
    # 高成交-费用查询
    elif re.search(r'(学费|价格|多少钱|收费|贵不贵)', keyword):
        return '高成交-费用查询'
    # 中成交-课程咨询
    elif re.search(r'(课程|专业|就业|培训|学什么)', keyword) and re.search(r'(吗|么|怎么|如何)', keyword):
        return '中成交-课程咨询'
    # 低成交-评价类
    elif re.search(r'(怎么样|好吗|靠谱吗|口碑|如何)', keyword):
        return '低成交-评价类'
    # 低成交-信息查询
    elif re.search(r'(地址|路线|校区|电话|官网|怎么去)', keyword):
        return '低成交-信息查询'
    else:
        return '无效词'

# 读取Excel文件
df = pd.read_excel('./keyword/品牌词.xlsx')

# 分类关键词
df['分组'] = df['关键词'].apply(classify_keyword)

# 保存结果到新文件
with pd.ExcelWriter('./result/品牌词_分组结果.xlsx') as writer:
    for group in df['分组'].unique():
        group_df = df[df['分组'] == group]
        group_df.to_excel(writer, sheet_name=group, index=False)
