import os
import json
import io
import PyPDF2
from typing import List
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class JobMatchAnalysis(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    matching_skills: List[str]
    missing_skills: List[str]
    experience_match: str
    gaps: List[str]
    recommendations: List[str]

class ImprovedSection(BaseModel):
    section: str = Field(description="Name or title of the resume section")
    suggestion: str = Field(description="Actionable suggestion to improve wording, clarity, presentation of existing experience, or what to learn/add next based on gaps and recommendations without inventing fake facts")

class ResumeImprovementResponse(BaseModel):
    improved_sections: List[ImprovedSection]

class MatchExplanation(BaseModel):
    explanation: str = Field(description="A clear, plain-language explanation of why the match score is what it is, grounded only in the provided resume, job description, and analysis. Do not invent facts.")

load_dotenv()

app = Flask(__name__)

# Initialize official Google GenAI Client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
@app.route('/api/ai/test', methods=['GET'])
def test_gemini():
    try:
        current_key = os.getenv("GEMINI_API_KEY")
        if not current_key:
            return jsonify({
                "success": False,
                "message": "gemini api connection failed"
            }), 500

        genai_client = client if client is not None else genai.Client(api_key=current_key)
        # Minimal real Gemini API request
        _ = genai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents="ping"
        )

        return jsonify({
            "success": True,
            "message": "gemini api connection working"
        }), 200
    except Exception:
        return jsonify({
            "success": False,
            "message": "gemini api connection failed"
        }), 500

@app.route('/api/extract-resume', methods=['POST'])
def extract_resume():
    if 'resume_pdf' not in request.files:
        return jsonify({
            "success": False,
            "message": "Only PDF files are alowed"
        }), 400

    file = request.files['resume_pdf']

    if not file or not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({
            "success": False,
            "message": "Only PDF files are alowed"
        }), 400

    try:
        pdf_bytes = file.read()
        if not pdf_bytes:
            return jsonify({
                "success": False,
                "message": "Could not extract text from PDF"
            }), 400

        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

        extracted_text = extracted_text.strip()
        if not extracted_text:
            return jsonify({
                "success": False,
                "message": "Could not extract text from PDF"
            }), 400

        return jsonify({
            "success": True,
            "resume_text": extracted_text
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Could not extract text from PDF"
        }), 400

@app.route('/api/analyze', methods=['POST'])

def analyze_job_match():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "resume and job_description are required"
        }), 400

    resume = data.get("resume")
    job_description = data.get("job_description")

    # Validation: resume and job_description required, non-whitespace string
    if not resume or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "resume is required and must contain non-whitespace text"
        }), 400

    if not job_description or not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "success": False,
            "message": "job_description is required and must contain non-whitespace text"
        }), 400

    prompt = f"""you are an ai job matching assistant.

compare the candidate's resume against the supplies job description.

evaluate only information explicitly present in the supplies resume and job description

do not invent:
-skills
-work expeience
-education
-certification
-projects

return a match analysis containing:
-match_score:integer from 0 to 100
-matching_skills:array of strings
-missing_skills:array of strings
-experience_match:short string
-gaps:array of strings
-recommendations:array of string

the recommendations must be practical and based only on the identified gaps:

Return a valid JSON object with exactly these fields:
{{
  "match_score": 0,
  "matching_skills": [],
  "missing_skills": [],
  "experience_match": "",
  "gaps": [],
  "recommendations": []
}}

Resume:
{resume.strip()}

Job Description:
{job_description.strip()}
"""

    try:
        current_key = os.getenv("GEMINI_API_KEY")
        if not current_key:
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502

        genai_client = client if client is not None else genai.Client(api_key=current_key)
        response = genai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobMatchAnalysis,
            ),
        )

        parsed_output = None
        if hasattr(response, 'parsed') and isinstance(response.parsed, JobMatchAnalysis):
            parsed_output = response.parsed
        elif getattr(response, 'text', None):
            try:
                if hasattr(JobMatchAnalysis, 'model_validate_json'):
                    parsed_output = JobMatchAnalysis.model_validate_json(response.text.strip())
                else:
                    parsed_output = JobMatchAnalysis.parse_raw(response.text.strip())
            except Exception:
                raw_json = json.loads(response.text.strip())
                if hasattr(JobMatchAnalysis, 'model_validate'):
                    parsed_output = JobMatchAnalysis.model_validate(raw_json)
                else:
                    parsed_output = JobMatchAnalysis.parse_obj(raw_json)

        if not parsed_output or not isinstance(parsed_output, JobMatchAnalysis):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502

        # Validate types and values
        if not isinstance(parsed_output.match_score, int) or isinstance(parsed_output.match_score, bool):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502
        if not isinstance(parsed_output.matching_skills, list) or not all(isinstance(x, str) for x in parsed_output.matching_skills):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502
        if not isinstance(parsed_output.missing_skills, list) or not all(isinstance(x, str) for x in parsed_output.missing_skills):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502
        if not isinstance(parsed_output.experience_match, str):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502
        if not isinstance(parsed_output.gaps, list) or not all(isinstance(x, str) for x in parsed_output.gaps):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502
        if not isinstance(parsed_output.recommendations, list) or not all(isinstance(x, str) for x in parsed_output.recommendations):
            return jsonify({
                "success": False,
                "message": "AI response validation failed"
            }), 502

        result = {
            "success": True,
            "match_score": parsed_output.match_score,
            "matching_skills": parsed_output.matching_skills,
            "missing_skills": parsed_output.missing_skills,
            "experience_match": parsed_output.experience_match,
            "gaps": parsed_output.gaps,
            "recommendations": parsed_output.recommendations
        }

        return jsonify(result), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "AI response validation failed"
        }), 502

