# Quick Start Guide - Virtual Patient Simulator

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies

Open terminal in the Frontend directory and run:

```bash
npm install
```

This will install all required packages:
- React and React DOM
- React Router for navigation
- Lucide React for icons
- Axios for API calls

### Step 2: Start the Application

```bash
npm start
```

The application will automatically open in your browser at `http://localhost:3000`

### Step 3: Explore the Features

1. **Click "Start Interview Session"**
   - Enter your name and student ID
   - Select a case from the dropdown
   - Click "Start Session"

2. **Chat with the Virtual Patient**
   - Type messages in the chat interface
   - The virtual patient will respond based on the case
   - View patient information in the right panel
   - Enter your diagnosis and treatment plan

3. **End the Session**
   - Click "End Session" when done
   - Review your session summary
   - Download the report

## 📁 Project Structure Overview

```
Frontend/
├── src/
│   ├── components/      # Reusable components
│   │   ├── chat/       # Chat-related components
│   │   └── modals/     # Modal dialogs
│   ├── context/        # Global state management
│   ├── pages/          # Main page components
│   ├── App.js          # Main app component
│   └── index.js        # Entry point
├── public/             # Static files
└── package.json        # Dependencies
```

## 🎨 Key Features

### Homepage
- Three main action buttons
- Session statistics
- Theme toggle (light/dark)
- Resume session capability

### Chat Interface
- Real-time messaging
- Patient information panel
- Diagnosis section
- Session timer
- Token usage tracking

### Settings
- AI model configuration
- Temperature and other parameters
- Theme customization
- Auto-save options

### Summary Page
- Session metrics
- Conversation history
- Download report as JSON

## 🔧 Configuration

### Change Backend URL

Edit `package.json`:
```json
"proxy": "http://localhost:5000"
```

### Modify Theme Colors

Edit `src/index.css` CSS variables:
```css
:root {
  --accent-primary: #3b82f6;  /* Change primary color */
  --bg-primary: #f8fafc;       /* Change background */
  /* ... more variables */
}
```

### Add New Cases

Edit `src/components/modals/StartSessionModal.js`:
```javascript
const MOCK_CASES = [
  {
    id: 'CASE-005',
    title: 'Your New Case',
    titleThai: 'กรณีของคุณ',
    specialty: 'Specialty',
    duration: 15,
    description: 'Case description'
  },
  // ... existing cases
];
```

## 🐛 Common Issues

### Issue: Port 3000 is already in use
**Solution:**
```bash
# Use a different port
PORT=3001 npm start
```

### Issue: Cannot connect to backend
**Solution:**
1. Make sure backend is running on port 5000
2. Check if CORS is enabled in backend
3. Verify proxy setting in package.json

### Issue: Module not found
**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Issue: Application won't build
**Solution:**
```bash
# Clear npm cache
npm cache clean --force
npm install
npm start
```

## 📱 Testing on Mobile

1. Find your computer's IP address
2. Start the app: `npm start`
3. On mobile browser, go to: `http://YOUR_IP:3000`

## 🎯 Next Steps

1. **Connect to Backend**
   - Uncomment API calls in `ChatInterface.js`
   - Replace mock data with real API endpoints
   
2. **Customize Appearance**
   - Modify colors in `index.css`
   - Update logos and branding
   
3. **Add Features**
   - Voice input
   - PDF export
   - Advanced analytics

## 📚 Learn More

- [React Documentation](https://react.dev)
- [React Router](https://reactrouter.com)
- [Lucide Icons](https://lucide.dev)

## 💡 Tips

- Use `Ctrl+Shift+I` (Windows) or `Cmd+Option+I` (Mac) to open DevTools
- Check Console for errors and logs
- Use React DevTools browser extension for debugging
- LocalStorage contains all session data - clear if needed

## 🎓 For Students

This simulator helps you practice:
- Patient interview skills
- Clinical reasoning
- Diagnosis formulation
- Treatment planning
- Time management

**Best Practices:**
1. Greet the patient naturally
2. Ask open-ended questions
3. Use follow-up questions
4. Take your time
5. Review patient information carefully

## 🏥 For Instructors

**Setup for Classroom:**
1. Install on server or multiple machines
2. Configure backend with your cases
3. Set exam mode in settings for standardized testing
4. Collect session reports for evaluation

**Customization:**
- Add your institution's cases
- Modify AI parameters for difficulty
- Adjust time limits
- Customize assessment criteria

---

**Ready to start? Run `npm start` and begin practicing!** 🚀
