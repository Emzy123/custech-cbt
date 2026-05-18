import React from 'react';
import { Clock } from '@phosphor-icons/react';
import clsx from 'clsx';

interface TimerProps {
  timeRemaining: number; // in seconds
  className?: string;
}

const Timer: React.FC<TimerProps> = ({ timeRemaining, className }) => {
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  const getTimerState = (): 'normal' | 'warning' | 'critical' => {
    if (timeRemaining <= 300) return 'critical'; // 5 minutes
    if (timeRemaining <= 900) return 'warning'; // 15 minutes
    return 'normal';
  };
  
  const state = getTimerState();
  const timeString = formatTime(timeRemaining);
  
  const timerClasses = clsx(
    'inline-flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm',
    {
      'bg-light text-body': state === 'normal',
      'bg-custech-gold bg-opacity-20 text-custech-primary': state === 'warning',
      'bg-danger bg-opacity-20 text-danger animate-pulse-slow': state === 'critical',
    },
    className
  );
  
  const iconWeight = state === 'critical' ? 'bold' : 'regular';
  
  return (
    <div className={timerClasses} role="timer" aria-live="polite">
      <Clock size={16} weight={iconWeight} />
      <span>{timeString}</span>
    </div>
  );
};

export default Timer;
