def draw_syntax_tree(self, expression):
        print(f"Generating syntax tree for expression: {expression}")
        scanner = Scanner(expression)
        self.tokens = scanner.get_tokens()
        self.position = 0
        self.current_token = self.tokens[
            self.position] if self.tokens else None
        self.parse_expr()
        if not os.path.exists('static'):
            os.makedirs('static')
        file_path = 'static/syntax_tree'
        try:
            self.graph.render(file_path, format='png', cleanup=False)
            with open(f"{file_path}.png", "rb") as image_file:
                base64_image = base64.b64encode(
                    image_file.read()).decode('utf-8')
            print(f"File {file_path}.png created successfully.")
            return base64_image
        except Exception as e:
            print(f"Error generating image: {e}")
            return None


@app.route('/')
def index():   #aca joo
    return render_template('index.html')


@app.route('/generate-syntax-tree', methods=['POST'])
def generate_syntax_tree():
    data = request.json
    expression = data['expression']
    print(f"Received expression from client: {expression}")  # Debug message
    parser = Parser([])
    base64_image = parser.draw_syntax_tree(expression)
    if base64_image:
        return jsonify({"success": True, "image": base64_image})
    else:
        return jsonify({"success": False})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
