import re
from collections import namedtuple
import copy

# 定义AST节点类型
ExactNode = namedtuple('ExactNode', ['pattern', 'is_boundary'])
WildcardNode = namedtuple('WildcardNode', ['patterns', 'is_boundary'])
ComplexRegexNode = namedtuple('ComplexRegexNode', ['regex', 'is_boundary'])
AndNode = namedtuple('AndNode', ['left', 'right'])
OrNode = namedtuple('OrNode', ['left', 'right'])
NotNode = namedtuple('NotNode', ['child'])

class KeywordClassifier:
    def __init__(self, config, wildcard, case_sensitive=True):
        self.config = config
        self.wildcard = wildcard
        self.case_sensitive = case_sensitive
        local_config = copy.deepcopy(config)
        
        self.negatives = self._process_negatives(local_config.pop('否定词', {}))
        self.brands = self._process_brands(local_config.pop('品牌词', {}))
        self.root = self._build_classifier(local_config) 
    
    def _process_negatives(self, config):
        return [(k, self._parse_condition(c)) for k, c in config.items()]
    
    def _process_brands(self, config):
        return [(k, self._parse_condition(c)) for k, c in config.items()]
    
    def _parse_condition(self, condition_str):

        tokens = tokenize(condition_str)
        parser = Parser(tokens)
        return parser.parse_expression()
    
    def _build_classifier(self, config):
        classifier = {}
        for key in sorted(config.keys()):
            condition = self._parse_condition(config[key])
            children = self._build_classifier(config.get(key, {}))
            classifier[key] = {'condition': condition, 'children': children}
        return classifier
    
    def classify(self, text):
        # Check negatives
        for neg_key, ast in self.negatives:
            if ast.evaluate(text, self.case_sensitive):
                return f'否定词-{neg_key}'
        # Check brands
        for brand_key, ast in self.brands:
            if ast.evaluate(text, self.case_sensitive):
                return f'品牌词-{brand_key}'
        # Process root classifier
        if not self.root:
            return '其他'
        best_path = None
        max_count = -1
        
        stack = [(node, [], 0) for node in sorted(self.root.values(), key=lambda x: x['key'])]
        
        while stack:
            current_node, path, count = stack.pop()
            current_key = list(current_node.keys())[0]
            current_ast = current_node[current_key]['condition']
            
            if not current_ast.evaluate(text, self.case_sensitive):
                continue
            
            new_count = count + 1
            new_path = path + [current_key]
            
            children = current_node[current_key]['children']
            if not children:
                if (new_count > max_count) or (new_count == max_count and (best_path is None or new_path < best_path)):
                    best_path = new_path
                    max_count = new_count
            else:
                for child in sorted(children.values(), key=lambda x: x['key']):
                    stack.append((child, new_path, new_count))
        
        return '-'.join(best_path) if best_path else '其他'

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def consume(self):
        self.pos += 1
    
    def parse_expression(self):
        return self.parse_or_expression()
    
    def parse_or_expression(self):
        node = self.parse_and_expression()
        while self.peek() == '|':
            self.consume()
            right = self.parse_and_expression()
            node = OrNode(node, right)
        return node
    
    def parse_and_expression(self):
        node = self.parse_unary_expression()
        while self.peek() == '&':
            self.consume()
            right = self.parse_unary_expression()
            node = AndNode(node, right)
        return node
    
    def parse_unary_expression(self):
        if self.peek() == '-':
            self.consume()
            expr = self.parse_primary_expression()
            return NotNode(expr)
        return self.parse_primary_expression()
    
    def parse_primary_expression(self):
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of input")
        if token == '(':
            self.consume()
            expr = self.parse_expression()
            if self.peek() != ')':
                raise SyntaxError("Missing closing parenthesis")
            self.consume()
            return expr
        else:
            atom = self.parse_atom(token)
            return atom
    
    def parse_atom(self, token):
        if token.startswith('$##') and token.endswith('#$'):
            regex_str = token[3:-2]
            is_boundary = False
            if len(regex_str) >= 2 and regex_str.startswith('^') and regex_str.endswith('$'):
                is_boundary = True
                regex_str = regex_str[1:-1]
            regex = re.compile(regex_str, flags=re.IGNORECASE if not self.case_sensitive else 0)
            return ComplexRegexNode(regex, is_boundary)
        elif token.startswith('^') and token.endswith('^'):
            pattern = token[1:-1]
            is_boundary = True
            return ExactNode(re.compile(re.escape(pattern)), is_boundary)
        elif '{}' in token:
            wildcard_matches = []
            for match in re.finditer(r'\{(\w+)\}', token):
                key = match.group(1)
                if key not in self.wildcard:
                    continue
                value = self.wildcard[key]
                replaced = token.replace('{' + key + '}', re.escape(value))
                wildcard_matches.append(replaced)
            if not wildcard_matches:
                raise SyntaxError(f"No wildcards available for {token}")
            combined = '|'.join(wildcard_matches)
            is_boundary = False
            if token.startswith('^') and token.endswith('^'):
                is_boundary = True
                combined = '^' + combined + '$'
            regex = re.compile(combined, flags=re.IGNORECASE if not self.case_sensitive else 0)
            return WildcardNode(regex, is_boundary)
        else:
            pattern = re.escape(token)
            is_boundary = False
            if token.startswith('^') and token.endswith('^'):
                is_boundary = True
                pattern = '^' + pattern + '$'
            regex = re.compile(pattern, flags=re.IGNORECASE if not self.case_sensitive else 0)
            return ExactNode(regex, is_boundary)

