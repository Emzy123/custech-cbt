import React from 'react';
import { BookmarkSimple } from '@phosphor-icons/react';
import clsx from 'clsx';

interface QuestionNavigationGridProps {
  totalQuestions: number;
  currentQuestion: number;
  answeredQuestions: number[];
  flaggedQuestions: number[];
  onQuestionSelect: (questionNumber: number) => void;
  className?: string;
}

const QuestionNavigationGrid: React.FC<QuestionNavigationGridProps> = ({
  totalQuestions,
  currentQuestion,
  answeredQuestions,
  flaggedQuestions,
  onQuestionSelect,
  className
}) => {
  const renderQuestionBox = (questionNumber: number) => {
    const isAnswered = answeredQuestions.includes(questionNumber);
    const isCurrent = questionNumber === currentQuestion;
    const isFlagged = flaggedQuestions.includes(questionNumber);
    
    const boxClasses = clsx(
      'w-10 h-10 border-2 rounded-md flex items-center justify-center text-sm font-medium cursor-pointer transition-all duration-150 relative',
      {
        'border-default text-muted': !isAnswered && !isCurrent,
        'bg-custech-navy text-white border-custech-navy': isAnswered && !isCurrent,
        'ring-2 ring-custech-navy ring-offset-2': isCurrent && !isAnswered,
        'bg-custech-navy text-white border-custech-navy ring-2 ring-custech-navy ring-offset-2': isCurrent && isAnswered,
        'hover:border-custech-navy': !isCurrent,
      }
    );
    
    return (
      <button
        key={questionNumber}
        className={boxClasses}
        onClick={() => onQuestionSelect(questionNumber)}
        aria-label={`Question ${questionNumber}${isAnswered ? ' answered' : ''}${isCurrent ? ' current' : ''}${isFlagged ? ' flagged' : ''}`}
        aria-pressed={isCurrent}
      >
        {questionNumber}
        {isFlagged && (
          <BookmarkSimple 
            size={12} 
            weight="fill" 
            className="absolute -top-1 -right-1 text-custech-gold"
            aria-hidden="true"
          />
        )}
      </button>
    );
  };
  
  const answeredCount = answeredQuestions.length;
  const unansweredCount = totalQuestions - answeredCount;
  const flaggedCount = flaggedQuestions.length;
  
  return (
    <div className={clsx('space-y-4', className)}>
      <div className="text-sm font-medium text-body">
        Questions
      </div>
      
      <div className="grid grid-cols-5 gap-2">
        {Array.from({ length: totalQuestions }, (_, i) => i + 1).map(renderQuestionBox)}
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-body">Answered:</span>
          <span className="font-medium text-heading">{answeredCount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-body">Unanswered:</span>
          <span className="font-medium text-heading">{unansweredCount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-body">Flagged:</span>
          <span className="font-medium text-custech-gold">{flaggedCount}</span>
        </div>
      </div>
    </div>
  );
};

export default QuestionNavigationGrid;
