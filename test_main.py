"""
Comprehensive tests for AI Tech Career Path Finder
"""

import pytest
from fastapi.testclient import TestClient
from main import app, get_azure_openai_client, UserProfile
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = TestClient(app)


class TestEnvironmentConfiguration:
    """Test environment variables and configuration"""
    
    def test_env_file_exists(self):
        """Test that .env file exists"""
        assert os.path.exists('.env'), ".env file not found"
    
    def test_azure_openai_endpoint_configured(self):
        """Test Azure OpenAI endpoint is configured"""
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        assert endpoint is not None, "AZURE_OPENAI_ENDPOINT not set"
        assert endpoint.startswith('https://'), "Endpoint should start with https://"
        assert 'openai.azure.com' in endpoint, "Should be an Azure OpenAI endpoint"
    
    def test_azure_openai_api_key_configured(self):
        """Test Azure OpenAI API key is configured"""
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        assert api_key is not None, "AZURE_OPENAI_API_KEY not set"
        assert len(api_key) > 20, "API key seems too short"
        assert api_key != 'your-api-key-here', "API key not updated from example"
    
    def test_azure_openai_deployment_configured(self):
        """Test Azure OpenAI deployment name is configured"""
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        assert deployment is not None, "AZURE_OPENAI_DEPLOYMENT_NAME not set"
        assert deployment == 'gpt-4o', "Expected deployment name to be gpt-4o"
    
    def test_azure_openai_api_version_configured(self):
        """Test Azure OpenAI API version is configured"""
        api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        assert api_version is not None, "AZURE_OPENAI_API_VERSION not set"


class TestAzureOpenAIConnection:
    """Test Azure OpenAI client initialization and connection"""
    
    def test_azure_client_initialization(self):
        """Test that Azure OpenAI client can be initialized"""
        try:
            client = get_azure_openai_client()
            assert client is not None, "Azure OpenAI client should not be None"
        except Exception as e:
            pytest.fail(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def test_azure_client_properties(self):
        """Test Azure OpenAI client has correct properties"""
        client = get_azure_openai_client()
        assert hasattr(client, 'chat'), "Client should have chat attribute"
        assert hasattr(client.chat, 'completions'), "Client should have completions attribute"


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
        assert 'AI Tech Career Path Finder' in response.text
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'AI Tech Career Path Finder' in data['service']
    
    def test_generate_plan_missing_fields(self):
        """Test generate plan endpoint with missing required fields"""
        response = client.post("/api/generate-plan", data={})
        assert response.status_code == 422  # Validation error


class TestUserProfileModel:
    """Test UserProfile Pydantic model"""
    
    def test_user_profile_creation(self):
        """Test creating a valid UserProfile"""
        profile = UserProfile(
            experience_level="intermediate",
            job_role="Software Engineer",
            interests=["Machine Learning", "NLP"],
            learning_style="hands-on",
            time_commitment="10-20-hours",
            goals="Become an ML Engineer"
        )
        assert profile.experience_level == "intermediate"
        assert len(profile.interests) == 2
    
    def test_user_profile_optional_fields(self):
        """Test UserProfile with optional fields"""
        profile = UserProfile(
            experience_level="beginner",
            job_role="Student",
            interests=["AI"],
            learning_style="video-courses",
            time_commitment="5-10-hours",
            goals="Learn AI",
            current_skills="Python, JavaScript",
            preferred_technologies="TensorFlow"
        )
        assert profile.current_skills == "Python, JavaScript"
        assert profile.preferred_technologies == "TensorFlow"


class TestDirectoryStructure:
    """Test required directories exist"""
    
    def test_static_directory_exists(self):
        """Test static directory exists"""
        assert os.path.exists('static'), "static directory should exist"
    
    def test_index_html_exists(self):
        """Test index.html exists in static directory"""
        assert os.path.exists('static/index.html'), "static/index.html should exist"
    
    def test_uploads_directory_exists(self):
        """Test uploads directory exists or is created"""
        assert os.path.exists('uploads'), "uploads directory should exist"
    
    def test_generated_directory_exists(self):
        """Test generated directory exists or is created"""
        assert os.path.exists('generated'), "generated directory should exist"


class TestAzureOpenAIIntegration:
    """Test actual Azure OpenAI integration (requires valid credentials)"""
    
    @pytest.mark.integration
    def test_simple_completion(self):
        """Test a simple completion with Azure OpenAI"""
        try:
            azure_client = get_azure_openai_client()
            response = azure_client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, Azure OpenAI!' and nothing else."}
                ],
                max_tokens=50
            )
            
            assert response is not None, "Response should not be None"
            assert len(response.choices) > 0, "Should have at least one choice"
            assert response.choices[0].message.content is not None, "Should have content"
            print(f"\n✓ Azure OpenAI Response: {response.choices[0].message.content}")
            
        except Exception as e:
            pytest.fail(f"Azure OpenAI integration test failed: {str(e)}")
    
    @pytest.mark.integration
    def test_generate_plan_endpoint_integration(self):
        """Test full plan generation with real Azure OpenAI call"""
        form_data = {
            "experience_level": "intermediate",
            "job_role": "Software Developer",
            "interests": "Machine Learning, Deep Learning",
            "learning_style": "hands-on",
            "time_commitment": "10-20-hours",
            "goals": "Become an AI/ML Engineer and build production ML systems",
            "current_skills": "Python, JavaScript, SQL",
            "preferred_technologies": "PyTorch, TensorFlow"
        }
        
        try:
            response = client.post("/api/generate-plan", data=form_data)
            
            # Print response details for debugging
            print(f"\n✓ Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"✗ Response: {response.text}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data['success'] == True, "Success should be True"
            assert 'html_plan' in data, "Should contain html_plan"
            assert 'user_profile' in data, "Should contain user_profile"
            assert len(data['html_plan']) > 100, "HTML plan should be substantial"
            
            print(f"✓ Plan generated successfully!")
            print(f"✓ Plan length: {len(data['html_plan'])} characters")
            
        except Exception as e:
            pytest.fail(f"Full integration test failed: {str(e)}")


def test_print_configuration():
    """Helper test to print current configuration (for debugging)"""
    print("\n" + "="*60)
    print("CURRENT CONFIGURATION")
    print("="*60)
    print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"API Key: {'*' * 40}{os.getenv('AZURE_OPENAI_API_KEY', '')[-8:]}")
    print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
    print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])