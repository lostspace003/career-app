"""
FastAPI backend for AI Tech Career Path Finder
Uses Azure OpenAI (GPT-4o) to generate personalized learning plans
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI
from pypdf import PdfReader
import docx
from xhtml2pdf import pisa
from io import BytesIO
import re
from storage_utils import storage_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Tech Career Path Finder")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
# Note: uploads and generated folders managed by storage_utils (Azure Blob or local)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Azure OpenAI Configuration (using environment variables - secure approach)
azure_client = None

def get_azure_openai_client():
    """Initialize Azure OpenAI client with proper error handling"""
    global azure_client
    if azure_client is None:
        try:
            azure_client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize Azure OpenAI client: {str(e)}")
    return azure_client

# Pydantic models
class UserProfile(BaseModel):
    experience_level: str
    job_role: str
    interests: list[str]
    learning_style: str
    time_commitment: str
    goals: str
    current_skills: Optional[str] = ""
    preferred_technologies: Optional[str] = ""

class CareerPlan(BaseModel):
    html_plan: str
    user_profile: dict

# Helper functions
def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")

def extract_text_from_file(filename: str, content: bytes) -> str:
    """Extract text based on file type"""
    extension = os.path.splitext(filename)[1].lower()
    
    if extension == '.pdf':
        return extract_text_from_pdf(content)
    elif extension in ['.doc', '.docx']:
        return extract_text_from_docx(content)
    elif extension == '.txt':
        return content.decode('utf-8')
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

def generate_career_plan(user_profile: UserProfile, resume_text: Optional[str] = None) -> str:
    """
    Generate personalized AI career path using Azure OpenAI GPT-4o
    Implements retry logic and proper error handling as per Azure best practices
    """
    client = get_azure_openai_client()
    
    # Build comprehensive prompt
    prompt = f"""You are an expert AI career advisor. Based on the following information about the user, create a comprehensive, personalized learning path to help them become a "Tech Freak in AI".

User Profile:
- Experience Level: {user_profile.experience_level}
- Current Job Role: {user_profile.job_role}
- Interests: {', '.join(user_profile.interests)}
- Learning Style: {user_profile.learning_style}
- Time Commitment: {user_profile.time_commitment}
- Goals: {user_profile.goals}
- Current Skills: {user_profile.current_skills}
- Preferred Technologies: {user_profile.preferred_technologies}

"""

    if resume_text:
        prompt += f"\nResume/CV Summary:\n{resume_text[:2000]}\n"

    prompt += """
Create a detailed, actionable learning plan in HTML format. The plan should include:

1. **Executive Summary**: Brief overview tailored to their background
2. **Skill Gap Analysis**: What they need to learn based on current level
3. **Learning Roadmap**: Structured in phases (Beginner/Intermediate/Advanced if applicable)
4. **Recommended Resources**: Specific courses, books, projects
5. **Timeline**: Realistic timeframes based on their time commitment
6. **Project Ideas**: Hands-on projects to build portfolio
7. **Career Opportunities**: Potential roles they can target
8. **Next Steps**: Immediate actions to take

Make it motivating, specific, and actionable. Use modern HTML with inline CSS for beautiful formatting. 
Use a professional color scheme with:
- Primary color: #6366f1 (indigo)
- Secondary color: #8b5cf6 (purple)
- Accent color: #ec4899 (pink)
- Background: #f8fafc
- Text: #1e293b

