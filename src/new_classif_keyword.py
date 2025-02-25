import re
from collections import defaultdict
class Tokenizer:
    def __init__(self, config_dict, wildcard_dict, case_sensitive=False):
        self.config = config_dict
        self.wildcards = wildcard_dict
        self.case_sensitive = case_sensitive
        self.compiled_rules = []
        self._compile_rules(config_dict)
    def _compile_rules(self, current_dict, path=[]):
        for key, value in current_dict.items():
            current_path = path + [key]
            if isinstance(value, dict):
                self._compile_rules(value, current_path)
            else:
                pattern = self._parse_expression(value)
                self.compiled_rules.append({
                    'path': current_path,
                    'pattern': pattern,
                    'exclude': self._parse_exclusion(value)
                })
    def _parse_expression(self, expr):
        # 处理通配符
        expr = re.sub(r'\{([^}]+)\}', self._replace_wildcard, expr)
        
        # 处理边界匹配
        expr = re.sub(r'\^([^^]+)\^', r'^\1$', expr)
        
        # 转换逻辑操作符
        expr = re.sub(r'&', ' AND ', expr)
        expr = re.sub(r'\|', ' OR ', expr)
        expr = re.sub(r'-', ' NOT ', expr)
        
        # 添加括号优先级处理
        return self._build_regex(expr)
    def _build_regex(self, expr):
        # 使用逆波兰表达式处理操作符优先级
        precedence = {'(': 0, ')': 0, 'NOT': 3, 'AND': 2, 'OR': 1}
        output = []
        stack = []
        
        for token in re.findall(r'$|$|\w+|\S', expr):
            if token == '(':
                stack.append(token)
            elif token == ')':
                while stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            elif token in precedence:
                while stack and precedence[stack[-1]] >= precedence[token]:
                    output.append(stack.pop())
                stack.append(token)
            else:
                output.append(token)
        
        while stack:
            output.append(stack.pop())
        
        return self._evaluate_rpn(output)
    def _evaluate_rpn(self, rpn_tokens):
        """逆波兰表达式求值核心算法"""
        stack = []
        
        for token in rpn_tokens:
            if token in {'AND', 'OR', 'NOT'}:
                # 处理二元操作符
                if token == 'NOT':
                    operand = stack.pop()
                    stack.append(f'(?!.*{operand})')
                else:
                    right = stack.pop()
                    left = stack.pop()
                    if token == 'AND':
                        # 使用顺序无关的肯定顺序断言
                        stack.append(f'(?=.*{left})(?=.*{right})')
                    elif token == 'OR':
                        stack.append(f'({left}|{right})')
            else:
                # 处理基础token
                stack.append(f'({token})')
        
        # 合并最终结果
        if len(stack) != 1:
            raise ValueError(f"Invalid RPN expression,{stack}")
        
        # 添加边界匹配检测
        return f'^{stack[0]}.*$' if '^' not in stack[0] else stack[0]
    def _replace_wildcard(self, match):
        key = match.group(1)
        values = self.wildcards.get(key, [])
        return '(' + '|'.join(re.escape(v) for v in values) + ')'
    def tokenize(self, text):
        matches = []
        for rule in self.compiled_rules:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            if re.search(rule['pattern'], text, flags=flags):
                if not self._check_exclusion(rule['exclude'], text):
                    matches.append(rule['path'])
        
        # 统计层级匹配次数
        counter = defaultdict(int)
        for path in matches:
            for depth in range(1, len(path)+1):
                counter[tuple(path[:depth])] += 1
        
        # 选择最优层级
        if not counter:
            return ['其他']
        
        max_count = max(counter.values())
        candidates = [k for k, v in counter.items() if v == max_count]
        
        # 按字典顺序排序
        sorted_candidates = sorted(candidates, key=lambda x: (len(x), x))
        return '-'.join(sorted_candidates[-1])
    def _check_exclusion(self, exclude_patterns, text):
        flags = 0 if self.case_sensitive else re.IGNORECASE
        for pattern in exclude_patterns:
            if re.search(pattern, text, flags=flags):
                return True
        return False


class EnhancedTokenizer(Tokenizer):
    def _parse_expression(self, expr):
        # 新增自定义正则表达式解析
        if isinstance(expr, str) and expr.startswith('$#') and expr.endswith('#$'):
            return self._parse_custom_regex(expr[2:-2])
        
        # 原有处理逻辑
        expr = re.sub(r'\{([^}]+)\}', self._replace_wildcard, expr)
        expr = re.sub(r'\^([^^]+)\^', r'^\1$', expr)
        expr = re.sub(r'&', ' AND ', expr)
        expr = re.sub(r'\|', ' OR ', expr)
        expr = re.sub(r'-', ' NOT ', expr)
        return self._build_regex(expr)

    def _parse_custom_regex(self, pattern):
        """处理自定义正则表达式"""
        try:
            # 自动捕获修饰符并编译正则
            return re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid custom regex: {pattern}") from e

    def _compile_rules(self, current_dict, path=[]):
        for key, value in current_dict.items():
            current_path = path + [key]
            if isinstance(value, dict):
                self._compile_rules(value, current_path)
            else:
                # 处理列表类型的值（多个模式）
                patterns = value if isinstance(value, list) else [value]
                for pattern in patterns:
                    compiled = self._parse_expression(pattern)
                    self.compiled_rules.append({
                        'path': current_path,
                        'pattern': compiled,
                        'exclude': self._parse_exclusion(pattern) if not isinstance(compiled, re.Pattern) else []
                    })

    def _parse_exclusion(self, expr):
        """排除逻辑处理（不处理自定义正则）"""
        if isinstance(expr, re.Pattern):
            return []
        return super()._parse_exclusion(expr)

# 配置示例
config = {
        "否定词": {
        "年龄": [
            r'''$#(?xi)
            ^
            (?:
                (?:年[龄纪]|岁)
                [\s：:]*
                (?:约|大概)?
                (
                    (?P<num1>\d{1,2})
                    |
                    (?P<cn1>[零一二两三四五六七八九十廿卅]+)
                )
                |
                (
                    (?P<num2>\d{1,2})
                    |
                    (?P<cn2>[零一二两三四五六七八九十廿卅]+)
                )
                [\s：:]*
                (?:约|大概)?
                (?:个?[周岁]|岁)
            )
            (?:多|余|左右)?
            #$'''
        ]
    },
    "课程": {
        "java": {
            "培训": {
                "学费": '学费|费用|钱',
                "重点城市": '{地址}'
            }
        }
    }
}

wildcards = {'地址': ['长沙', '东莞']}

# 初始化分词器
tokenizer = EnhancedTokenizer(config, wildcards, case_sensitive=False)

# 测试用例
test_cases = [
    "长沙Java培训",
    "长沙Java培训多少钱",
    "Java培训",
    "Java培训学费",
    "长沙web培训",
    "35岁学Java好不好",
    "28周岁程序员",
    "二十岁开始编程",
    "年龄：约25左右"
]

for case in test_cases:
    print(f"{case} -> {tokenizer.tokenize(case)}")