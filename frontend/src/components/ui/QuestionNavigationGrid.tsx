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
        'border-surface-grey-dark text-text-secondary': !isAnswered && !isCurrent,
        'bg-info text-surface-white border-info': isAnswered && !isCurrent,
        'ring-2 ring-info ring-offset-2': isCurrent && !isAnswered,
        'bg-info text-surface-white border-info ring-2 ring-info ring-offset-2': isCurrent && isAnswered,
        'hover:border-info': !isCurrent,
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
            className="absolute -top-1 -right-1 text-warning"
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
      <div className="text-sm font-medium text-text-secondary">
        Questions
      </div>
      
      <div className="grid grid-cols-5 gap-2">
        {Array.from({ length: totalQuestions }, (_, i) => i + 1).map(renderQuestionBox)}
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-text-secondary">Answered:</span>
          <span className="font-medium text-text-primary">{answeredCount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Unanswered:</span>
          <span className="font-medium text-text-primary">{unansweredCount}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Flagged:</span>
          <span className="font-medium text-warning">{flaggedCount}</span>
        </div>
      </div>
    </div>
  );
};

export default QuestionNavigationGrid;
