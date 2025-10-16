# Thai gTTS Integration Guide

## Overview
The Virtual Patient Simulator now uses **Google Text-to-Speech (gTTS)** for high-quality Thai language synthesis, replacing the browser's Web Speech API for TTS functionality.

## ✅ What's Changed

### 🔊 **Text-to-Speech (TTS)**
- **Before**: Browser Web Speech API (limited Thai support)
- **After**: Google gTTS service (excellent Thai pronunciation)
- **Language**: Thai only (`th-TH`)
- **Quality**: High-quality natural voice

### 🎤 **Speech-to-Text (STT)** 
- **Unchanged**: Still uses browser Web Speech Recognition
- **Language**: Thai (`th-TH`)
- **Works**: Chrome, Edge, Safari

## 📦 New Files Added

1. **`src/services/ttsService.js`** - Google gTTS integration service
2. **Updated `package.json`** - Added speech recognition packages
3. **Updated `SpeechModule.js`** - Now uses gTTS for Thai TTS
4. **Updated `SpeechModule.css`** - Enhanced error styling

## 🚀 Installation

1. **Install new packages:**
   ```bash
   cd Frontend
   npm install
   ```

2. **Start the application:**
   ```bash
   npm start
   ```

## 🎯 Features

### ✅ **Thai TTS with gTTS**
- Natural Thai pronunciation
- Automatic speech for patient responses
- Queue system for multiple messages
- Volume and speed control
- Error handling with user feedback

### ✅ **Thai STT (Unchanged)**
- Voice recognition for Thai language
- Auto-send transcribed messages
- Real-time transcript display
- Microphone permission handling

### ✅ **Smart Integration**
- TTS automatically stops when STT starts
- Visual feedback for both states
- Separate error messages
- Responsive design

## 🎛️ How to Use

### **For Patients (TTS):**
1. Patient responses are **automatically spoken** in Thai
2. High-quality natural voice pronunciation
3. Visual indicator shows when speaking
4. Click speaker button to stop

### **For Doctors (STT):**
1. Click **microphone button** to start listening
2. Speak in Thai - text appears in real-time
3. Message sent automatically after speaking
4. Works with Thai medical terminology

## ⚙️ Configuration

### **TTS Settings (in ttsService.js):**
```javascript
{
  language: 'th',     // Thai language
  slow: false,        // Normal speed
  volume: 0.8        // 80% volume
}
```

### **Speaker Characteristics:**
- **Child patients**: Slower speed
- **Adult patients**: Normal speed  
- **All patients**: Thai language only

## 🔧 Technical Details

### **gTTS Implementation:**
- Uses Google Translate TTS API
- Generates audio URLs for Thai text
- HTML5 Audio element for playback
- Queue system for message sequence
- Error handling and recovery

### **STT (Unchanged):**
- Web Speech Recognition API
- Thai language recognition (`th-TH`)
- Continuous listening mode
- Browser compatibility checks

## 🌐 Browser Compatibility

### **✅ Fully Supported:**
- **Chrome 60+** (TTS + STT)
- **Edge 79+** (TTS + STT)
- **Safari 14+** (TTS + STT)

### **⚠️ Limited Support:**
- **Firefox** (TTS only, no STT)
- **Mobile browsers** (varies)

## 🚨 Troubleshooting

### **TTS Issues:**
- **No sound**: Check volume, internet connection
- **Poor quality**: Clear browser cache
- **Yellow error**: TTS service temporarily unavailable

### **STT Issues:**
- **Red error**: Microphone permission denied
- **No recognition**: Check browser support, microphone
- **Poor accuracy**: Speak clearly, reduce background noise

### **Common Fixes:**
1. **Refresh the page** - Resets speech services
2. **Check browser console** - Look for detailed errors
3. **Test internet connection** - gTTS requires online access
4. **Grant microphone permission** - Required for STT

## 🔍 Code Structure

```
src/
├── services/
│   ├── ttsService.js          # gTTS service (NEW)
│   └── apiService.js          # API calls
├── components/chat/
│   ├── SpeechModule.js        # Speech integration (UPDATED)
│   ├── SpeechModule.css       # Styling (UPDATED)
│   └── ChatInterface.js       # Main chat (unchanged)
└── package.json               # Dependencies (UPDATED)
```

## 🧪 Testing

### **Test TTS:**
1. Start a chat session
2. Send a message as doctor
3. Patient response should be **automatically spoken**
4. Check for clear Thai pronunciation

### **Test STT:**
1. Click microphone button
2. Say "สวัสดีครับ" (Hello)
3. Text should appear and auto-send
4. Check response is received

## 📈 Benefits

### **🎯 Improved User Experience:**
- **Natural Thai pronunciation** vs robotic browser TTS
- **Consistent voice quality** across all devices
- **Better medical term pronunciation**
- **Queue system** prevents overlapping speech

### **🛠️ Better Maintainability:**
- **Centralized TTS service** - easy to modify
- **Error handling** - graceful failure recovery
- **Logging** - detailed console information for debugging
- **Configuration** - easy to adjust settings

## ⚡ Performance

- **Fast**: Audio loads in ~1-2 seconds
- **Reliable**: Fallback error handling
- **Efficient**: Queue system prevents conflicts
- **Responsive**: Non-blocking UI during speech

## 🔮 Future Enhancements

- **Voice selection**: Male/female Thai voices
- **Speed control**: User-adjustable speech rate
- **Offline mode**: Cached audio for common phrases
- **Recording**: Save conversations as audio files

---

## 🎉 Ready to Use!

Your Virtual Patient Simulator now has **professional-grade Thai TTS** using Google's technology. Enjoy natural, clear pronunciation for all patient interactions!

**Questions?** Check the browser console for detailed logging and error messages.