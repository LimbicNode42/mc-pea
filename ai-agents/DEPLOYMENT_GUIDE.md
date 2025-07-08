# MC-PEA AI Agents Deployment Guide

## 🚀 Quick Start

### Development Mode
```bash
# 1. Install dependencies
cd ai-agents
pip install -r requirements.txt

# 2. Set environment variables
export ANTHROPIC_API_KEY="your_api_key_here"

# 3. Run the application
streamlit run interfaces/mcp_server_generator.py
```

### Production Deployment with Docker

#### Option 1: Docker Compose (Recommended)
```bash
# 1. Copy and configure environment variables
cp .env.ai-agents.example .env
# Edit .env with your actual API keys

# 2. Build and run with Docker Compose
docker-compose -f docker-compose.ai-agents.yml up -d

# 3. Access the application
# http://localhost:8501
```

#### Option 2: Direct Docker Build
```bash
# 1. Build the image
docker build -f Dockerfile.ai-agents -t mc-pea-ai-agents .

# 2. Run with environment variables
docker run -d \
  --name mc-pea-ai-agents \
  -p 8501:8501 \
  -e ANTHROPIC_API_KEY="your_api_key_here" \
  mc-pea-ai-agents
```

## 🔒 Security Best Practices

### Environment Variables
- **Never commit API keys to version control**
- Use `.env` files for local development
- Use container orchestration secrets for production
- Set `ANTHROPIC_API_KEY` environment variable

### Docker Security
- Application runs as non-root user (mcpea:1000)
- Minimal base image (python:3.11-slim)
- Health checks included
- Resource limits configured

## 🏗️ Production Deployment Options

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mc-pea-ai-agents
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mc-pea-ai-agents
  template:
    metadata:
      labels:
        app: mc-pea-ai-agents
    spec:
      containers:
      - name: mc-pea-ai-agents
        image: mc-pea-ai-agents:latest
        ports:
        - containerPort: 8501
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-agents-secrets
              key: anthropic-api-key
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2
            memory: 2Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mc-pea-ai-agents-service
spec:
  selector:
    app: mc-pea-ai-agents
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

### AWS ECS
```json
{
  "family": "mc-pea-ai-agents",
  "containerDefinitions": [
    {
      "name": "mc-pea-ai-agents",
      "image": "your-registry/mc-pea-ai-agents:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ANTHROPIC_API_KEY",
          "value": "from-secrets-manager"
        }
      ],
      "memory": 2048,
      "cpu": 1024
    }
  ]
}
```

## 📊 Monitoring and Logging

### Health Checks
The application includes built-in health checks:
- HTTP endpoint: `/_stcore/health`
- Docker health check configured
- Kubernetes liveness/readiness probes supported

### Logging
- Application logs to stdout/stderr
- Structured logging with configurable levels
- Set `LOG_LEVEL` environment variable (debug, info, warn, error)

### Metrics
- Streamlit provides built-in metrics
- Custom metrics can be added via Plotly visualizations
- Resource usage monitoring via container metrics

## 🔧 Configuration Options

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude access | Required |
| `STREAMLIT_SERVER_PORT` | Port for Streamlit server | 8501 |
| `STREAMLIT_SERVER_ADDRESS` | Server bind address | 0.0.0.0 |
| `NODE_ENV` | Environment mode | development |
| `LOG_LEVEL` | Logging level | info |

### Persistent Data
Mount volumes for persistent data:
```bash
docker run -v ./output:/app/output mc-pea-ai-agents
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `ANTHROPIC_API_KEY` is set
   - Check environment variable spelling
   - Verify API key is valid

2. **Port Already in Use**
   - Change `STREAMLIT_SERVER_PORT` environment variable
   - Use different host port: `-p 8502:8501`

3. **Memory Issues**
   - Increase Docker memory limits
   - Monitor resource usage
   - Consider horizontal scaling

### Debug Mode
```bash
# Run with debug logging
docker run -e LOG_LEVEL=debug mc-pea-ai-agents
```

## 📝 Development Notes

### Local Development
- Use virtual environment: `python -m venv venv`
- Install dev dependencies: `pip install -r requirements.txt`
- Run tests: `python -m pytest`

### Code Structure
- `ai-agents/interfaces/` - Streamlit UI components
- `ai-agents/core/` - Core agent framework
- `ai-agents/agents/` - Individual agent implementations
- `ai-agents/workflows/` - Business logic workflows
- `ai-agents/tools/` - Utility functions

### Adding New Features
1. Follow the agent pattern in `ai-agents/agents/`
2. Add workflow definitions in `ai-agents/workflows/`
3. Update UI components in `ai-agents/interfaces/`
4. Add tests in appropriate test files

## 🚀 Next Steps

1. **Production Deployment**: Deploy to your preferred platform
2. **Monitoring**: Set up application monitoring
3. **Scaling**: Configure auto-scaling based on usage
4. **Security**: Implement additional security measures
5. **CI/CD**: Set up automated deployment pipelines
