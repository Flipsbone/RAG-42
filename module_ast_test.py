import ast

code = "x = 5 + 3"
# Parse the code into an AST object
tree = ast.parse(code)

# Dump the tree into a readable string format
print(ast.dump(tree, indent=4))