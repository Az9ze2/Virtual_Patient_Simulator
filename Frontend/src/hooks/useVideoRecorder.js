import { useState, useRef, useCallback } from 'react';

/**
 * Custom hook for video recording using MediaRecorder API
 * Handles camera permission, recording start/stop, and video blob generation
 */
const useVideoRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [error, setError] = useState(null);
  const [permissionGranted, setPermissionGranted] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  /**
   * Request camera permission and prepare for recording
   */
  const requestCameraPermission = useCallback(async () => {
    try {
      setError(null);
      
      // Request user media with video and audio
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: true
      });

      streamRef.current = stream;
      setPermissionGranted(true);
      return { success: true, stream };
    } catch (err) {
      console.error('Camera permission error:', err);
      let errorMessage = 'Failed to access camera';
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Camera permission denied. Please allow camera access to record.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No camera found. Please connect a camera device.';
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'Camera is already in use by another application.';
      }
      
      setError(errorMessage);
      setPermissionGranted(false);
      return { success: false, error: errorMessage };
    }
  }, []);

  /**
   * Start recording video
   */
  const startRecording = useCallback(async () => {
    try {
      // If no stream, request permission first
      if (!streamRef.current) {
        const result = await requestCameraPermission();
        if (!result.success) {
          return { success: false, error: result.error };
        }
      }

      // Reset chunks
      chunksRef.current = [];

      // Create MediaRecorder
      const options = {
        mimeType: 'video/webm;codecs=vp9' // VP9 for better compression
      };

      // Fallback to VP8 if VP9 not supported
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'video/webm;codecs=vp8';
      }

      // Fallback to default if neither supported
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'video/webm';
      }

      const mediaRecorder = new MediaRecorder(streamRef.current, options);
      mediaRecorderRef.current = mediaRecorder;

      // Collect data chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: options.mimeType });
        setRecordedBlob(blob);
        setIsRecording(false);
      };

      // Handle errors
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
        setError(`Recording error: ${event.error.name}`);
        setIsRecording(false);
      };

      // Start recording
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      setError(null);

      return { success: true };
    } catch (err) {
      console.error('Start recording error:', err);
      const errorMessage = `Failed to start recording: ${err.message}`;
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  }, [requestCameraPermission]);

  /**
   * Stop recording video
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      
      // Stop all tracks to release camera
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      
      setPermissionGranted(false);
      return { success: true };
    }
    return { success: false, error: 'No active recording' };
  }, [isRecording]);

  /**
   * Cancel recording and clean up
   */
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      if (isRecording) {
        mediaRecorderRef.current.stop();
      }
      mediaRecorderRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    chunksRef.current = [];
    setIsRecording(false);
    setRecordedBlob(null);
    setPermissionGranted(false);
    setError(null);
  }, [isRecording]);

  /**
   * Download the recorded video
   */
  const downloadVideo = useCallback((filename = 'session-recording.webm') => {
    if (!recordedBlob) {
      console.warn('No recorded video to download');
      return { success: false, error: 'No recorded video available' };
    }

    try {
      const url = URL.createObjectURL(recordedBlob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);

      return { success: true };
    } catch (err) {
      console.error('Download error:', err);
      return { success: false, error: err.message };
    }
  }, [recordedBlob]);

  /**
   * Get video URL for preview
   */
  const getVideoURL = useCallback(() => {
    if (!recordedBlob) return null;
    return URL.createObjectURL(recordedBlob);
  }, [recordedBlob]);

  /**
   * Clean up resources
   */
  const cleanup = useCallback(() => {
    cancelRecording();
  }, [cancelRecording]);

  return {
    isRecording,
    recordedBlob,
    error,
    permissionGranted,
    requestCameraPermission,
    startRecording,
    stopRecording,
    cancelRecording,
    downloadVideo,
    getVideoURL,
    cleanup
  };
};

export default useVideoRecorder;
