import io
import sys
import unittest
from app import app

def create_sample_pdf_bytes():
    pdf_content = (
        "%PDF-1.4\n"
        "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        "3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>> endobj\n"
        "4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        "5 0 obj <</Length 78>> stream\n"
        "BT\n"
        "/F1 12 Tf\n"
        "100 700 Td\n"
        "(John Doe - Software Engineer experienced in Python, Flask, and REST APIs.) Tj\n"
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
        "422\n"
        "%%EOF\n"
    )
    return pdf_content.encode("latin-1")

class TestPdfExtractEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_extract_pdf_success(self):
        pdf_bytes = create_sample_pdf_bytes()
        data = {
            'resume_pdf': (io.BytesIO(pdf_bytes), 'sample_resume.pdf', 'application/pdf')
        }
        response = self.client.post('/api/extract-resume', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertTrue(res_json.get('success'))
        self.assertIn("John Doe", res_json.get('resume_text', ''))

    def test_no_file_provided(self):
        response = self.client.post('/api/extract-resume', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        res_json = response.get_json()
        self.assertFalse(res_json.get('success'))
        self.assertEqual(res_json.get('message'), "Only PDF files are alowed")

    def test_non_pdf_file(self):
        data = {
            'resume_pdf': (io.BytesIO(b"Hello world"), 'resume.txt', 'text/plain')
        }
        response = self.client.post('/api/extract-resume', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        res_json = response.get_json()
        self.assertFalse(res_json.get('success'))
        self.assertEqual(res_json.get('message'), "Only PDF files are alowed")

    def test_invalid_pdf_content(self):
        data = {
            'resume_pdf': (io.BytesIO(b"Not a valid pdf structure"), 'corrupted.pdf', 'application/pdf')
        }
        response = self.client.post('/api/extract-resume', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        res_json = response.get_json()
        self.assertFalse(res_json.get('success'))
        self.assertEqual(res_json.get('message'), "Could not extract text from PDF")

if __name__ == '__main__':
    unittest.main()
