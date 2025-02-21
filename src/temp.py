import re
from typing import Dict, List, Optional

def build_keyword_regex(
    keyword_roots: Dict[str, List[str]],
    *,
    categories: Optional[List[str]] = None,
    word_boundary: bool = False,
    escape: bool = True,
    flags: re.RegexFlag = re.IGNORECASE
) -> re.Pattern:
    """
    通用关键词正则表达式构建函数
    
    参数：
    keyword_roots - 关键词字典 {类别: [关键词列表]}
    categories    - 指定要处理的类别列表（默认全部处理）
    word_boundary - 是否添加词边界（默认True）
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
    full_pattern = "|".join(patterns)
    if len(patterns) > 1:
        full_pattern = f"(?:{full_pattern})"
        
    return re.compile(full_pattern, flags=flags)

# 使用示例
if __name__ == "__main__":
    # 示例关键词数据
    KEYWORD_ROOTS = {
        "languages": ["Python", "C++", "Java", "JavaScript", "SQL"],
        "frameworks": ["Django", "Flask", "React", "Vue.js"],
        "tools": ["Git", "Docker", "Kubernetes", "AWS EC2"],
        "empty_category": []
    }

    # 构建编程语言正则
    lang_regex = build_keyword_regex(
        {"languages": KEYWORD_ROOTS["languages"]},
        word_boundary=False
    )
    
    # 构建全栈技术正则
    full_stack_regex = build_keyword_regex(
        KEYWORD_ROOTS,
        categories=["languages", "frameworks", "tools"],
        escape=True,
        word_boundary=False

        
    )

    # 测试用例
    test_cases = [
        "Python3.8",       # 匹配语言
        "vue.js项目",       # 匹配框架
        "aws ec2实例",      # 匹配工具（带空格）
        "Java开发工程师",    # 边界测试
        "无关内容"          # 不匹配
    ]

    print("编程语言匹配测试：")
    for text in test_cases:
        print(f"{text:15} => {bool(lang_regex.search(text))}")

    print("\n全栈技术匹配测试：")
    for text in test_cases:
        print(f"{text:15} => {bool(full_stack_regex.search(text))}")
