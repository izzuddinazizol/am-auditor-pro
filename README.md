# AM Auditor Pro

AI-powered conversation auditing for Account Management teams. Analyze conversations and get objective, actionable feedback to improve performance.

## 🚀 Features

- **Multi-format Support**: Audio, video, PDF, images, and text files
- **AI-Powered Analysis**: Uses Google Gemini for intelligent conversation evaluation
- **Multi-language Support**: English, Malay, Mandarin, Cantonese
- **Real-time Processing**: Background processing with status updates
- **Detailed Reports**: Comprehensive scoring with improvement recommendations
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS

## 🏗️ Architecture

- **Frontend**: React 18 with Tailwind CSS
- **Backend**: FastAPI with Python 3.11
- **AI**: Google Gemini Pro for conversation analysis
- **Transcription**: OpenAI Whisper for audio/video
- **OCR**: Tesseract for image text extraction
- **Queue**: Redis for background job processing
- **Database**: PostgreSQL for data persistence

## 📋 Prerequisites

- Docker & Docker Compose
- API Keys:
  - Google Gemini API key
  - OpenAI API key (for Whisper transcription)

## 🔧 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd am-auditor-pro
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🛠️ Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

## 📝 Environment Variables

Create a `.env` file in the root directory:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/am_auditor_pro

# Redis
REDIS_URL=redis://localhost:6379

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your_secret_key_here

# File Upload Settings
MAX_FILE_SIZE_MB=100
ALLOWED_EXTENSIONS=mp3,wav,mp4,avi,mov,pdf,docx,txt,png,jpg,jpeg
```

## 🎯 Usage

1. **Upload a file**: Drag and drop or select a conversation file
2. **Monitor progress**: Track processing status in real-time
3. **View results**: Get comprehensive analysis with scores and recommendations

### Supported File Formats

- **Audio**: MP3, WAV, M4A
- **Video**: MP4, AVI, MOV
- **Documents**: PDF, DOCX, TXT
- **Images**: PNG, JPG, JPEG

## 🏃‍♂️ API Endpoints

- `POST /api/upload` - Upload conversation file
- `GET /api/status/{job_id}` - Get processing status
- `GET /api/results/{job_id}` - Get analysis results
- `GET /api/test-sample` - Test analysis with sample conversation
- `GET /api/health` - Health check

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Development Phases

### ✅ Phase 1: Foundation (Complete)
- Project setup and infrastructure
- File upload and basic processing
- Docker containerization
- Basic transcription pipeline

### ✅ Phase 2: AI Analysis Engine (Complete)
- Gemini API integration with real scoring rubric
- Dynamic rubric loading from Word documents
- Enhanced mock analysis with sample conversation
- Advanced processing pipeline with error handling

### 📋 Phase 3: Results Dashboard
- Interactive results visualization
- Charts and progress indicators
- Detailed breakdown tables
- Export functionality

### 🔮 Phase 4: Enhancement & Polish
- Performance optimization
- Error handling improvements
- Testing and validation
- Production deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the health check endpoint at `/api/health`
3. Check Docker logs: `docker-compose logs`

## 🔮 Future Enhancements

- User authentication and role management
- Team-level analytics and reporting
- Integration with call platforms (Aircall, etc.)
- Historical performance tracking
- Manager override and calibration features 