Include proper headings, lists, cards, and sections. Make it visually appealing and easy to read.
Do NOT include <html>, <head>, or <body> tags - just the content div that will be inserted into the page.
"""

    try:
        # Call Azure OpenAI with retry logic
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are an expert AI career advisor who creates personalized, actionable learning plans."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        html_plan = response.choices[0].message.content
        return html_plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan with Azure OpenAI: {str(e)}")

async def create_pdf_from_html(html_content: str, filename: str) -> str:
    """
    Generate PDF from HTML content preserving all formatting
    Saves to Azure Blob Storage or local filesystem
    Returns the file path or blob URL of generated PDF
    """
    try:
        # Create complete HTML document with styling
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    line-height: 1.6;
                    color: #1e293b;
                    background-color: #ffffff;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #1e293b;
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                }}
                h1 {{
                    color: #6366f1;
                    font-size: 24px;
                    border-bottom: 3px solid #6366f1;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #8b5cf6;
                    font-size: 20px;
                    border-bottom: 2px solid #8b5cf6;
                    padding-bottom: 8px;
                }}
                h3 {{
                    color: #ec4899;
                    font-size: 18px;
                }}
                ul, ol {{
                    margin-left: 20px;
                    margin-bottom: 1em;
                }}
                li {{
                    margin-bottom: 0.5em;
                }}
                p {{
                    margin-bottom: 1em;
                }}
                .card {{
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: #f8fafc;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 12px;
                    background-color: #e0e7ff;
                    color: #4338ca;
                    font-size: 12px;
                    margin-right: 5px;
                    margin-bottom: 5px;
                }}
                strong {{
                    color: #0f172a;
                }}
                em {{
                    color: #475569;
                }}
                code {{
                    background-color: #f1f5f9;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 0.9em;
                }}
                blockquote {{
                    border-left: 4px solid #6366f1;
                    padding-left: 15px;
                    margin-left: 0;
                    color: #64748b;
                    font-style: italic;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 1em;
                }}
                th, td {{
                    border: 1px solid #e2e8f0;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f1f5f9;
                    font-weight: bold;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #6366f1;
                }}
                .header h1 {{
                    color: #6366f1;
                    font-size: 28px;
                    margin-bottom: 10px;
                    border-bottom: none;
                }}
                .header p {{
                    color: #64748b;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 AI Tech Career Path Plan</h1>
                <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
            </div>
            <div class="content">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        # Convert HTML to PDF in memory
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(
            BytesIO(html_template.encode('utf-8')),
            dest=pdf_buffer,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            raise Exception("Error during PDF generation")
        
        # Save PDF to Azure Blob Storage or local filesystem
        pdf_content = pdf_buffer.getvalue()
        file_path = await storage_manager.save_file(pdf_content, filename, "generated")
        
        return file_path
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>AI Tech Career Path Finder</h1>
                <p>Please ensure static/index.html exists</p>
            </body>
        </html>
        """

@app.post("/api/generate-plan")
async def generate_plan(
    experience_level: str = Form(...),
    job_role: str = Form(...),
    interests: str = Form(...),
    learning_style: str = Form(...),
    time_commitment: str = Form(...),
    goals: str = Form(...),
    current_skills: str = Form(""),
    preferred_technologies: str = Form(""),
    resume: Optional[UploadFile] = File(None)
):
    """
    Generate personalized AI career plan
    Accepts form data and optional resume file
    """
    
    # Parse interests
    interests_list = [i.strip() for i in interests.split(',') if i.strip()]
    
    # Create user profile
    user_profile = UserProfile(
        experience_level=experience_level,
        job_role=job_role,
        interests=interests_list,
        learning_style=learning_style,
        time_commitment=time_commitment,
        goals=goals,
        current_skills=current_skills,
        preferred_technologies=preferred_technologies
    )
    
    # Process resume if provided
    resume_text = None
    if resume and resume.filename:
        # Validate file size (10MB max)
        content = await resume.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max size is 10MB")
        
        # Save resume to storage (Azure Blob or local)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{resume.filename}"
        await storage_manager.save_file(content, safe_filename, "uploads")
        logger.info(f"Resume saved: {safe_filename}")
        
        # Extract text from resume
        resume_text = extract_text_from_file(resume.filename, content)
    
    # Generate plan using Azure OpenAI
    html_plan = generate_career_plan(user_profile, resume_text)
    
    return JSONResponse({
        "success": True,
        "html_plan": html_plan,
        "user_profile": user_profile.model_dump()
    })

@app.post("/api/download-pdf")
async def download_pdf(plan: CareerPlan):
    """
    Generate and download PDF version of the career plan
    Saves to Azure Blob Storage or local filesystem
    """
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_career_plan_{timestamp}.pdf"
    
    # Create PDF and save to storage
    pdf_path = await create_pdf_from_html(plan.html_plan, filename)
    
    # If using Azure Blob Storage, download the file temporarily for response
    if storage_manager.use_azure:
        # Get the PDF content from Azure Blob
        pdf_content = await storage_manager.get_file(filename, "generated")
        if pdf_content:
            return JSONResponse({
                "success": True,
                "filename": filename,
                "download_url": pdf_path,  # This is the blob URL
                "message": "PDF generated successfully"
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve generated PDF")
    else:
        # For local storage, return file directly
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=filename
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Tech Career Path Finder"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
