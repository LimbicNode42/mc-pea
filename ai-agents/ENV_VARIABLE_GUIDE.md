# Environment Variable Configuration Guide

## 🔧 How Environment Variables Work in Different Scenarios

### 1. **Development Mode (Local)**
```bash
# Option 1: Create .env file (recommended for development)
echo 'ANTHROPIC_API_KEY=your_api_key_here' > ai-agents/.env

# Option 2: Set environment variable directly
export ANTHROPIC_API_KEY="your_api_key_here"

# Run the application
cd ai-agents
streamlit run interfaces/server_generator.py
```

### 2. **Docker Container**
```bash
# Option 1: Environment variable at runtime
docker run -e ANTHROPIC_API_KEY="your_api_key_here" mc-pea-ai-agents

# Option 2: Using .env file with Docker
docker run --env-file .env mc-pea-ai-agents

# Option 3: Docker Compose (recommended for production)
docker-compose -f docker-compose.ai-agents.yml up
```

### 3. **Production Deployment**
```bash
# Kubernetes Secret
kubectl create secret generic ai-agents-secrets \
  --from-literal=anthropic-api-key=your_api_key_here

# AWS ECS Task Definition
{
  "environment": [
    {
      "name": "ANTHROPIC_API_KEY",
      "value": "your_api_key_here"
    }
  ]
}

# Azure Container Instance
az container create \
  --environment-variables ANTHROPIC_API_KEY=your_api_key_here
```

## 🔍 Environment Variable Loading Order

The application loads environment variables in this priority order:

1. **System Environment Variables** (highest priority)
2. **Docker environment variables** (`-e` flag or `environment:` in docker-compose)
3. **`.env` file** (loaded by `python-dotenv`)
4. **Streamlit UI input** (fallback, lowest priority)

## 🔒 Security Best Practices

### ✅ **DO:**
- Use `.env` files for local development
- Use container orchestration secrets for production
- Set environment variables in CI/CD pipelines
- Use cloud provider secret managers (AWS Secrets Manager, Azure Key Vault, etc.)

### ❌ **DON'T:**
- Commit `.env` files to version control
- Hardcode API keys in source code
- Log or print API keys in application logs
- Use plain text files for production secrets

## 🚀 Deployment Examples

### Local Development with .env
```bash
# Create .env file
cat > ai-agents/.env << EOF
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
NODE_ENV=development
LOG_LEVEL=debug
EOF

# Run application
cd ai-agents
streamlit run interfaces/server_generator.py
```

### Docker with Environment Variables
```bash
# Build image
docker build -f Dockerfile.ai-agents -t mc-pea-ai-agents .

# Run with environment variable
docker run -d \
  --name mc-pea-ai-agents \
  -p 8501:8501 \
  -e ANTHROPIC_API_KEY="sk-ant-api03-your-key-here" \
  mc-pea-ai-agents
```

### Docker Compose with .env
```yaml
# docker-compose.ai-agents.yml
version: '3.8'
services:
  mc-pea-ai-agents:
    build:
      context: .
      dockerfile: Dockerfile.ai-agents
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports:
      - "8501:8501"
```

```bash
# Create .env file for docker-compose
echo 'ANTHROPIC_API_KEY=sk-ant-api03-your-key-here' > .env

# Run with docker-compose
docker-compose -f docker-compose.ai-agents.yml up -d
```

### Kubernetes with Secrets
```yaml
# Create secret
apiVersion: v1
kind: Secret
metadata:
  name: ai-agents-secrets
type: Opaque
data:
  anthropic-api-key: c2stYW50LWFwaTAzLXlvdXIta2V5LWhlcmU=  # base64 encoded

---
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mc-pea-ai-agents
spec:
  template:
    spec:
      containers:
      - name: mc-pea-ai-agents
        image: mc-pea-ai-agents:latest
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-agents-secrets
              key: anthropic-api-key
```

## 🛠️ Troubleshooting

### Environment Variable Not Found
```bash
# Check if variable is set
echo $ANTHROPIC_API_KEY

# Check from Python
python -c "import os; print(os.getenv('ANTHROPIC_API_KEY', 'NOT_FOUND'))"

# Check with dotenv
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY', 'NOT_FOUND'))"
```

### Docker Environment Issues
```bash
# Check container environment
docker exec -it mc-pea-ai-agents env | grep ANTHROPIC

# Check container logs
docker logs mc-pea-ai-agents
```

### Streamlit Environment Variables
```python
# In Streamlit app, you can debug with:
import os
from dotenv import load_dotenv

load_dotenv()
st.write("Environment variables:")
st.write(f"ANTHROPIC_API_KEY: {'Found' if os.getenv('ANTHROPIC_API_KEY') else 'Not found'}")
```

## 📝 Environment Variable Validation

The application includes built-in validation:

```python
# In server_generator.py
def validate_environment():
    """Validate required environment variables."""
    required_vars = ['ANTHROPIC_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True
```

## 🔄 Development vs Production

### Development Setup
```bash
# Use .env file for convenience
cp .env.ai-agents.example ai-agents/.env
# Edit ai-agents/.env with your API keys

# Run locally
cd ai-agents
streamlit run interfaces/server_generator.py
```

### Production Setup
```bash
# Use environment variables (no .env file)
export ANTHROPIC_API_KEY="your_production_key"
export NODE_ENV="production"
export LOG_LEVEL="info"

# Run with production settings
streamlit run interfaces/server_generator.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.headless true
```

This approach ensures security best practices while providing flexibility for different deployment scenarios.
