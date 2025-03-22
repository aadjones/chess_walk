import ast, os, json
from pathlib import Path

def extract_code_info(filepath: Path) -> dict:
    try:
        tree = ast.parse(filepath.read_text(), filename=str(filepath))
    except SyntaxError as e:
        return {"path": str(filepath), "error": f"SyntaxError: {e}"}

    info = {"path": str(filepath), "imports": [], "classes": [], "functions": []}
    current_class = None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                info["imports"].append(alias.name)
        if isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                info["imports"].append(f"{module}.{alias.name}")
        if isinstance(node, ast.ClassDef):
            current_class = node
            info["classes"].append({
                "name": node.name,
                "doc": ast.get_docstring(node) or "",
                "methods": [extract_function_data(m) for m in node.body if isinstance(m, ast.FunctionDef)]
            })
        if isinstance(node, ast.FunctionDef):
            if current_class is None:  # Only add standalone functions
                info["functions"].append(extract_function_data(node))
            current_class = None  # Reset class context after processing function

    return info

def extract_function_data(node):
    return {
        "name": node.name,
        "doc": ast.get_docstring(node) or "",
        "args": [arg.arg for arg in node.args.args],
        "decorators": [d.id if isinstance(d, ast.Name) else ast.unparse(d) for d in node.decorator_list],
        "returns": ast.unparse(node.returns) if node.returns else None
    }

if __name__ == "__main__":
    base = Path('src')
    summaries = []
    for py in base.rglob('*.py'):
        summaries.append(extract_code_info(py))
    out = Path('summaries')
    out.mkdir(exist_ok=True)
    for info in summaries:
        fname = out / (Path(info['path']).stem + '.json')
        fname.write_text(json.dumps(info, indent=2))