@app.route('/api/improve-resume', methods=['POST'])
def improve_resume():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "resume, gaps, and recommendations are required"
        }), 400

    resume = data.get("resume")
    gaps = data.get("gaps")
    recommendations = data.get("recommendations")

    if not resume or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "resume is required and must contain non-whitespace text"
        }), 400

    if gaps is None or not isinstance(gaps, list):
        return jsonify({
            "success": False,
            "message": "gaps must be a list"
        }), 400

    if recommendations is None or not isinstance(recommendations, list):
        return jsonify({
            "success": False,
            "message": "recommendations must be a list"
        }), 400

    prompt = f"""You are an expert AI resume advisor.

Review the candidate's existing resume along with the identified gaps and recommendations.
Suggest improvements to the resume based ONLY on the provided gaps and recommendations.

CRITICAL RULES:
- Never invent or fabricate:
  - work experience
  - projects
  - skills
  - certifications
  - education
  - achievements
- The AI may:
  - improve wording
  - improve clarity
  - suggest where existing experience could be presented better
  - suggest what the student should learn or add in the future
- Do not rewrite the entire resume automatically; provide structured section suggestions.

Candidate Resume:
{resume.strip()}

Gaps:
{json.dumps(gaps, indent=2)}

Recommendations:
{json.dumps(recommendations, indent=2)}
"""

    try:
        current_key = os.getenv("GEMINI_API_KEY")
        if not current_key:
            return jsonify({
                "success": False,
                "message": "Resume improvement failed"
            }), 502

        genai_client = client if client is not None else genai.Client(api_key=current_key)
        response = genai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResumeImprovementResponse,
            ),
        )

        parsed_output = None
        if hasattr(response, 'parsed') and isinstance(response.parsed, ResumeImprovementResponse):
            parsed_output = response.parsed
        elif getattr(response, 'text', None):
            try:
                if hasattr(ResumeImprovementResponse, 'model_validate_json'):
                    parsed_output = ResumeImprovementResponse.model_validate_json(response.text.strip())
                else:
                    parsed_output = ResumeImprovementResponse.parse_raw(response.text.strip())
            except Exception:
                raw_json = json.loads(response.text.strip())
                if hasattr(ResumeImprovementResponse, 'model_validate'):
                    parsed_output = ResumeImprovementResponse.model_validate(raw_json)
                else:
                    parsed_output = ResumeImprovementResponse.parse_obj(raw_json)

        if not parsed_output or not isinstance(parsed_output, ResumeImprovementResponse):
            return jsonify({
                "success": False,
                "message": "Resume improvement failed"
            }), 502

        if not isinstance(parsed_output.improved_sections, list):
            return jsonify({
                "success": False,
                "message": "Resume improvement failed"
            }), 502

        improved_sections_data = []
        for sec in parsed_output.improved_sections:
            if not isinstance(sec.section, str) or not isinstance(sec.suggestion, str):
                return jsonify({
                    "success": False,
                    "message": "Resume improvement failed"
                }), 502
            improved_sections_data.append({
                "section": sec.section,
                "suggestion": sec.suggestion
            })

        result = {
            "success": True,
            "improved_sections": improved_sections_data
        }

        return jsonify(result), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "Resume improvement failed"
        }), 502

