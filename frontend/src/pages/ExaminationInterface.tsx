import React, { useState, useEffect, useCallback } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  BookmarkSimple, 
  Flag,
  Clock,
  Warning,
  CheckCircle
} from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import OptionCard from '../components/ui/OptionCard';
import QuestionNavigationGrid from '../components/ui/QuestionNavigationGrid';
import Timer from '../components/ui/Timer';

interface Question {
  id: number;
  stem: string;
  options: {
    id: string;
    label: string;
    text: string;
  }[];
  imageUrl?: string;
}

interface ExamState {
  examId: string;
  courseCode: string;
  courseTitle: string;
  studentName: string;
  matricNumber: string;
  duration: number; // in seconds
  questions: Question[];
  currentQuestion: number;
  answers: Record<number, string>;
  flaggedQuestions: number[];
  startTime: Date;
  timeRemaining: number;
  isSubmitted: boolean;
}

const ExaminationInterface: React.FC = () => {
  // Mock exam data - replace with actual API data
  const [examState, setExamState] = useState<ExamState>({
    examId: 'exam-123',
    courseCode: 'GST 111',
    courseTitle: 'Communication in English',
    studentName: 'Chiamaka Okafor',
    matricNumber: 'MIC/2024/023',
    duration: 7200, // 2 hours in seconds
    questions: [
      {
        id: 1,
        stem: "Which of the following is NOT a component of effective communication?",
        options: [
          { id: 'a', label: 'A', text: 'Sender' },
          { id: 'b', label: 'B', text: 'Message' },
          { id: 'c', label: 'C', text: 'Noise' },
          { id: 'd', label: 'D', text: 'Receiver' }
        ]
      },
      {
        id: 2,
        stem: "The process of converting ideas into words is called:",
        options: [
          { id: 'a', label: 'A', text: 'Encoding' },
          { id: 'b', label: 'B', text: 'Decoding' },
          { id: 'c', label: 'C', text: 'Transmission' },
          { id: 'd', label: 'D', text: 'Feedback' }
        ]
      },
      // Add more questions as needed
    ],
    currentQuestion: 1,
    answers: {},
    flaggedQuestions: [],
    startTime: new Date(),
    timeRemaining: 7200,
    isSubmitted: false
  });

  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('connected');
  const [lastSyncTime, setLastSyncTime] = useState<Date>(new Date());

  // Timer effect
  useEffect(() => {
    if (examState.isSubmitted || examState.timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setExamState(prev => {
        const newTimeRemaining = Math.max(0, prev.timeRemaining - 1);
        
        // Show time warning at 15 minutes
        if (newTimeRemaining === 900 && !showTimeWarning) {
          setShowTimeWarning(true);
        }
        
        // Auto-submit when time expires
        if (newTimeRemaining === 0) {
          handleSubmitExam();
          return { ...prev, timeRemaining: 0, isSubmitted: true };
        }
        
        return { ...prev, timeRemaining: newTimeRemaining };
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [examState.isSubmitted, showTimeWarning]);

  // Auto-save effect
  useEffect(() => {
    if (examState.isSubmitted) return;

    const saveTimer = setInterval(() => {
      saveProgress();
    }, 30000); // Save every 30 seconds

    return () => clearInterval(saveTimer);
  }, [examState.answers, examState.flaggedQuestions, examState.currentQuestion]);

  const saveProgress = useCallback(async () => {
    try {
      // TODO: Implement actual save API call
      console.log('Saving progress:', {
        answers: examState.answers,
        flaggedQuestions: examState.flaggedQuestions,
        currentQuestion: examState.currentQuestion
      });
      
      setLastSyncTime(new Date());
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Failed to save progress:', error);
      setConnectionStatus('disconnected');
    }
  }, [examState]);

  const handleAnswerSelect = useCallback((questionId: number, optionId: string) => {
    setExamState(prev => ({
      ...prev,
      answers: { ...prev.answers, [questionId]: optionId }
    }));
    
    // Immediate save indicator
    setTimeout(() => saveProgress(), 100);
  }, [saveProgress]);

  const handleQuestionNavigation = useCallback((questionNumber: number) => {
    setExamState(prev => ({ ...prev, currentQuestion: questionNumber }));
  }, []);

  const handleFlagQuestion = useCallback(() => {
    setExamState(prev => {
      const isFlagged = prev.flaggedQuestions.includes(prev.currentQuestion);
      const newFlagged = isFlagged
        ? prev.flaggedQuestions.filter(q => q !== prev.currentQuestion)
        : [...prev.flaggedQuestions, prev.currentQuestion];
      
      return { ...prev, flaggedQuestions: newFlagged };
    });
  }, []);

  const handlePreviousQuestion = useCallback(() => {
    setExamState(prev => ({
      ...prev,
      currentQuestion: Math.max(1, prev.currentQuestion - 1)
    }));
  }, []);

  const handleNextQuestion = useCallback(() => {
    setExamState(prev => ({
      ...prev,
      currentQuestion: Math.min(prev.questions.length, prev.currentQuestion + 1)
    }));
  }, []);

  const handleSubmitExam = useCallback(async () => {
    try {
      // TODO: Implement actual submit API call
      console.log('Submitting exam:', examState);
      
      setExamState(prev => ({ ...prev, isSubmitted: true }));
    } catch (error) {
      console.error('Failed to submit exam:', error);
    }
  }, [examState]);

  const currentQuestionData = examState.questions.find(q => q.id === examState.currentQuestion);
  const answeredQuestions = Object.keys(examState.answers).map(Number);
  const unansweredCount = examState.questions.length - answeredQuestions.length;

  if (examState.isSubmitted) {
    return (
      <div className="min-h-screen bg-surface-grey flex items-center justify-center p-8">
        <Card elevation={2} className="max-w-md w-full p-8 text-center">
          <CheckCircle size={64} weight="duotone" className="text-success mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-text-primary mb-2">
            Your examination has been submitted successfully
          </h2>
          <p className="text-text-secondary mb-6">
            Your answers have been recorded. Results will be available after the examination window closes.
          </p>
          <Button variant="secondary" size="md" onClick={() => window.location.href = '/dashboard'}>
            Return to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-grey flex">
      {/* Skip to main content for accessibility */}
      <a href="#question-content" className="skip-to-main">
        Skip to question content
      </a>

      {/* Top Bar */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-primary-blue-800 text-white flex items-center justify-between px-6 z-50">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="font-semibold">{examState.courseCode} – {examState.courseTitle}</h1>
            <p className="text-sm opacity-90">Candidate: {examState.studentName}</p>
          </div>
        </div>
        
        <Timer timeRemaining={examState.timeRemaining} />
      </header>

      {/* Time Warning Banner */}
      {showTimeWarning && examState.timeRemaining <= 900 && examState.timeRemaining > 300 && (
        <div className="fixed top-14 left-0 right-0 bg-amber-50 border-b border-amber-200 p-3 z-40">
          <div className="container-fluid flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Warning size={20} weight="bold" className="text-warning" />
              <span className="text-warning font-medium">
                Time is running out. We recommend reviewing your unanswered questions.
              </span>
            </div>
            <Button 
              variant="tertiary" 
              size="sm"
              onClick={() => {
                const firstUnanswered = examState.questions.find(q => !answeredQuestions.includes(q.id));
                if (firstUnanswered) {
                  handleQuestionNavigation(firstUnanswered.id);
                }
              }}
            >
              Go to First Unanswered
            </Button>
          </div>
        </div>
      )}

      {/* Connection Status Banner */}
      {connectionStatus === 'disconnected' && (
        <div className="fixed top-14 left-0 right-0 bg-amber-50 border-b border-amber-200 p-3 z-40">
          <div className="container-fluid flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Warning size={20} weight="bold" className="text-warning" />
              <span className="text-warning">
                Connection lost. Your answers are saved on your device and will sync when the connection is restored.
              </span>
            </div>
            <span className="text-sm text-text-secondary">
              Last synced {Math.floor((new Date().getTime() - lastSyncTime.getTime()) / 1000)}s ago
            </span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex pt-14">
        {/* Question Navigation Sidebar */}
        <aside className="hidden md:block w-60 bg-surface-white border-r border-surface-grey-dark p-6 overflow-y-auto">
          <QuestionNavigationGrid
            totalQuestions={examState.questions.length}
            currentQuestion={examState.currentQuestion}
            answeredQuestions={answeredQuestions}
            flaggedQuestions={examState.flaggedQuestions}
            onQuestionSelect={handleQuestionNavigation}
          />
        </aside>

        {/* Question Panel */}
        <main id="question-content" className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-4xl mx-auto">
            <Card elevation={1} className="p-8">
              {/* Question Header */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-sm text-text-secondary">
                    Question {examState.currentQuestion} of {examState.questions.length}
                  </div>
                  <button
                    onClick={handleFlagQuestion}
                    className={`flex items-center gap-2 px-3 py-1 rounded-md text-sm font-medium transition-colors duration-150 ${
                      examState.flaggedQuestions.includes(examState.currentQuestion)
                        ? 'bg-amber-100 text-warning hover:bg-amber-200'
                        : 'bg-surface-grey text-text-secondary hover:bg-surface-grey-dark'
                    }`}
                  >
                    <Flag size={16} weight={examState.flaggedQuestions.includes(examState.currentQuestion) ? 'fill' : 'regular'} />
                    {examState.flaggedQuestions.includes(examState.currentQuestion) ? 'Flagged' : 'Flag for Review'}
                  </button>
                </div>
              </div>

              {/* Question Content */}
              {currentQuestionData && (
                <div className="space-y-6">
                  {/* Question Stem */}
                  <div className="font-lora text-lg text-text-primary leading-relaxed">
                    {currentQuestionData.stem}
                  </div>

                  {/* Question Image (if any) */}
                  {currentQuestionData.imageUrl && (
                    <div className="my-6">
                      <img 
                        src={currentQuestionData.imageUrl} 
                        alt="Question image" 
                        className="max-w-full h-auto border border-surface-grey-dark rounded"
                      />
                    </div>
                  )}

                  {/* Options */}
                  <div className="space-y-3">
                    {currentQuestionData.options.map((option) => (
                      <OptionCard
                        key={option.id}
                        id={option.id}
                        label={option.label}
                        selected={examState.answers[examState.currentQuestion] === option.id}
                        onClick={() => handleAnswerSelect(examState.currentQuestion, option.id)}
                      >
                        {option.text}
                      </OptionCard>
                    ))}
                  </div>
                </div>
              )}

              {/* Navigation Controls */}
              <div className="flex items-center justify-between mt-8 pt-6 border-t border-surface-grey-dark">
                <Button
                  variant="secondary"
                  size="md"
                  onClick={handlePreviousQuestion}
                  disabled={examState.currentQuestion === 1}
                >
                  <ArrowLeft size={16} weight="bold" className="mr-2" />
                  Previous
                </Button>

                <div className="flex items-center gap-4">
                  {examState.currentQuestion === examState.questions.length ? (
                    <Button
                      variant="primary"
                      size="md"
                      onClick={() => setShowSubmitConfirm(true)}
                      className="bg-danger hover:bg-red-700 focus:ring-danger"
                    >
                      Submit Exam
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      size="md"
                      onClick={handleNextQuestion}
                    >
                      Next
                      <ArrowRight size={16} weight="bold" className="ml-2" />
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          </div>
        </main>
      </div>

      {/* Submit Confirmation Modal */}
      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-text-primary mb-4">
              Submit Examination
            </h3>
            <p className="text-text-secondary mb-6">
              You are about to submit your examination. You have answered {answeredQuestions.length} of {examState.questions.length} questions. 
              {unansweredCount > 0 && ` ${unansweredCount} questions are unanswered.`}
              This action cannot be undone.
            </p>
            
            <div className="space-y-4">
              <label className="flex items-center gap-2">
                <input 
                  type="checkbox" 
                  className="rounded border-surface-grey-dark"
                  onChange={(e) => {
                    // Enable submit button only when checkbox is checked
                    const submitBtn = document.getElementById('confirm-submit-btn') as HTMLButtonElement;
                    if (submitBtn) {
                      submitBtn.disabled = !e.target.checked;
                    }
                  }}
                />
                <span className="text-sm text-text-primary">
                  I understand this cannot be undone
                </span>
              </label>
              
              <div className="flex gap-3 justify-end">
                <Button
                  variant="secondary"
                  size="md"
                  onClick={() => setShowSubmitConfirm(false)}
                >
                  Cancel
                </Button>
                <Button
                  id="confirm-submit-btn"
                  variant="primary"
                  size="md"
                  onClick={() => {
                    setShowSubmitConfirm(false);
                    handleSubmitExam();
                  }}
                  disabled={true}
                  className="bg-danger hover:bg-red-700 focus:ring-danger"
                >
                  Submit Exam
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Mobile Navigation Grid */}
      <div className="md:hidden fixed bottom-20 right-4 z-40">
        <Button
          variant="primary"
          size="md"
          className="rounded-full w-14 h-14"
          onClick={() => {
            // TODO: Implement mobile bottom sheet
            console.log('Open mobile navigation grid');
          }}
        >
          {examState.currentQuestion}
        </Button>
      </div>
    </div>
  );
};

export default ExaminationInterface;