def tokenize(s):
    # tokens = []
    # pattern = r'([-&|()])|([^\\s-&|()]+)'
    # for match in re.finditer(pattern, s):
    #     if match.group(1):
    #         tokens.append(match.group(1))
    #     else:
    #         token = match.group(2).strip()
    #         if token:
    #             tokens.append(token)
    # return tokens
    complex_regex_pattern = r'\$##(.*?)##\$'
    token_pattern = re.compile(r"""
        ([-&|()]) |                   # 操作符
        (\$##.*?##\$) |               # 复杂正则（非贪婪匹配）
        ([^\s\-&|()]+)               # 其他内容（排除空白、-、&、|、()）
    """, re.VERBOSE)
    
    tokens = []
    pos = 0
    while pos < len(s):
        match = token_pattern.match(s, pos)
        if not match:
            # 跳过空格或非法字符
            if s[pos] == ' ':
                pos += 1
            else:
                raise SyntaxError(f"Unexpected character: '{s[pos]}' at position {pos}")
            continue
        
        operator, complex_regex, text = match.groups()
        
        if complex_regex is not None:
            tokens.append(('complex', complex_regex.strip()))
            pos = match.end()
        elif operator is not None:
            tokens.append(operator)
            pos += 1
        elif text is not None:
            tokens.append(text.strip())
            pos += len(text)
    
    return tokens

# AST Node Evaluation Methods
def evaluate(node, text, case_sensitive):
    if isinstance(node, ExactNode):
        return node.pattern.fullmatch(text) if node.is_boundary else node.pattern.search(text)
    elif isinstance(node, WildcardNode):
        for pattern in node.patterns:
            if node.is_boundary:
                if pattern.fullmatch(text):
                    return True
            else:
                if pattern.search(text):
                    return True
        return False
    elif isinstance(node, ComplexRegexNode):
        return node.regex.fullmatch(text) if node.is_boundary else node.regex.search(text)
    elif isinstance(node, NotNode):
        return not evaluate(node.child, text, case_sensitive)
    elif isinstance(node, AndNode):
        return evaluate(node.left, text, case_sensitive) and evaluate(node.right, text, case_sensitive)
    elif isinstance(node, OrNode):
        return evaluate(node.left, text, case_sensitive) or evaluate(node.right, text, case_sensitive)
    else:
        raise TypeError(f"Unknown node type: {type(node)}")

# Example usage
if __name__ == "__main__":
    config = {
        #     "否定词": {
        #     "年龄": [
        #         r'''$#(?xi)
        #         ^
        #         (?:
        #             (?:年[龄纪]|岁)
        #             [\s：:]*
        #             (?:约|大概)?
        #             (
        #                 (?P<num1>\d{1,2})
        #                 |
        #                 (?P<cn1>[零一二两三四五六七八九十廿卅]+)
        #             )
        #             |
        #             (
        #                 (?P<num2>\d{1,2})
        #                 |
        #                 (?P<cn2>[零一二两三四五六七八九十廿卅]+)
        #             )
        #             [\s：:]*
        #             (?:约|大概)?
        #             (?:个?[周岁]|岁)
        #         )
        #         (?:多|余|左右)?
        #         #$'''
        #     ]
        # },
        "课程": {
            "java": {
                "培训": {
                    "学费": '学费|费用|钱',
                    "重点城市": '{地址}'
                }
            }
        }
    }

    wildcard = {'地址': ['长沙', '东莞']}
    classifier = KeywordClassifier(config, wildcard, case_sensitive=False)
    
    test_cases = [
        "长沙Java培训",
        "长沙Java培训多少钱",
        "Java培训",
        "Java培训学费",
        "长沙web培训"
        "28岁能学编程吗"
    ]
    
    for case in test_cases:
        print(f"{case} -> {classifier.classify(case)}")