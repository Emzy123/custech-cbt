import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Flag, Warning, CheckCircle, LockKey, WifiSlash } from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import OptionCard from '../components/ui/OptionCard';
import QuestionNavigationGrid from '../components/ui/QuestionNavigationGrid';
import Timer from '../components/ui/Timer';
import { apiRequest } from '../lib/api';

interface OfflineQueueItem {
  instanceId: string;
  payload: object;
}

interface PaperOption {
  id: string;
  label: string;
  text: string;
}

interface PaperQuestion {
  sequence: number;
  id: string;
  stem: string;
  options: PaperOption[];
}

interface ExamPayload {
  attempt_id: number;
  exam: {
    id: number;
    course_code: string;
    course_title: string;
    duration_minutes: number;
  };
  questions: PaperQuestion[];
}

interface ActiveAttemptResponse {
  attempt_id: number | null;
}

interface StartAttemptResponse {
  attempt_id?: string;
  instance_id?: string;
}

interface AttemptClockResponse {
  attempt_id?: number;
  status?: string;
  server_now?: string;
  ends_at?: string | null;
  paused?: boolean;
  submitted_at?: string;
}

const ExaminationInterface: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const [instanceId, setInstanceId] = useState<string | null>(null);
  const [preExamStep, setPreExamStep] = useState<'rules' | 'ready' | 'exam'>('rules');
  const [rulesAccepted, setRulesAccepted] = useState(false);
  const [examState, setExamState] = useState({
    examId: examId || '',
    courseCode: '',
    courseTitle: '',
    durationSeconds: 3600,
    questions: [] as PaperQuestion[],
    currentQuestion: 1,
    answers: {} as Record<number, string>,
    flaggedQuestions: [] as number[],
    timeRemaining: 3600,
    isSubmitted: false,
  });

  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [isSubmitAgreementChecked, setIsSubmitAgreementChecked] = useState(false);
  const [showTimeWarning, setShowTimeWarning] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('connected');
  const [lastSyncTime, setLastSyncTime] = useState<Date>(new Date());
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const submittingRef = useRef(false);
  const autoFinalizeRef = useRef(false);
  const offlineQueueRef = useRef<OfflineQueueItem[]>([]);

  // Drain offline queue when back online
  const drainOfflineQueue = useCallback(async (currentInstanceId: string) => {
    const queue = [...offlineQueueRef.current];
    offlineQueueRef.current = [];
    for (const item of queue) {
      try {
        await apiRequest(`/api/v1/examinations/${examId}/instances/${currentInstanceId}/answers`, {
          method: 'POST',
          body: JSON.stringify(item.payload),
        });
      } catch {
        offlineQueueRef.current.push(item); // re-queue on failure
      }
    }
  }, [examId]);

  // Bootstrap: start instance, then load paper
  useEffect(() => {
    const bootstrapExam = async () => {
      if (!examId || preExamStep !== 'exam') return;
      try {
        localStorage.setItem('activeExamId', examId);

        const started = await apiRequest<StartAttemptResponse>(`/api/v1/examinations/${examId}/start`, {
          method: 'POST',
          body: JSON.stringify({ rules_accepted: true }),
        });
        const nextInstanceId = String(started.attempt_id ?? started.instance_id ?? '');
        if (!nextInstanceId) {
          throw new Error('Exam could not be started (no instance id returned)');
        }
        setInstanceId(nextInstanceId);

        const paper = await apiRequest<ExamPayload>(`/api/v1/examinations/${examId}/instances/${nextInstanceId}/paper`);
        const durationSeconds = Math.max(60, (paper.exam.duration_minutes || 60) * 60);

        setExamState((prev) => ({
          ...prev,
          examId,
          courseCode: paper.exam.course_code,
          courseTitle: paper.exam.course_title,
          durationSeconds,
          questions: paper.questions,
          timeRemaining: durationSeconds,
          currentQuestion: 1,
          answers: {},
          flaggedQuestions: [],
          isSubmitted: false,
        }));
        setLoading(false);
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : 'Failed to load examination');
        setLoading(false);
      }
    };

    void bootstrapExam();
  }, [examId, preExamStep, drainOfflineQueue]);

  useEffect(() => {
    if (!instanceId || examState.isSubmitted) {
      return;
    }

    const syncClock = async () => {
      try {
        const clock = await apiRequest<AttemptClockResponse>(`/api/v1/examinations/${examId}/instances/${instanceId}/clock`);
        if (clock.status && ['timed_out', 'submitted', 'terminated'].includes(clock.status)) {
          setExamState((prev) => ({ ...prev, isSubmitted: true, timeRemaining: 0 }));
          return;
        }
        if (clock.ends_at && clock.server_now) {
          const end = new Date(clock.ends_at).getTime();
          const now = new Date(clock.server_now).getTime();
          const seconds = Math.max(0, Math.floor((end - now) / 1000));
          setExamState((prev) => {
            const next = { ...prev, timeRemaining: seconds };
            if (seconds <= 900 && !showTimeWarning) {
              setShowTimeWarning(true);
            }
            return next;
          });
        }
        setConnectionStatus('connected');
        setLastSyncTime(new Date());
        if (offlineQueueRef.current.length > 0) {
          await drainOfflineQueue(instanceId);
        }
      } catch {
        setConnectionStatus('disconnected');
      }
    };

    // Sync with server every 30 seconds
    void syncClock();
    const serverSyncHandle = window.setInterval(() => {
      void syncClock();
    }, 30_000);

    // Count down locally every second
    const localTickHandle = window.setInterval(() => {
      setExamState((prev) => {
        if (prev.isSubmitted || prev.timeRemaining <= 0) return prev;
        const next = prev.timeRemaining - 1;
        if (next <= 900 && !showTimeWarning) {
          setShowTimeWarning(true);
        }
        return { ...prev, timeRemaining: next };
      });
    }, 1_000);

    return () => {
      window.clearInterval(serverSyncHandle);
      window.clearInterval(localTickHandle);
    };
  }, [instanceId, examId, examState.isSubmitted, showTimeWarning, drainOfflineQueue]);



  const answeredQuestions = useMemo(
    () =>
      Object.entries(examState.answers)
        .filter(([, value]) => Boolean(value))
        .map(([key]) => Number(key)),
    [examState.answers],
  );

  const unansweredCount = examState.questions.length - answeredQuestions.length;

  const saveProgress = useCallback(async () => {
    try {
      localStorage.setItem(
        `exam-progress-${examState.examId}`,
        JSON.stringify({
          answers: examState.answers,
          flaggedQuestions: examState.flaggedQuestions,
          currentQuestion: examState.currentQuestion,
          updatedAt: new Date().toISOString(),
        }),
      );
      setLastSyncTime(new Date());
      setConnectionStatus('connected');
    } catch {
      setConnectionStatus('disconnected');
    }
  }, [examState]);

  const persistAnswer = useCallback(
    async (questionIndex: number, optionId: string, isFlagged: boolean) => {
      if (!instanceId) return;
      const question = examState.questions[questionIndex - 1];
      if (!question) return;

      const payload = {
        question_id: question.id,
        selected_option_id: optionId,
        is_flagged: isFlagged,
        idempotency_key: `${instanceId}-${question.id}`,
      };

      try {
        await apiRequest(`/api/v1/examinations/${examId}/instances/${instanceId}/answers`, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        setLastSyncTime(new Date());
        setConnectionStatus('connected');
      } catch {
        // Queue for replay when back online
        offlineQueueRef.current.push({ instanceId, payload });
        setConnectionStatus('disconnected');
      }
    },
    [instanceId, examId, examState.questions],
  );

  const handleAnswerSelect = useCallback(
    async (questionIndex: number, optionId: string) => {
      setExamState((prev) => ({
        ...prev,
        answers: { ...prev.answers, [questionIndex]: optionId },
      }));

      try {
        await persistAnswer(questionIndex, optionId, examState.flaggedQuestions.includes(questionIndex));
      } catch {
        setConnectionStatus('disconnected');
      }

      window.setTimeout(() => {
        void saveProgress();
      }, 150);
    },
    [examState.flaggedQuestions, persistAnswer, saveProgress],
  );

  const handleQuestionNavigation = useCallback((questionNumber: number) => {
    setExamState((prev) => ({ ...prev, currentQuestion: questionNumber }));
  }, []);

  const handleFlagQuestion = useCallback(async () => {
    const questionIndex = examState.currentQuestion;
    const selectedOptionId = examState.answers[questionIndex];
    const wasFlagged = examState.flaggedQuestions.includes(questionIndex);
    const nextFlagged = wasFlagged
      ? examState.flaggedQuestions.filter((q) => q !== questionIndex)
      : [...examState.flaggedQuestions, questionIndex];

    setExamState((prev) => ({
      ...prev,
      flaggedQuestions: nextFlagged,
    }));

    if (!instanceId || !selectedOptionId) {
      return;
    }

    try {
      await persistAnswer(questionIndex, selectedOptionId, nextFlagged.includes(questionIndex));
    } catch {
      setConnectionStatus('disconnected');
    }
  }, [instanceId, examState.answers, examState.currentQuestion, examState.flaggedQuestions, persistAnswer]);

  const handlePreviousQuestion = useCallback(() => {
    setExamState((prev) => ({
      ...prev,
      currentQuestion: Math.max(1, prev.currentQuestion - 1),
    }));
  }, []);

  const handleNextQuestion = useCallback(() => {
    setExamState((prev) => ({
      ...prev,
      currentQuestion: Math.min(prev.questions.length, prev.currentQuestion + 1),
    }));
  }, []);

  const handleSubmitExam = useCallback(async () => {
    if (!instanceId || submittingRef.current) return;
    submittingRef.current = true;
    try {
      await apiRequest(`/api/v1/examinations/${examId}/instances/${instanceId}/submit`, {
        method: 'POST',
        body: JSON.stringify({
          answers: [],
          submission_time: new Date().toISOString(),
        }),
      });
      setExamState((prev) => ({ ...prev, isSubmitted: true, timeRemaining: 0 }));
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Failed to submit exam');
    } finally {
      submittingRef.current = false;
    }
  }, [instanceId, examId]);

  useEffect(() => {
    if (examState.timeRemaining > 0 || examState.isSubmitted || !instanceId || autoFinalizeRef.current) {
      return;
    }
    autoFinalizeRef.current = true;
    void handleSubmitExam();
  }, [instanceId, examState.isSubmitted, examState.timeRemaining, handleSubmitExam]);

  if (loadError) {
    return (
      <div className="min-h-screen bg-light flex items-center justify-center p-8">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-heading mb-2">Unable to load exam</h2>
          <p className="text-body mb-4">{loadError}</p>
          <Button variant="secondary" size="md" onClick={() => navigate('/dashboard')}>
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  // Rules acceptance step
  if (preExamStep === 'rules') {
    return (
      <div className="min-h-screen bg-light flex items-center justify-center p-4">
        <Card elevation={2} className="max-w-2xl w-full p-8">
          <div className="text-center mb-6">
            <LockKey size={32} weight="duotone" className="text-custech-primary mx-auto mb-4" />
            <h1 className="text-2xl font-semibold text-heading">Examination Rules & Instructions</h1>
            <p className="text-body mt-2">Please read and accept the following rules to begin your examination</p>
          </div>
          
          <ol className="space-y-3 text-body list-decimal list-inside mb-8">
            <li>Ensure you complete the examination within the allotted countdown time.</li>
            <li>All questions are multiple-choice. Select the best option for each question.</li>
            <li>Ensure you submit your answers by clicking "Submit Exam" when done.</li>
            <li>If your time expires, your current progress will be automatically submitted.</li>
            <li>Make sure you have a stable connection throughout the session.</li>
          </ol>
          
          <label className="flex items-start gap-3 mb-6 cursor-pointer">
            <input
              type="checkbox"
              id="rules-accept"
              className="mt-1 rounded border-default"
              checked={rulesAccepted}
              onChange={(e) => setRulesAccepted(e.target.checked)}
            />
            <span className="text-heading font-medium">I have read and agree to abide by all examination rules stated above.</span>
          </label>
          
          <div className="flex justify-end">
            <Button
              variant="primary"
              size="md"
              disabled={!rulesAccepted}
              onClick={() => {
                document.documentElement.requestFullscreen?.().catch(() => undefined);
                setPreExamStep('exam');
              }}
            >
              Begin Examination
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-light flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-custech-primary mx-auto mb-4"></div>
          <p className="text-body">Loading question bank...</p>
        </div>
      </div>
    );
  }

  if (examState.isSubmitted) {
    return (
      <div className="min-h-screen bg-light flex items-center justify-center p-8">
        <Card elevation={2} className="max-w-md w-full p-8 text-center">
          <CheckCircle size={64} weight="duotone" className="text-success mx-auto mb-4" />
          <h2 className="text-2xl font-semibold text-heading mb-2">
            Your examination has been submitted successfully
          </h2>
          <p className="text-body mb-6">
            Your answers have been recorded. Results will be available after the examination window closes.
          </p>
          <Button variant="secondary" size="md" onClick={() => navigate('/dashboard')}>
            Return to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-light flex">
      <a href="#question-content" className="skip-to-main">
        Skip to question content
      </a>

      <header className="fixed top-0 left-0 right-0 h-14 bg-custech-primary text-white flex items-center justify-between px-6 z-50">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="font-semibold">
              {examState.courseCode} – {examState.courseTitle}
            </h1>
          </div>
        </div>

        <Timer timeRemaining={examState.timeRemaining} />
      </header>

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
              variant="outline"
              size="sm"
              onClick={() => {
                const firstUnanswered = examState.questions.find(
                  (_, idx) => !examState.answers[idx + 1],
                );
                if (firstUnanswered) {
                  handleQuestionNavigation(firstUnanswered.sequence);
                }
              }}
            >
              Go to First Unanswered
            </Button>
          </div>
        </div>
      )}

      {connectionStatus === 'disconnected' && (
        <div className="fixed top-14 left-0 right-0 bg-amber-50 border-b border-amber-200 p-3 z-40">
          <div className="container-fluid flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Warning size={20} weight="bold" className="text-warning" />
              <span className="text-warning">
                Connection lost. Your answers are saved on your device and will sync when the connection is restored.
              </span>
            </div>
            <span className="text-sm text-body">
              Last synced {Math.floor((new Date().getTime() - lastSyncTime.getTime()) / 1000)}s ago
            </span>
          </div>
        </div>
      )}

      <div className="flex-1 flex pt-14">
        <aside className="hidden md:block w-60 bg-white border-r border-default p-6 overflow-y-auto">
          <QuestionNavigationGrid
            totalQuestions={examState.questions.length}
            currentQuestion={examState.currentQuestion}
            answeredQuestions={answeredQuestions}
            flaggedQuestions={examState.flaggedQuestions}
            onQuestionSelect={handleQuestionNavigation}
          />
        </aside>

        <main id="question-content" className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-4xl mx-auto">
            <Card elevation={1} className="p-8">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-sm text-body">
                    Question {examState.currentQuestion} of {examState.questions.length}
                  </div>
                  <button
                    type="button"
                    onClick={() => void handleFlagQuestion()}
                    className={`flex items-center gap-2 px-3 py-1 rounded-md text-sm font-medium transition-colors duration-150 ${
                      examState.flaggedQuestions.includes(examState.currentQuestion)
                        ? 'bg-amber-100 text-warning hover:bg-amber-200'
                        : 'bg-light text-body hover:bg-light-dark'
                    }`}
                  >
                    <Flag
                      size={16}
                      weight={examState.flaggedQuestions.includes(examState.currentQuestion) ? 'fill' : 'regular'}
                    />
                    {examState.flaggedQuestions.includes(examState.currentQuestion) ? 'Flagged' : 'Flag for Review'}
                  </button>
                </div>
              </div>

              {(() => {
                const currentQuestionData = examState.questions.find(q => q.sequence === examState.currentQuestion);
                return currentQuestionData && (
                <div className="space-y-6">
                  <div className="font-lora text-lg text-heading leading-relaxed">{currentQuestionData.stem}</div>

                  <div className="space-y-3">
                    {currentQuestionData.options.map((option) => (
                      <OptionCard
                        key={`${currentQuestionData.id}-${option.label}`}
                        id={`${currentQuestionData.id}-${option.label}`}
                        label={option.label}
                        selected={examState.answers[examState.currentQuestion] === option.id}
                        onClick={() => void handleAnswerSelect(examState.currentQuestion, option.id)}
                      >
                        {option.text}
                      </OptionCard>
                    ))}
                  </div>
                </div>
                );
              })()}

              <div className="flex items-center justify-between mt-8 pt-6 border-t border-default">
                <Button variant="secondary" size="md" onClick={handlePreviousQuestion} disabled={examState.currentQuestion === 1}>
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
                    <Button variant="primary" size="md" onClick={handleNextQuestion}>
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

      {showSubmitConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-heading mb-4">Submit Examination</h3>
            <p className="text-body mb-6">
              You are about to submit your examination. You have answered {answeredQuestions.length} of{' '}
              {examState.questions.length} questions.
              {unansweredCount > 0 && ` ${unansweredCount} questions are unanswered.`} This action cannot be undone.
            </p>

            <div className="space-y-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="rounded border-default"
                  checked={isSubmitAgreementChecked}
                  onChange={(e) => setIsSubmitAgreementChecked(e.target.checked)}
                />
                <span className="text-sm text-heading">I understand this cannot be undone</span>
              </label>

              <div className="flex gap-3 justify-end">
                <Button variant="secondary" size="md" onClick={() => { setShowSubmitConfirm(false); setIsSubmitAgreementChecked(false); }}>
                  Cancel
                </Button>
                <Button
                  id="confirm-submit-btn"
                  variant="primary"
                  size="md"
                  onClick={() => {
                    setShowSubmitConfirm(false);
                    setIsSubmitAgreementChecked(false);
                    void handleSubmitExam();
                  }}
                  disabled={!isSubmitAgreementChecked}
                  className="bg-danger hover:bg-red-700 focus:ring-danger"
                >
                  Submit Exam
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="md:hidden fixed bottom-20 right-4 z-40">
        <Button variant="primary" size="md" className="rounded-full w-14 h-14">
          {examState.currentQuestion}
        </Button>
      </div>
    </div>
  );
};

export default ExaminationInterface;
