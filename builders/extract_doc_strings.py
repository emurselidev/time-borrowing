"""Extract user-facing strings from document build scripts."""
import ast
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {
    "Calibri", "Table Grid", "List Bullet", "007A87", "utf-8",
    "w:shd", "w:pBdr", "w:bottom", "clear", "auto", "single",
}


def extract_strings(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    strings = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if s in SKIP or len(s) < 3:
                continue
            if not any(c.isalpha() for c in s):
                continue
            if s.startswith("w:"):
                continue
            strings.add(s)
    return sorted(strings, key=len)


def main():
    all_strings = {}
    for fn in ("build_all_docs.py", "build_word_doc.py"):
        path = os.path.join(HERE, fn)
        ss = extract_strings(path)
        all_strings[fn] = ss
        print(f"{fn}: {len(ss)} strings")

    merged = sorted(set(s for ss in all_strings.values() for s in ss), key=len)
    out = os.path.join(HERE, "locales", "en_keys.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Merged unique: {len(merged)} -> {out}")


if __name__ == "__main__":
    main()
