# AI Job Match Assistant

## Project Overview
AI Job Match Assistant is a web application designed to help job seekers compare their resumes against job descriptions. It leverages the Google Gemini API to analyze the match, highlight missing skills, identify gaps, and provide actionable recommendations. Furthermore, it offers capabilities to suggest resume improvements and explain the match results in a beginner-friendly way.

## Features
- **PDF Resume Upload**: Easily extract text from PDF resumes using the built-in parser.
- **Match Analysis**: Compares a resume to a job description and generates a match score, matching/missing skills, experience match, gaps, and recommendations.
- **Improve My Resume**: Suggests section-by-section improvements for the uploaded resume based on identified gaps.
- **Explain My Match**: Provides a plain-language explanation of why a particular match score was given and what to focus on next.

## Tech Stack
- **Backend**: Python 3, Flask
- **AI Integration**: Google GenAI (`google-genai`), Gemini 3.6 Flash model
- **PDF Processing**: PyPDF2
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Environment Management**: `python-dotenv`

## Project Structure
```text
ai-job-match/
├── .env                    # Environment variables (not tracked in git)
├── .gitignore              # Git ignore file
├── app.py                  # Main Flask application and API endpoints
├── create_pdf.py           # Helper script for PDF generation/testing
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Frontend UI
└── test_pdf_endpoint.py    # Test script for the PDF extraction endpoint
```

## Setup and Environment Configuration
1. **Clone the repository** (if applicable) and navigate to the project directory:
   ```bash
   cd ai-job-match
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root of the project and add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## How to Run
Start the Flask development server by running:
```bash
python app.py
```
The application will be accessible at `http://localhost:5000` or `http://127.0.0.1:5000`.

## How to Use
1. Open the application in your web browser.
2. **Upload PDF or Paste Resume**: Click "Upload PDF" to extract text from your resume, or paste the text directly into the "Resume" textarea.
3. **Paste Job Description**: Paste the target job description into the "Job Description" textarea.
4. **Analyze Match**: Click "Analyze Match" to get your match score, skills analysis, and recommendations.
5. **Improve or Explain**: Once the analysis is complete, you can click "Improve My Resume" for targeted resume tweaks, or "Explain My Match" for a clear breakdown of your score.

## API Endpoints
- `GET /` - Serves the frontend application (`index.html`).
- `GET /api/test` or `GET /api/ai/test` - Verifies the Gemini API connection.
- `POST /api/extract-resume` - Accepts a `multipart/form-data` request with a `resume_pdf` file and returns the extracted text.
- `POST /api/analyze` - Accepts JSON with `resume` and `job_description` and returns a structured match analysis.
- `POST /api/improve-resume` - Accepts JSON with `resume`, `gaps`, and `recommendations` and returns suggested resume improvements.
- `POST /api/explain-match` - Accepts JSON with `resume`, `job_description`, and the `analysis` result object, returning a plain-language explanation.

## Security Note About API Keys
**Do not hardcode your API keys** in the source code or commit the `.env` file to version control. The `.env` file should be included in your `.gitignore` file. Always keep your `GEMINI_API_KEY` secure and rotate it if you suspect it has been compromised.

## Future Improvements
- **Database Integration**: Store user profiles, past resumes, and analysis history.
- **Authentication**: Add user sign-up/login to save sessions across devices.
- **Advanced UI/UX**: Migrate the frontend to a modern framework (e.g., React, Vue, or Next.js) for a more interactive experience.
- **Export Results**: Allow users to download their match reports or improved resumes as PDFs.
