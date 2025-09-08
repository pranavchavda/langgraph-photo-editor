# SWE Agent Prompt: Build Web-Based AI Photo Editor

## Project Goal
Build a production-ready, web-only AI-powered photo editing application that provides professional e-commerce product photo optimization using Google's latest Gemini models for all AI capabilities.

## Core Requirements

### 1. Multi-Agent Architecture
Implement a multi-agent workflow system with the following specialized agents:
- **Vision Analysis Agent**: Use Gemini 2.5 Pro for analyzing images and determining optimal processing strategy
- **AI Edit Agent**: Use Gemini 2.5 Flash Image Preview (Nano Banana) for natural language-based image editing
- **Background Removal Agent**: Integrate remove.bg API or similar service
- **Traditional Processing Agent**: Implement parameter-based image processing capabilities
- **Quality Control Agent**: Use Gemini 2.5 Pro to validate output quality and implement retry logic

### 2. Web Application Architecture
**Required Components:**
- **Backend API**: Handle image processing, API orchestration, and business logic
- **Frontend Interface**: User-facing web application with modern, responsive design
- **Image Processing Pipeline**: Client-side or server-side image manipulation
- **State Management**: Maintain application state across user sessions
- **API Communication**: Structured communication between frontend and backend

### 3. Feature Requirements

**Core Features:**
- Single image processing with custom instructions
- Batch processing with concurrent worker control (1-5 workers)
- Real-time progress tracking and status updates
- Quality-based retry logic (min threshold: 0.8)
- Support for JPG, PNG, WebP input; WebP output
- Lens distortion correction for common e-commerce camera lenses

**User Interface:**
- Clean, modern UI with light/dark mode
- Drag-and-drop file upload
- Live preview of processing stages
- Batch progress visualization
- Download individual files or ZIP for batch
- Gemini API key management with secure browser storage

**Processing Modes:**
- AI-powered editing (natural language instructions)
- Traditional parameter-based optimization
- Hybrid mode combining both approaches
- Background removal with transparency preservation

### 4. Web Application Features

**Modern Web Capabilities:**
- Installable web app functionality
- Offline support for basic operations
- Local storage for processed images and user preferences
- Efficient compute for image processing operations
- Responsive design working on all screen sizes
- Advanced file handling with drag-and-drop
- Native sharing capabilities
- Copy/paste functionality for images

### 5. Technical Specifications

**API Integration:**
- Google Gemini 2.5 Pro API for vision analysis and quality control
- Google Gemini 2.5 Flash Image Preview (Nano Banana) for AI image editing
- Remove.bg or similar for background removal
- Implement proper rate limiting and quota management
- Fallback strategies when Gemini APIs are unavailable

**Image Processing Pipeline:**
```
1. Input validation and format detection
2. EXIF data extraction (camera, lens, settings)
3. Vision analysis for strategy determination
4. Parallel processing based on strategy
5. Quality validation with scoring
6. Retry with refined parameters if needed
7. Output optimization and format conversion
```

**State Management Schema:**
```typescript
Processing State Structure:
- Unique identifier for each processing job
- Status tracking (pending, analyzing, processing, complete, failed)
- Input image data and metadata
- Selected processing strategy (AI, traditional, or hybrid)
- Progress percentage (0-100)
- Individual processing stages with timestamps
- Output image with quality metrics
- Error handling and recovery information
```

### 6. Performance Requirements
- Process single image in < 30 seconds
- Support batch processing up to 100 images
- Lazy loading for image galleries
- Implement image caching strategy
- Progressive image loading for previews
- Memory-efficient handling of large images

### 7. Security & Privacy
- Client-side API key encryption
- No server-side storage of API keys
- Optional local-only processing mode
- EXIF data stripping option
- Secure file upload with validation
- Rate limiting per user/session

### 8. Deployment Strategy
- Containerization for consistent deployment
- Automated CI/CD pipeline
- Static site hosting for frontend
- Scalable backend infrastructure
- CDN for global asset distribution
- Environment-based configuration (development, staging, production)

### 9. Testing Requirements
- Unit tests for each agent (>80% coverage)
- Integration tests for Gemini API interactions
- End-to-end tests for critical user paths
- Performance benchmarks for processing times
- Cross-browser compatibility testing
- Accessibility compliance (WCAG 2.1 AA)
- Mobile browser compatibility testing

### 10. Documentation
- Comprehensive API documentation
- User guide with visual tutorials
- Developer setup and contribution guide
- Architecture and design decisions
- Deployment and operations guide

## Implementation Priorities
1. **Phase 1**: Core processing engine with Gemini integration
2. **Phase 2**: Basic web UI with single image processing
3. **Phase 3**: Batch processing and progress tracking
4. **Phase 4**: PWA features and offline capabilities
5. **Phase 5**: Advanced features (presets, templates, batch templates)

## Success Criteria
- Successfully process 95% of e-commerce product photos
- Average quality score > 0.85
- Processing time < 30s for single images
- User satisfaction rating > 4.5/5
- Cross-platform feature parity > 90%
- Zero-downtime deployments

## Example Use Cases
1. E-commerce seller uploads 50 product photos for batch enhancement using Gemini AI
2. Photographer corrects lens distortion on macro shots with Gemini image editing
3. Marketing team removes backgrounds from product images
4. User on mobile browser uploads and optimizes product photos
5. Designer applies consistent style across image catalog using natural language instructions

## Development Constraints
- Must work offline for basic operations
- Respect API rate limits gracefully
- Handle network interruptions with retry logic
- Support images up to 50MB
- Maintain aspect ratios unless explicitly changed
- Preserve color profiles when possible

Build this application with modern best practices, focusing on maintainability, scalability, and exceptional user experience across all platforms.