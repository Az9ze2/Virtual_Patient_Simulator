import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import './SessionTimer.css';

const SessionTimer = ({ startTime }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const formatTime = (ms) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60) % 60;
    const seconds = totalSeconds % 60;
    const hours = Math.floor(totalSeconds / 3600);
    return `${hours.toString().padStart(1, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="session-timer">
      <Clock size={18} />
      <span className="timer-display">{formatTime(elapsed)}</span>
    </div>
  );
};

export default SessionTimer;
