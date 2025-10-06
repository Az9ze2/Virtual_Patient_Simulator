# Thai Language-Based Virtual Patient Simulator - Frontend

A modern React-based frontend for the Virtual Patient Simulator system, designed for medical education and OSCE practice.

## Features

### 🏠 Homepage
- Clean, intuitive interface with three main actions
- Quick session statistics
- Support for both light and dark themes
- Resume session capability

### 💬 Start Interview Session
- Two-step session initialization
- Student information collection
- Case selection from available patient cases
- Visual progress indicators

### 📄 Document Upload
- Drag-and-drop file upload
- Support for DOCX and PDF files
- Real-time extraction progress
- JSON preview and validation
- Quick session start with uploaded cases

### ⚙️ Settings
- **AI Configuration**
  - Model selection (GPT-4.1 Mini / GPT-5)
  - Temperature, Top P, Frequency Penalty, Presence Penalty adjustments
  - Memory mode selection
  - Exam vs Practice mode toggle
- **Appearance**
  - Light/Dark theme toggle
  - Auto-save session toggle
  - Timer visibility control

### 💻 Chatbot Interface
- Real-time chat with virtual patient
- Message history with timestamps
- Typing indicators
- Smooth animations
- Patient information panel
- Diagnosis and treatment plan section
- Session timer
- Token usage tracking

### 📊 Summary Page
- Comprehensive session metrics
- Time tracking (duration, active time)
- Message statistics
- Token usage breakdown
- Diagnosis and treatment review
- Conversation history preview
- Download session report as JSON

## Tech Stack

- **React 18** - Modern UI library
- **React Router** - Client-side routing
- **Context API** - State management
- **Lucide React** - Icon library
- **Axios** - HTTP client
- **CSS3** - Custom styling with CSS variables

## Project Structure

```
Frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.js
│   │   │   ├── ChatInterface.css
│   │   │   ├── PatientInfo.js
│   │   │   ├── PatientInfo.css
│   │   │   ├── DiagnosisSection.js
│   │   │   ├── DiagnosisSection.css
│   │   │   ├── SessionTimer.js
│   │   │   └── SessionTimer.css
│   │   └── modals/
│   │       ├── StartSessionModal.js
│   │       ├── UploadDocumentModal.js
│   │       ├── SettingsModal.js
│   │       └── Modal.css
│   ├── context/
│   │   └── AppContext.js
│   ├── pages/
│   │   ├── HomePage.js
│   │   ├── HomePage.css
│   │   ├── ChatbotPage.js
│   │   ├── ChatbotPage.css
│   │   ├── SummaryPage.js
│   │   └── SummaryPage.css
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   └── index.css
├── package.json
└── README.md
```

## Installation

### Prerequisites
- Node.js 14+ and npm
- Backend server running on `http://localhost:5000`

### Steps

1. **Navigate to Frontend directory**
   ```bash
   cd Frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

The application will open at `http://localhost:3000`

## Available Scripts

- `npm start` - Run development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App (one-way operation)

## Configuration

### Backend API
The frontend is configured to proxy API requests to `http://localhost:5000`. 

To change the backend URL, modify the `proxy` field in `package.json`:
```json
"proxy": "http://your-backend-url:port"
```

### Theme
The application supports light and dark themes with automatic persistence. Colors are defined using CSS variables in `index.css`.

### Settings Persistence
User settings are stored in browser localStorage:
- Theme preference
- AI model parameters
- UI preferences
- Session data (auto-save enabled)

## Features in Detail

### Session Management
- Sessions are automatically saved to localStorage
- Resume capability from homepage
- Session history (last 10 sessions)
- Auto-save every 30 seconds (if enabled)

### Mock Data
The prototype includes mock patient cases and responses for demonstration:
- 4 pre-loaded pediatric cases
- Intelligent response matching based on keywords
- Simulated API delays for realistic experience

### Responsive Design
- Mobile-first approach
- Breakpoints at 640px, 768px, 968px, 1200px
- Touch-friendly interface
- Adaptive layouts for all screen sizes

## Integration with Backend

### Expected API Endpoints

```javascript
// Session Management
POST /api/session/start
  Body: { name, studentId, caseId }
  Response: { success, sessionId, caseData }

// Chat
POST /api/chat/message
  Body: { sessionId, message, caseData }
  Response: { success, response, tokenUsage }

// Document Upload
POST /api/document/upload
  Body: FormData with file
  Response: { success, extractedData, validationStatus }

// Cases
GET /api/cases/list
  Response: { success, cases: [...] }

// Session End
POST /api/session/end
  Body: { sessionId, diagnosis, treatmentPlan }
  Response: { success, summary }
```

### Current Mock Implementation
The prototype uses mock data and simulated API calls. To connect to real backend:

1. Uncomment API calls in `ChatInterface.js`
2. Replace mock responses with actual API endpoints
3. Update token usage calculations
4. Implement proper error handling

## Customization

### Adding New Cases
Add cases to the `MOCK_CASES` array in `StartSessionModal.js`:
```javascript
{
  id: 'CASE-XXX',
  title: 'Case Title',
  titleThai: 'ชื่อภาษาไทย',
  specialty: 'Specialty',
  duration: 15,
  description: 'Case description'
}
```

### Modifying AI Parameters
Default parameters are in `AppContext.js`:
```javascript
{
  model: 'gpt-4.1-mini',
  temperature: 0.7,
  topP: 0.85,
  frequencyPenalty: 0.6,
  presencePenalty: 0.9,
  memoryMode: 'summarize',
  examMode: false
}
```

### Styling
- Global styles: `index.css`
- Component styles: Individual `.css` files
- Theme colors: CSS variables in `:root` and `[data-theme="dark"]`

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Optimization

- Code splitting with React.lazy (can be added)
- CSS optimization with custom properties
- Efficient re-renders with React Context
- Debounced auto-save
- Virtualized lists for long conversations (can be added)

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus management in modals
- Color contrast compliance (WCAG AA)

## Known Limitations

1. Mock data for demonstration only
2. No real-time collaboration
3. No voice input (can be added)
4. Limited offline support
5. Session storage in localStorage (should use backend in production)

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Export to PDF
- [ ] Screen recording capability
- [ ] Peer review features
- [ ] Integration with learning management systems

## Troubleshooting

### Port 3000 already in use
```bash
# Windows
set PORT=3001 && npm start

# macOS/Linux
PORT=3001 npm start
```

### Backend connection errors
- Verify backend is running on port 5000
- Check CORS settings in backend
- Verify proxy configuration in package.json

### Module not found errors
```bash
rm -rf node_modules package-lock.json
npm install
```

### Build errors
```bash
npm cache clean --force
npm install
npm run build
```

## Contributing

1. Follow the existing code structure
2. Maintain consistent naming conventions
3. Add comments for complex logic
4. Test on multiple browsers
5. Ensure responsive design
6. Update this README for new features

## License

This project is part of the IRPC Internship program.

## Support

For issues or questions:
1. Check this README
2. Review existing code comments
3. Contact the development team

---

**Note**: This is a prototype with mock data. Connect to the actual backend API for production use.
