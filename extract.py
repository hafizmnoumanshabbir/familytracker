try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        import sys; print("NEED:pypdf or PyPDF2", file=sys.stderr); sys.exit(1)
r = PdfReader("/Users/macbook/Downloads/Reading-List-v2.pdf")
print(f"--PAGES:{len(r.pages)}--")
for i, p in enumerate(r.pages):
    print(f"\n===PAGE {i+1}===")
    print(p.extract_text())
