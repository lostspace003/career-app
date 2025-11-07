# AI Tech Career Path Finder 🤖

A comprehensive web application that helps users create personalized AI learning paths using Azure OpenAI (GPT-4o). The app collects user information through an intelligent questionnaire, optionally processes their resume, and generates a beautiful, customized career roadmap.

## Features ✨

- **Smart Questionnaire**: Multi-step form that captures:
  - Experience level and current role
  - AI interests and career goals
  - Learning preferences and time commitment
  - Current skills and preferred technologies

- **Resume Processing**: Upload and analyze resumes in multiple formats (PDF, DOC, DOCX, TXT)

- **AI-Powered Plan Generation**: Uses Azure OpenAI GPT-4o to create personalized learning paths

- **Beautiful UI**: Modern, responsive design built with Tailwind CSS

- **PDF Export**: Download your career plan as a beautifully formatted PDF with all HTML styling preserved

- **Refresh Functionality**: Easy restart to create new plans

## Tech Stack 🛠️

### Backend
- **FastAPI**: Modern Python web framework
- **Azure OpenAI**: GPT-4o for intelligent plan generation
- **xhtml2pdf**: HTML to PDF conversion with formatting preservation
- **pypdf**: Resume parsing (PDF files)
- **python-docx**: Resume parsing (DOCX files)

### Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **Vanilla JavaScript**: Interactive UI
- **Font Awesome**: Icons

## Prerequisites 📋

- Python 3.8+
- Azure OpenAI account with GPT-4o deployment
- pip (Python package manager)

## Installation 🚀

1. **Clone the repository**
   ```bash
   cd path-finder
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example env file
   cp .env.example .env
   ```

   Edit `.env` and add your Azure OpenAI credentials:
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key-here
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

## Getting Azure OpenAI Credentials 🔑

1. Go to [Azure Portal](https://portal.azure.com/)
2. Create an Azure OpenAI resource
3. Deploy the GPT-4o model
4. Get your endpoint and API key from the resource's "Keys and Endpoint" section
5. Note your deployment name

## Running the Application 🏃

1. **Start the server**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the application**
   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Project Structure 📁

```
path-finder/
│
├── main.py                 # FastAPI backend application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore file
├── README.md              # This file
│
├── static/                # Static files
│   └── index.html         # Frontend UI
│
├── uploads/               # Uploaded resume files (auto-created)
└── generated/             # Generated PDF files (auto-created)
```

## API Endpoints 📡

### `GET /`
Serves the main HTML page

### `POST /api/generate-plan`
Generates a personalized AI career plan

**Form Data:**
- `experience_level` (required)
- `job_role` (required)
- `interests` (required)
- `learning_style` (required)
- `time_commitment` (required)
- `goals` (required)
- `current_skills` (optional)
- `preferred_technologies` (optional)
- `resume` (optional file)

**Response:**
```json
{
  "success": true,
  "html_plan": "<div>...</div>",
  "user_profile": {...}
}
```

### `POST /api/download-pdf`
Generates and downloads a PDF version of the career plan

**Request Body:**
```json
{
  "html_plan": "<div>...</div>",
  "user_profile": {...}
}
```

**Response:** PDF file download

### `GET /health`
Health check endpoint

## Usage Guide 📖

1. **Fill out the questionnaire** through the 4-step form:
   - Step 1: Experience & Current Role
   - Step 2: Interests & Goals
   - Step 3: Learning Preferences
   - Step 4: Resume Upload (optional)

2. **Submit the form** to generate your personalized career plan

3. **Review your plan** with detailed sections including:
   - Executive Summary
   - Skill Gap Analysis
   - Learning Roadmap
   - Recommended Resources
   - Timeline
   - Project Ideas
   - Career Opportunities
   - Next Steps

4. **Download as PDF** for offline reference

5. **Start Over** anytime with the refresh button

## Security Best Practices 🔒

This application follows Azure security best practices:

- ✅ Environment variables for sensitive credentials
- ✅ No hardcoded API keys
- ✅ File size validation (10MB max)
- ✅ File type validation
- ✅ Proper error handling
- ✅ CORS configuration
- ✅ Input validation

## Customization 🎨

### Modify the AI Prompt
Edit the `generate_career_plan()` function in `main.py` to customize the plan structure and content.

### Change Color Scheme
Update the color variables in `static/index.html` (search for color codes like `#6366f1`).

### Adjust File Limits
Modify `MAX_FILE_SIZE` and `ALLOWED_FILE_TYPES` in `.env`.

## Troubleshooting 🔧

### Issue: "Failed to initialize Azure OpenAI client"
- Verify your `.env` file has correct Azure OpenAI credentials
- Check that your Azure OpenAI resource is active
- Ensure your deployment name matches exactly

### Issue: "File too large"
- Maximum file size is 10MB
- Compress your resume or use a different format

### Issue: "Unsupported file type"
- Only PDF, DOC, DOCX, and TXT files are supported
- Convert your resume to a supported format

## Deployment 🌐

### Deploy to Azure App Service (Free Tier)

This application is ready for Azure deployment with:
- ✅ Azure Blob Storage integration for file management
- ✅ Managed Identity for secure authentication
- ✅ GitHub Actions CI/CD pipeline
- ✅ Free tier compatibility

**See detailed deployment instructions**: [DEPLOYMENT.md](DEPLOYMENT.md)

**Quick deployment guide**: [QUICK_DEPLOY.md](QUICK_DEPLOY.md)

### Key Features for Production

1. **Azure Blob Storage**: Files stored in `uploads` and `generated` containers
2. **Managed Identity**: No hardcoded credentials, uses Azure AD authentication
3. **Automatic Scaling**: Ready to scale when needed
4. **CI/CD**: Push to GitHub → Automatic deployment to Azure
5. **Environment Variables**: Secure configuration via Azure App Settings

### Deploy to Other Platforms

- **Heroku**: Use the included `Procfile`
- **Docker**: Create a Dockerfile based on Python 3.11
- **AWS EC2**: Run as a systemd service

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the MIT License.

## Support 💬

For issues and questions:
- Open an issue on GitHub
- Check Azure OpenAI documentation
- Review FastAPI documentation

## Acknowledgments 🙏

- Built with FastAPI and Tailwind CSS
- Powered by Azure OpenAI GPT-4o
- Icons by Font Awesome

---

**Made with ❤️ for aspiring AI enthusiasts**
