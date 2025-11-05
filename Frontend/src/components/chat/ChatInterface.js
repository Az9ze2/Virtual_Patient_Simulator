import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Send, Loader, Mic, Volume2, VolumeX } from 'lucide-react';
import apiService from '../../services/apiService';
import './ChatInterface.css';

const ChatInterface = () => {
  const { sessionData, addMessage, updateSession } = useApp();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // ============ STT STATE ============
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [sttError, setSttError] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  
  // ============ SILENCE DETECTION STATE ============
  const [isListeningForSilence, setIsListeningForSilence] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  // ============ 📊 ENHANCED TTS STATE (OPTIMIZED) ============
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [autoVoiceSelect, setAutoVoiceSelect] = useState(true);
  const [manualVoice, setManualVoice] = useState('nova');
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [speakerRole, setSpeakerRole] = useState('patient'); // 'patient' or 'mother'
  const audioRef = useRef(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const silenceTimeoutRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const inputRef = useRef(null);
  
  // ============ AUDIO ANALYSIS REFS ============
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const lastSoundTimeRef = useRef(0);
  const hasSpeechDetectedRef = useRef(false);

  // ============ 👶 CHECK IF PATIENT IS CHILD ============
  useEffect(() => {
    if (sessionData?.patientInfo) {
      const age = getPatientAge();
      const isChild = age < 12;
      setSpeakerRole(isChild ? 'mother' : 'patient');
      console.log(`👥 Speaker role updated: ${isChild ? 'MOTHER' : 'PATIENT'} (age: ${age})`);
    }
  }, [sessionData?.patientInfo]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessionData?.messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!isLoading && !isRecording) {
      inputRef.current?.focus();
    }
  }, [isLoading, isRecording, sessionData?.messages]);

  useEffect(() => {
    if (sttError) {
      const timer = setTimeout(() => {
        setSttError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [sttError]);

  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    }
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);

  const formatRecordingTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // ============ 🎵 ENHANCED AUDIO PLAYBACK ============
  const playAudio = (base64Audio) => {
    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      
      const audioUrl = `data:audio/mp3;base64,${base64Audio}`;
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onplay = () => {
        setIsPlayingAudio(true);
        console.log('📊 TTS audio started playing');
      };
      
      audio.onended = () => {
        setIsPlayingAudio(false);
        console.log('✅ TTS audio finished playing');
      };
      
      audio.onerror = (error) => {
        setIsPlayingAudio(false);
        console.error('❌ TTS audio playback error:', error);
      };
      
      audio.play().catch(error => {
        console.error('❌ Failed to play audio:', error);
        setIsPlayingAudio(false);
      });
    } catch (error) {
      console.error('❌ Error playing audio:', error);
      setIsPlayingAudio(false);
    }
  };

  // ============ 🧠 BUILD CONVERSATION CONTEXT FOR AI CORRECTION ============
  const getConversationContext = () => {
    return apiService.buildConversationContext(
      sessionData?.messages || [], 
      sessionData?.caseData
    );
  };

  // ============ 👶 GET PATIENT AGE ============
  const getPatientAge = () => {
    if (!sessionData?.patientInfo) return 0;
    
    const ageData = sessionData.patientInfo.age;
    if (typeof ageData === 'object' && ageData.value) {
      return parseInt(ageData.value);
    } else if (typeof ageData === 'string') {
      return parseInt(ageData.match(/\d+/)?.[0] || '0');
    } else if (typeof ageData === 'number') {
      return ageData;
    }
    return 0;
  };

  // ============ 💬 ENHANCED MESSAGE SENDING WITH OPTIMIZED TTS ============
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !sessionData?.sessionId) return;

    const userMessage = input.trim();
    setInput('');

    addMessage({
      role: 'user',
      content: userMessage,
      timestamp: Date.now()
    });

    setIsLoading(true);

    try {
      console.log('💬 Sending message with optimized TTS...');
      console.log('   TTS Enabled:', ttsEnabled);
      console.log('   Auto Voice:', autoVoiceSelect);
      console.log('   Manual Voice:', manualVoice);
      console.log('   👥 Speaker Role:', speakerRole);
      
      // 🎯 Use auto voice selection (null) or manual override
      const selectedVoice = autoVoiceSelect ? null : manualVoice;
      
      const response = ttsEnabled 
        ? await apiService.sendMessageWithTTS(
            sessionData.sessionId, 
            userMessage, 
            true, 
            selectedVoice, // null = auto-select (mother for children <12)
            1
          )
        : await apiService.sendMessage(sessionData.sessionId, userMessage);
      
      if (response.success) {
        addMessage({
          role: 'assistant',
          content: response.data.response,
          timestamp: Date.now()
        });

        // 📊 Log voice selection and speaker role info
        if (ttsEnabled && response.data.audio) {
          console.log('🎤 TTS Voice Info (OPTIMIZED):');
          console.log('   - Voice used:', response.data.audio.voice);
          console.log('   - Auto-selected:', response.data.audio.voice_auto_selected);
          console.log('   - Speed:', response.data.audio.speed);
          console.log('   - Speaker role:', response.data.audio.speaker_role);
          console.log('   - Is child patient:', response.data.audio.is_child_patient);
          console.log('   - Thai optimized:', response.data.audio.optimized_for_thai);
          
          // Update speaker role from response
          if (response.data.audio.speaker_role) {
            setSpeakerRole(response.data.audio.speaker_role);
          }
          
          if (response.data.audio.audio_base64) {
            const speakerLabel = response.data.audio.speaker_role === 'mother' ? 'Mother' : 'Patient';
            console.log(`🎵 Playing ${speakerLabel}'s optimized TTS audio...`);
            playAudio(response.data.audio.audio_base64);
          }
        }

        // Update token usage
        const tokens = response.data.token_usage;
        if (tokens) {
          const currentTokenUsage = sessionData?.tokenUsage || {
            inputTokens: 0,
            outputTokens: 0,
            totalTokens: 0
          };
          
          updateSession({
            tokenUsage: {
              inputTokens: currentTokenUsage.inputTokens + tokens.input_tokens,
              outputTokens: currentTokenUsage.outputTokens + tokens.output_tokens,
              totalTokens: currentTokenUsage.totalTokens + tokens.total_tokens
            }
          });
        }
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        role: 'system',
        content: `ข้อผิดพลาด เกิดข้อผิดพลาด: ${error.message}`,
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ============ 🚀 AUTO-SEND MESSAGE AFTER TRANSCRIPTION ============
  const autoSendTranscribedMessage = async (transcribedText) => {
    if (!transcribedText.trim() || !sessionData?.sessionId) return;

    addMessage({
      role: 'user',
      content: transcribedText,
      timestamp: Date.now()
    });

    setIsLoading(true);

    try {
      console.log('🚀 Auto-sending transcribed message with optimized TTS...');
      console.log('   👥 Speaker Role:', speakerRole);
      
      // 🎯 Use auto voice selection (null) or manual override
      const selectedVoice = autoVoiceSelect ? null : manualVoice;
      
      const response = ttsEnabled 
        ? await apiService.sendMessageWithTTS(
            sessionData.sessionId, 
            transcribedText, 
            true, 
            selectedVoice,
            1
          )
        : await apiService.sendMessage(sessionData.sessionId, transcribedText);
      
      if (response.success) {
        addMessage({
          role: 'assistant',
          content: response.data.response,
          timestamp: Date.now()
        });

        // 📊 Log voice selection and speaker info
        if (ttsEnabled && response.data.audio) {
          console.log('🎤 TTS Voice Info (Auto-send, OPTIMIZED):');
          console.log('   - Voice used:', response.data.audio.voice);
          console.log('   - Auto-selected:', response.data.audio.voice_auto_selected);
          console.log('   - Speaker role:', response.data.audio.speaker_role);
          console.log('   - Thai optimized:', response.data.audio.optimized_for_thai);
          
          // Update speaker role from response
          if (response.data.audio.speaker_role) {
            setSpeakerRole(response.data.audio.speaker_role);
          }
          
          if (response.data.audio.audio_base64) {
            const speakerLabel = response.data.audio.speaker_role === 'mother' ? 'Mother' : 'Patient';
            console.log(`🎵 Playing ${speakerLabel}'s optimized TTS audio...`);
            playAudio(response.data.audio.audio_base64);
          }
        }

        // Update token usage
        const tokens = response.data.token_usage;
        if (tokens) {
          const currentTokenUsage = sessionData?.tokenUsage || {
            inputTokens: 0,
            outputTokens: 0,
            totalTokens: 0
          };
          
          updateSession({
            tokenUsage: {
              inputTokens: currentTokenUsage.inputTokens + tokens.input_tokens,
              outputTokens: currentTokenUsage.outputTokens + tokens.output_tokens,
              totalTokens: currentTokenUsage.totalTokens + tokens.total_tokens
            }
          });
        }
      } else {
        throw new Error(response.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        role: 'system',
        content: `ข้อผิดพลาด เกิดข้อผิดพลาด: ${error.message}`,
        timestamp: Date.now()
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ============ 🎤 AUDIO LEVEL DETECTION WITH NOISE CANCELLATION ============
  const detectAudioLevel = () => {
    if (!analyserRef.current) {
      console.log('⚠️ Analyser not available - cannot detect audio levels');
      return;
    }
    
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') {
      console.log('⚠️ MediaRecorder not recording - stopping detection');
      return;
    }

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    analyser.getByteFrequencyData(dataArray);
    
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i];
    }
    const average = sum / bufferLength;
    
    const NOISE_THRESHOLD = 12;
    const SPEECH_THRESHOLD = 32;
    
    setAudioLevel(average);
    
    const now = Date.now();
    if (!window.lastLogTime || now - window.lastLogTime > 500) {
      console.log('📊 Audio Level:', average.toFixed(2), 
                  '| Noise:', average > NOISE_THRESHOLD ? '✅' : '❌',
                  '| Speech:', average > SPEECH_THRESHOLD ? '✅' : '❌',
                  '| Has Speech:', hasSpeechDetectedRef.current);
      window.lastLogTime = now;
    }
    
    if (average > SPEECH_THRESHOLD) {
      lastSoundTimeRef.current = Date.now();
      
      if (!hasSpeechDetectedRef.current) {
        hasSpeechDetectedRef.current = true;
        setIsListeningForSilence(true);
        console.log('🎤 SPEECH DETECTED! Listening for silence...');
      }
    }
    
    const SILENCE_DURATION = 1250;
    const MIN_RECORDING_DURATION = 1000;
    
    const timeSinceLastSound = Date.now() - lastSoundTimeRef.current;
    const recordingDuration = Date.now() - (mediaRecorderRef.current?.startTime || Date.now());
    
    if (hasSpeechDetectedRef.current) {
      if (!window.lastTimingLog || now - window.lastTimingLog > 500) {
        console.log('⏱️ Time since last sound:', (timeSinceLastSound/1000).toFixed(1) + 's',
                    '| Recording duration:', (recordingDuration/1000).toFixed(1) + 's');
        window.lastTimingLog = now;
      }
    }
    
    if (hasSpeechDetectedRef.current && 
        timeSinceLastSound > SILENCE_DURATION && 
        recordingDuration > MIN_RECORDING_DURATION) {
      console.log('🔇 SILENCE DETECTED! Auto-stopping recording...');
      console.log('   - Time since last sound:', (timeSinceLastSound/1000).toFixed(1) + 's');
      console.log('   - Total recording time:', (recordingDuration/1000).toFixed(1) + 's');
      stopRecording();
      return;
    }
    
    animationFrameRef.current = requestAnimationFrame(detectAudioLevel);
  };

  // ============ 🎙️ START RECORDING WITH AUDIO ANALYSIS ============
  const startRecording = async () => {
    try {
      setSttError(null);
      
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setSttError('เบราว์เซอร์ของคุณไม่รองรับการบันทึกเสียง กรุณาใช้ Chrome, Firefox หรือ Edge');
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });

      try {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContextRef.current.createMediaStreamSource(stream);
        analyserRef.current = audioContextRef.current.createAnalyser();
        
        analyserRef.current.fftSize = 2048;
        analyserRef.current.smoothingTimeConstant = 0.8;
        
        source.connect(analyserRef.current);
        
        console.log('✅ Audio analyser initialized successfully');
      } catch (error) {
        console.error('❌ Failed to initialize audio analyser:', error);
      }

      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4'
      ];
      
      let selectedMimeType = '';
      for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          selectedMimeType = type;
          break;
        }
      }

      if (!selectedMimeType) {
        throw new Error('ไม่พบรูปแบบการบันทึกเสียงที่รองรับ');
      }

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: selectedMimeType,
        audioBitsPerSecond: 128000
      });

      mediaRecorderRef.current.startTime = Date.now();
      audioChunksRef.current = [];
      hasSpeechDetectedRef.current = false;
      lastSoundTimeRef.current = Date.now();

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        
        setAudioLevel(0);
        setIsListeningForSilence(false);
        
        await processRecording(); 
      };

      mediaRecorderRef.current.start(100);
      setIsRecording(true);
      
      console.log('🎤 Recording started with noise cancellation enabled');

      setTimeout(() => {
        console.log('🎯 Starting audio level detection...');
        console.log('   - isRecording:', isRecording);
        console.log('   - analyserRef.current:', !!analyserRef.current);
        detectAudioLevel();
      }, 100);

      silenceTimeoutRef.current = setTimeout(() => {
        console.log('⏰ Auto-stopping recording after 60 seconds');
        stopRecording();
      }, 60000);
      
    } catch (error) {
      console.error('🚨 Microphone access error:', error);
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        setSttError('ไม่ได้รับอนุญาตให้ใช้ไมโครโฟน กรุณาอนุญาตการเข้าถึงไมโครโฟนในการตั้งค่าเบราว์เซอร์');
      } else if (error.name === 'NotFoundError') {
        setSttError('ไม่พบไมโครโฟน กรุณาเชื่อมต่อไมโครโฟนกับอุปกรณ์ของคุณ');
      } else if (error.name === 'NotReadableError') {
        setSttError('ไม่สามารถเข้าถึงไมโครโฟนได้ อาจมีแอปพลิเคชั่นอื่นกำลังใช้งานอยู่');
      } else {
        setSttError('เกิดข้อผิดพลาดในการเข้าถึงไมโครโฟน: ' + error.message);
      }
    }
  };
  
  const stopRecording = () => {
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('🛑 Recording stopped');
    }
  };

  // ============ 🧠 ENHANCED AUDIO PROCESSING WITH CONTEXT-AWARE CORRECTION ============
  const processRecording = async () => {
    if (audioChunksRef.current.length === 0) {
      console.log('❌ No audio chunks recorded');
      setSttError('ไม่มีข้อมูลเสียงที่บันทึก กรุณาลองอีกครั้ง');
      return;
    }

    setIsProcessingAudio(true);
    setSttError(null);

    try {
      const audioBlob = new Blob(audioChunksRef.current, { 
        type: mediaRecorderRef.current.mimeType 
      });

      const fileSizeKB = (audioBlob.size / 1024).toFixed(2);
      console.log(`📊 Audio blob created: ${fileSizeKB} KB, type: ${audioBlob.type}`);

      if (audioBlob.size < 1000) {
        console.log('❌ Audio too small:', audioBlob.size, 'bytes');
        setSttError('เสียงที่บันทึกสั้นเกินไป กรุณาพูดนานขึ้นและลองอีกครั้ง');
        setIsProcessingAudio(false);
        return;
      }

      console.log('📤 Sending audio to backend with context-aware correction...');
      
      // 🧠 BUILD CONVERSATION CONTEXT FOR BETTER AI CORRECTION
      const conversationContext = getConversationContext();
      console.log('🧠 Context length:', conversationContext.length, 'characters');
      
      // 🚀 TRANSCRIBE WITH CONTEXT AND CORRECTION
      const transcription = await apiService.transcribeAudioWithContext(
        audioBlob,
        conversationContext,
        null  // Use backend default correction setting
      );

      console.log('📥 Transcription response:', transcription);

      if (transcription.success && transcription.data.text) {
        const finalText = transcription.data.text.trim();
        
        console.log('✅ Transcription successful:', finalText);
        
        // 📊 LOG CORRECTION DETAILS
        if (transcription.data.correction) {
          const correction = transcription.data.correction;
          console.log('🧠 AI Correction Details:');
          console.log('   - Was corrected:', correction.was_corrected);
          console.log('   - Original text:', correction.original_text);
          console.log('   - Corrected text:', correction.corrected_text);
          console.log('   - Model used:', correction.model_used);
          console.log('   - Confidence:', correction.confidence);
          console.log('   - Processing time:', correction.processing_time_ms, 'ms');
          
          if (correction.was_corrected && correction.changes && correction.changes.length > 0) {
            console.log('✏️ Changes made:', correction.changes.length);
            correction.changes.forEach((change, idx) => {
              console.log(`   ${idx + 1}. "${change.original}" → "${change.corrected}" (${change.type})`);
            });
          }
        }
        
        // 📊 LOG PERFORMANCE METRICS
        if (transcription.data.processing_time) {
          console.log('⏱️ Performance Metrics:');
          console.log('   - Whisper transcription:', transcription.data.processing_time.whisper_ms, 'ms');
          console.log('   - Total processing:', transcription.data.processing_time.total_ms, 'ms');
        }
        
        if (!finalText || finalText.length < 2) {
          console.log('❌ Transcribed text is empty or too short');
          setSttError('ไม่สามารถแปลงเสียงเป็นข้อความได้ กรุณาลองพูดชัดขึ้น');
          setIsProcessingAudio(false);
          return;
        }

        // 🚀 AUTO-SEND THE CORRECTED MESSAGE
        console.log('🚀 Auto-sending transcribed message with optimized TTS...');
        await autoSendTranscribedMessage(finalText);
        console.log('✅ Message auto-sent successfully!');
        
      } else {
        console.log('❌ Transcription failed:', transcription.error);
        throw new Error(transcription.error || 'Transcription failed');
      }

    } catch (error) {
      console.error('🚨 Transcription error:', error);
      
      let userFriendlyMessage = 'เกิดข้อผิดพลาดในการแปลงเสียง กรุณาลองอีกครั้ง';
      
      if (error.response?.data?.detail) {
        const errorData = error.response.data;
        
        if (errorData.detail) {
          if (typeof errorData.detail === 'object') {
            if (errorData.detail.error === 'unclear_audio') {
              userFriendlyMessage = errorData.detail.message || 'ไม่สามารถแปลงเสียงให้เป็นข้อความที่มีความหมายได้';
              
              if (errorData.detail.hints) {
                console.log('💡 คำแนะนำ:');
                errorData.detail.hints.forEach(hint => console.log('   -', hint));
              }
            } else if (errorData.detail.error === 'silent_audio') {
              userFriendlyMessage = 'ไม่พบเสียงพูดในการบันทึก กรุณาตรวจสอบไมโครโฟนและพูดให้ชัดเจน';
            } else if (errorData.detail.error === 'audio_too_short') {
              userFriendlyMessage = 'เสียงที่บันทึกสั้นเกินไป กรุณาพูดนานขึ้นและลองอีกครั้ง';
            } else if (errorData.detail.message) {
              userFriendlyMessage = errorData.detail.message;
            }
          } else if (typeof errorData.detail === 'string') {
            userFriendlyMessage = errorData.detail;
          }
        }
      }
      
      if (error.message && !userFriendlyMessage.includes('เกิดข้อผิดพลาด')) {
        if (error.message.includes('timeout') || error.message.includes('หมดเวลา')) {
          userFriendlyMessage = 'หมดเวลาในการประมวลผลเสียง กรุณาลองอีกครั้ง';
        } else if (error.message.includes('network') || error.message.includes('Network error')) {
          userFriendlyMessage = 'เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย กรุณาตรวจสอบอินเทอร์เน็ต';
        }
      }
      
      setSttError(userFriendlyMessage);
    } finally {
      setIsProcessingAudio(false);
      audioChunksRef.current = [];
      console.log('🧹 Cleanup complete');
    }
  };

  // ============ 🎛️ TOGGLE RECORDING (SINGLE BUTTON) ============
  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('th-TH', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // ============ 🎭 GET PATIENT INFO FOR DISPLAY ============
  const getPatientDisplayInfo = () => {
    if (sessionData?.patientInfo) {
      const patient = sessionData.patientInfo;
      const age = getPatientAge();
      const ageDisplay = typeof patient.age === 'object' ? patient.age.value : patient.age;
      return `${patient.name || 'Patient'} (${patient.sex || 'N/A'}, ${ageDisplay || 'N/A'}y)`;
    }
    return 'Virtual Patient';
  };

  // ============ 👥 GET SPEAKER DISPLAY LABEL ============
  const getSpeakerLabel = () => {
    if (speakerRole === 'mother') {
      return '👩 Mother (speaking for child)';
    }
    return '👤 Patient';
  };

  return (
    <div className="chat-interface">
      {/* ⚠️ STT ERROR BANNER */}
      {sttError && (
        <div className="stt-error-banner">
          <div className="stt-error-content">
            <span className="stt-error-icon">⚠️</span>
            <span className="stt-error-text">{sttError}</span>
          </div>
          <button 
            className="stt-error-close"
            onClick={() => setSttError(null)}
            aria-label="ปิด"
          >
            ✕
          </button>
        </div>
      )}

      {/* 📊 CHAT HEADER */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="patient-avatar">
            {speakerRole === 'mother' ? '👩' : '👤'}
          </div>
          <div>
            <h3 className="chat-title">
              {speakerRole === 'mother' ? 'Patient\'s Mother' : 'Virtual Patient'}
            </h3>
            <p className="chat-subtitle">
              {isPlayingAudio ? '📊 Speaking...' : 
               isListeningForSilence ? '👂 Listening...' : 
               isRecording ? '🎤 Ready to listen' : 
               speakerRole === 'mother' ? '👶 Child patient (<12y) - Mother responds' :
               autoVoiceSelect ? '🎭 Auto Voice Mode' : '🎤 Manual Voice'}
            </p>
          </div>
        </div>
        <div className="header-stats">
          <div className="message-count">
            💬 {sessionData?.messages?.length || 0} messages
          </div>
        </div>
      </div>

      {/* 💬 CHAT MESSAGES */}
      <div className="chat-messages" ref={chatContainerRef}>
        {!sessionData?.messages?.length ? (
          <div className="empty-chat">
            <div className="empty-icon">💬</div>
            <h3>Start the Conversation</h3>
            <p>Click the microphone to speak or type your message.</p>
            <p className="text-sm text-muted" style={{ marginTop: '0.5rem' }}>
              🧠 AI correction enabled for medical terminology
            </p>
            {speakerRole === 'mother' && (
              <p className="text-sm text-muted" style={{ marginTop: '0.5rem', color: '#8b5cf6' }}>
                👶 Child patient detected - Mother will speak
              </p>
            )}
          </div>
        ) : (
          sessionData.messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.role === 'user' ? 'message-user' : 'message-assistant'} ${
                message.role === 'system' ? 'message-system' : ''
              }`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? '🧑‍⚕️' : 
                 message.role === 'system' ? '⚠️' : 
                 speakerRole === 'mother' ? '👩' : '👤'}
              </div>
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {message.role === 'user' ? 'Doctor' : 
                     message.role === 'system' ? 'System' : 
                     speakerRole === 'mother' ? "Patient's Mother" : 'Patient'}
                  </span>
                  <span className="message-time">{formatTime(message.timestamp)}</span>
                </div>
                <div className="message-text">{message.content}</div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message message-assistant">
            <div className="message-avatar">
              {speakerRole === 'mother' ? '👩' : '👤'}
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder={
            isRecording 
              ? isListeningForSilence 
                ? "🎤 กำลังฟัง... (พูดได้เลย)" 
                : "🎤 เริ่มพูดได้เลย..."
              : isProcessingAudio 
                ? "⚙️ กำลังประมวลผล..." 
                : "พิมพ์ข้อความหรือคลิกไมโครโฟนเพื่อพูด..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading || isRecording || isProcessingAudio}
        />
        
        <button
          type="button"
          className={`btn chat-mic-btn ${ttsEnabled ? '' : 'btn-outline'}`}
          onClick={() => setTtsEnabled(!ttsEnabled)}
          disabled={isLoading || isRecording || isProcessingAudio}
          title={ttsEnabled ? 'ปิดเสียงตอบกลับ' : 'เปิดเสียงตอบกลับ'}
          style={{ 
            background: ttsEnabled ? 'linear-gradient(135deg, #8b5cf6, #7c3aed)' : undefined,
            height: '52px',
            minHeight: '52px'
          }}
        >
          {ttsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
        </button>
        
        <button
          type="button"
          className={`btn chat-mic-btn ${isRecording ? 'recording' : ''} ${isListeningForSilence ? 'listening' : ''}`}
          onClick={toggleRecording}
          disabled={isLoading || isProcessingAudio}
          title={isRecording ? "หยุดบันทึก" : "เริ่มบันทึกเสียง"}
          style={{ 
            height: '52px',
            minHeight: '52px',
            boxShadow: isRecording && audioLevel > 30 
              ? `0 4px 25px rgba(239, 68, 68, ${0.3 + (audioLevel / 255) * 0.5})` 
              : undefined
          }}
        >
          {isProcessingAudio ? (
            <Loader size={20} className="spinning" />
          ) : isRecording ? (
            <>
              <Mic size={20} />
              <span style={{ marginLeft: '0.25rem', fontSize: '0.875rem' }}>
                {formatRecordingTime(recordingTime)}
              </span>
            </>
          ) : (
            <Mic size={20} />
          )}
        </button>

        <button
          type="submit"
          className="btn btn-primary chat-send-btn"
          disabled={!input.trim() || isLoading || isRecording || isProcessingAudio}
          style={{ 
            height: '52px',
            minHeight: '52px'
          }}
        >
          {isLoading ? <Loader size={20} className="spinning" /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;