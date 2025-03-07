from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from graphviz import Digraph
import base64

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class Scanner:
    def __init__(self, input_string):
        self.input_string = input_string.replace(' ', '')
        self.position = 0
        self.current_char = self.input_string[self.position] if self.input_string else None

    def advance(self):
        self.position += 1
        if self.position < len(self.input_string):
            self.current_char = self.input_string[self.position]
        else:
            self.current_char = None

    def get_tokens(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char.isdigit():
                tokens.append(('NUM', self.collect_number()))
            elif self.current_char.isalpha():
                tokens.append(('ID', self.current_char))
                self.advance()
            elif self.current_char in '+-*/()':
                tokens.append(('SYM', self.current_char))
                self.advance()
            else:
                self.advance()
        return tokens

    def collect_number(self):
        number = self.current_char
        self.advance()
        while self.current_char is not None and self.current_char.isdigit():
            number += self.current_char
            self.advance()
        return number

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[self.position] if self.tokens else None
        self.graph = Digraph(comment='Syntax Tree')

    def advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None

    def expect(self, expected_type, expected_value=None):
        if (self.current_token and self.current_token[0] == expected_type and
            (expected_value is None or self.current_token[1] == expected_value)):
            self.advance()
        else:
            raise Exception(f"Syntax error: expected {expected_type} {expected_value} but got {self.current_token}")

    def parse_expr(self, parent=None):
        expr_node = f'expr{self.position}'
        self.graph.node(expr_node, 'expr')
        if parent:
            self.graph.edge(parent, expr_node)
        
        term_node = self.parse_term(expr_node)
        self.parse_z(expr_node)
        
        return expr_node

    def parse_z(self, parent=None):
        if self.current_token and self.current_token[1] in ['+', '-']:
            op_node = f'op{self.position}'
            self.graph.node(op_node, self.current_token[1])
            self.graph.edge(parent, op_node)
            self.advance()
            
            expr_node = self.parse_expr(parent)
        # epsilon transition does nothing
        return parent

    def parse_term(self, parent=None):
        term_node = f'term{self.position}'
        self.graph.node(term_node, 'term')
        if parent:
            self.graph.edge(parent, term_node)
        
        factor_node = self.parse_factor(term_node)
        self.parse_x(term_node)
        
        return term_node

    def parse_x(self, parent=None):
        if self.current_token and self.current_token[1] in ['*', '/']:
            op_node = f'op{self.position}'
            self.graph.node(op_node, self.current_token[1])
            self.graph.edge(parent, op_node)
            self.advance()
            
            term_node = self.parse_term(parent)
        # epsilon transition does nothing
        return parent

    def parse_factor(self, parent=None):
        factor_node = f'factor{self.position}'
        self.graph.node(factor_node, 'factor')
        if parent:
            self.graph.edge(parent, factor_node)
        
        if self.current_token and self.current_token[1] == '(':
            paren_open_node = f'paren_open{self.position}'
            self.graph.node(paren_open_node, '(')
            self.graph.edge(factor_node, paren_open_node)
            self.advance()
            
            expr_node = self.parse_expr(factor_node)
            
            self.expect('SYM', ')')
            paren_close_node = f'paren_close{self.position}'
            self.graph.node(paren_close_node, ')')
            self.graph.edge(factor_node, paren_close_node)
        elif self.current_token and self.current_token[0] == 'NUM':
            num_node = f'num{self.position}'
            self.graph.node(num_node, self.current_token[1])
            self.graph.edge(factor_node, num_node)
            self.advance()
        elif self.current_token and self.current_token[0] == 'ID':
            id_node = f'id{self.position}'
            self.graph.node(id_node, self.current_token[1])
            self.graph.edge(factor_node, id_node)
            self.advance()
        else:
            raise Exception("Syntax error: expected '(', number or identifier")
        
        return factor_node

    def draw_syntax_tree(self, expression):
        print(f"Generating syntax tree for expression: {expression}")
        scanner = Scanner(expression)
        self.tokens = scanner.get_tokens()
        self.position = 0
        self.current_token = self.tokens[self.position] if self.tokens else None
        self.parse_expr()
        file_path = 'static/syntax_tree'
        try:
            self.graph.render(file_path, format='png', cleanup=False)
            with open(f"{file_path}.png", "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            print(f"File {file_path} created successfully.")
            return base64_image
        except Exception as e:
            print(f"Error generating image: {e}")
            return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-syntax-tree', methods=['POST'])
def generate_syntax_tree():
    data = request.json
    expressions = data['expression'].split('\n')
    print(f"Received expressions from client: {expressions}")  # Debug message
    last_expression = expressions[-1]
    parser = Parser([])
    base64_image = parser.draw_syntax_tree(last_expression)
    if base64_image:
        return jsonify({"success": True, "image": base64_image})
    else:
        return jsonify({"success": False})

if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5000, debug=True)
