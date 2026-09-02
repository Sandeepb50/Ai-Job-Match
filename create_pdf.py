import PyPDF2

writer = PyPDF2.PdfWriter()
# PyPDF2 PdfWriter doesn't draw text without canvas, so let's write valid PDF bytes directly
pdf_bytes = (
    "%PDF-1.4\n"
    "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    "3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>> endobj\n"
    "4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
    "5 0 obj <</Length 115>> stream\n"
    "BT\n"
    "/F1 14 Tf\n"
    "50 750 Td\n"
    "(Alex Smith - Senior Software Engineer) Tj\n"
    "0 -20 Td\n"
    "(Skills: Python, Flask, REST API, PyPDF2, Gemini AI, Docker) Tj\n"
    "ET\n"
    "endstream\n"
    "endobj\n"
    "xref\n"
    "0 6\n"
    "0000000000 65535 f \n"
    "0000000009 00000 n \n"
    "0000000058 00000 n \n"
    "0000000115 00000 n \n"
    "0000000226 00000 n \n"
    "0000000293 00000 n \n"
    "trailer <</Size 6 /Root 1 0 R>>\n"
    "startxref\n"
    "460\n"
    "%%EOF\n"
).encode("latin-1")

with open("sample_resume.pdf", "wb") as f:
    f.write(pdf_bytes)

print("Created sample_resume.pdf successfully")