@app.route('/api/explain-match', methods=['POST'])
def explain_match():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "resume, job_description, and analysis are required"
        }), 400

    resume = data.get("resume")
    job_description = data.get("job_description")
    analysis = data.get("analysis")

    if not resume or not isinstance(resume, str) or not resume.strip():
        return jsonify({
            "success": False,
            "message": "resume is required and must contain non-whitespace text"
        }), 400

    if not job_description or not isinstance(job_description, str) or not job_description.strip():
        return jsonify({
            "success": False,
            "message": "job_description is required and must contain non-whitespace text"
        }), 400

    if not analysis or not isinstance(analysis, dict):
        return jsonify({
            "success": False,
            "message": "analysis must be a JSON object"
        }), 400

    # Validate required analysis fields
    required_analysis_fields = ["match_score", "matching_skills", "missing_skills", "experience_match", "gaps", "recommendations"]
    for field in required_analysis_fields:
        if field not in analysis:
            return jsonify({
                "success": False,
                "message": f"analysis.{field} is required"
            }), 400

    if not isinstance(analysis["match_score"], int) or isinstance(analysis["match_score"], bool):
        return jsonify({
            "success": False,
            "message": "analysis.match_score must be an integer"
        }), 400

    for list_field in ["matching_skills", "missing_skills", "gaps", "recommendations"]:
        if not isinstance(analysis[list_field], list):
            return jsonify({
                "success": False,
                "message": f"analysis.{list_field} must be a list"
            }), 400

    if not isinstance(analysis["experience_match"], str):
        return jsonify({
            "success": False,
            "message": "analysis.experience_match must be a string"
        }), 400

    prompt = f"""You are a friendly AI career advisor helping a beginner understand their job application results.

A candidate's resume was evaluated against a job description and produced the analysis below.
Write a clear, beginner-friendly explanation of WHY the candidate received this match score.

Your explanation MUST:
1. Be easy to understand for someone with no HR or technical recruiting background.
2. Mention the candidate's STRONGEST matching skills from the analysis.
3. Explain the MOST IMPORTANT gaps that lowered the score.
4. Suggest what the candidate could realistically improve or learn next.

STRICT RULES:
- Base your explanation ONLY on the provided resume, job description, and analysis.
- Do NOT recalculate or change the score.
- Do NOT invent skills, experience, projects, certifications, or education that are not in the resume.
- Do NOT repeat the raw lists — explain them in plain English.

---

Resume:
{resume.strip()}

Job Description:
{job_description.strip()}

Analysis:
- Match Score: {analysis["match_score"]}%
- Matching Skills: {json.dumps(analysis["matching_skills"])}
- Missing Skills: {json.dumps(analysis["missing_skills"])}
- Experience Match: {analysis["experience_match"]}
- Gaps: {json.dumps(analysis["gaps"])}
- Recommendations: {json.dumps(analysis["recommendations"])}
"""

    try:
        current_key = os.getenv("GEMINI_API_KEY")
        if not current_key:
            return jsonify({
                "success": False,
                "message": "match explanation failed"
            }), 502

        genai_client = client if client is not None else genai.Client(api_key=current_key)
        response = genai_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MatchExplanation,
            ),
        )

        parsed_output = None
        if hasattr(response, 'parsed') and isinstance(response.parsed, MatchExplanation):
            parsed_output = response.parsed
        elif getattr(response, 'text', None):
            try:
                if hasattr(MatchExplanation, 'model_validate_json'):
                    parsed_output = MatchExplanation.model_validate_json(response.text.strip())
                else:
                    parsed_output = MatchExplanation.parse_raw(response.text.strip())
            except Exception:
                raw_json = json.loads(response.text.strip())
                if hasattr(MatchExplanation, 'model_validate'):
                    parsed_output = MatchExplanation.model_validate(raw_json)
                else:
                    parsed_output = MatchExplanation.parse_obj(raw_json)

        if not parsed_output or not isinstance(parsed_output, MatchExplanation):
            return jsonify({
                "success": False,
                "message": "match explanation failed"
            }), 502

        if not isinstance(parsed_output.explanation, str) or not parsed_output.explanation.strip():
            return jsonify({
                "success": False,
                "message": "match explanation failed"
            }), 502

        return jsonify({
            "success": True,
            "explanation": parsed_output.explanation
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "message": "match explanation failed"
        }), 502

if __name__ == '__main__':
    app.run(debug=True, port=5000)

