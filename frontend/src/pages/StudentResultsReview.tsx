import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  BookOpen,
  Question,
  Hourglass,
  ArrowSquareOut
} from '@phosphor-icons/react';
import { apiRequest } from '../lib/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

interface OptionReview {
  id: string;
  option_text: string;
  is_correct: boolean;
}

interface AnswerReview {
  question_id: string;
  question_text: string;
  selected_option_id: string | null;
  answer_text: string | null;
  is_correct: boolean | null;
  points_earned: number;
  time_spent: number;
  options: OptionReview[];
  correct_option_id: string | null;
  explanation: string;
}

interface ExamReview {
  instance_id: string;
  exam_title: string;
  student_name: string;
  start_time: string;
  end_time: string;
  duration_taken: number; // in seconds
  total_points: number;
  points_earned: number;
  percentage_score: number;
  grade: string;
  passed: boolean;
  answers: AnswerReview[];
}

const StudentResultsReview: React.FC = () => {
  const { examId, instanceId } = useParams<{ examId: string; instanceId: string }>();
  const navigate = useNavigate();
  const [review, setReview] = useState<ExamReview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Interactive filters
  const [activeFilter, setActiveFilter] = useState<'all' | 'correct' | 'incorrect' | 'unanswered'>('all');
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);

  useEffect(() => {
    const fetchReviewData = async () => {
      try {
        setLoading(true);
        if (!examId || !instanceId) {
          throw new Error('Missing examination or instance identifier.');
        }
        const data = await apiRequest<ExamReview>(`/api/v1/examinations/${examId}/instances/${instanceId}/review`);
        setReview(data);
        if (data.answers && data.answers.length > 0) {
          setSelectedQuestionId(data.answers[0].question_id);
        }
      } catch (err: any) {
        console.error('Error fetching review:', err);
        setError(err.message || 'Failed to load exam review data.');
      } finally {
        setLoading(false);
      }
    };

    fetchReviewData();
  }, [examId, instanceId]);

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getStatusColor = (isCorrect: boolean | null, selected: string | null) => {
    if (!selected) return 'border-amber-200 bg-amber-50/50 dark:border-amber-900/30 dark:bg-amber-950/10 text-amber-800 dark:text-amber-300';
    return isCorrect
      ? 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/30 dark:bg-emerald-950/10 text-emerald-800 dark:text-emerald-300'
      : 'border-rose-200 bg-rose-50/50 dark:border-rose-900/30 dark:bg-rose-950/10 text-rose-800 dark:text-rose-300';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-light dark:bg-bg-dark flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-t-custech-primary border-r-custech-primary border-b-transparent border-l-transparent"></div>
          <p className="text-body font-medium animate-pulse">Loading review details...</p>
        </div>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="min-h-screen bg-bg-light dark:bg-bg-dark flex items-center justify-center p-6">
        <Card className="max-w-md w-full p-8 text-center" elevation={2}>
          <XCircle size={64} className="text-danger mx-auto mb-4" weight="duotone" />
          <h3 className="text-xl font-bold text-heading mb-2">Error Loading Review</h3>
          <p className="text-body mb-6">{error || 'Review data is unavailable at this time.'}</p>
          <Button variant="primary" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  // Filtered answers
  const filteredAnswers = review.answers.filter((ans) => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'correct') return ans.is_correct === true;
    if (activeFilter === 'incorrect') return ans.is_correct === false;
    if (activeFilter === 'unanswered') return ans.selected_option_id === null && ans.answer_text === null;
    return true;
  });

  return (
    <div className="min-h-screen bg-bg-light dark:bg-bg-dark text-text-body font-inter transition-colors duration-200">
      {/* Premium Header */}
      <header className="sticky top-0 z-30 bg-white/80 dark:bg-bg-dark/80 backdrop-blur-md border-b border-border-default dark:border-gray-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 rounded-full text-body hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-150"
              aria-label="Back to Dashboard"
            >
              <ArrowLeft size={22} weight="bold" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase tracking-widest font-semibold text-custech-navy dark:text-sky-400 bg-custech-navy/10 px-2 py-0.5 rounded">
                  Review Mode
                </span>
                <span className="text-xs text-text-muted">ID: {review.instance_id.slice(0, 8)}</span>
              </div>
              <h1 className="text-lg md:text-xl font-bold text-heading mt-0.5 line-clamp-1">
                {review.exam_title}
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-body">
            <div className="hidden sm:block text-right">
              <p className="font-semibold text-heading">{review.student_name}</p>
              <p className="text-xs text-text-muted">Student Account</p>
            </div>
            <div className="w-px h-8 bg-border-default dark:bg-gray-800 hidden sm:block"></div>
            <Button
              variant="outline"
              size="sm"
              className="!py-2 !px-4 text-xs font-semibold"
              onClick={() => navigate('/dashboard')}
            >
              Close Review
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-8 space-y-8 animate-slide-up">
        {/* Overall Performance Metrics Dashboard */}
        <section className="relative overflow-hidden bg-gradient-to-r from-custech-primary to-custech-primary-light text-white rounded-lg shadow-elevation-2 p-6 md:p-8">
          <div className="absolute right-0 top-0 translate-x-12 -translate-y-12 w-64 h-64 bg-white/5 rounded-full blur-2xl pointer-events-none"></div>
          <div className="absolute left-1/3 bottom-0 w-48 h-48 bg-custech-gold/10 rounded-full blur-2xl pointer-events-none"></div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 relative z-10">
            <div className="flex flex-col justify-center">
              <span className="text-xs uppercase tracking-wider text-white/70 font-medium">Performance Score</span>
              <div className="flex items-baseline mt-1 gap-1">
                <span className="text-4xl md:text-5xl font-extrabold text-custech-gold">
                  {review.points_earned}
                </span>
                <span className="text-lg text-white/60">/ {review.total_points}</span>
              </div>
              <span className="text-xs text-white/80 mt-1">Total Points Earned</span>
            </div>

            <div className="flex flex-col justify-center border-l border-white/10 pl-6 md:pl-8">
              <span className="text-xs uppercase tracking-wider text-white/70 font-medium">Success Rate</span>
              <span className="text-4xl md:text-5xl font-extrabold text-white mt-1">
                {review.percentage_score.toFixed(1)}%
              </span>
              <span className="text-xs text-white/80 mt-1">Final Percentage</span>
            </div>

            <div className="flex flex-col justify-center border-l border-white/10 pl-6 md:pl-8">
              <span className="text-xs uppercase tracking-wider text-white/70 font-medium">Earned Grade</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-4xl md:text-5xl font-extrabold text-white">
                  {review.grade || 'N/A'}
                </span>
                <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded ${
                  review.passed 
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                }`}>
                  {review.passed ? 'PASSED' : 'FAILED'}
                </span>
              </div>
              <span className="text-xs text-white/80 mt-1">Academic Result Status</span>
            </div>

            <div className="flex flex-col justify-center border-l border-white/10 pl-6 md:pl-8">
              <span className="text-xs uppercase tracking-wider text-white/70 font-medium">Duration Taken</span>
              <div className="flex items-center gap-2 mt-1">
                <Clock size={28} className="text-custech-gold" />
                <span className="text-2xl md:text-3xl font-extrabold text-white">
                  {formatDuration(review.duration_taken)}
                </span>
              </div>
              <span className="text-xs text-white/80 mt-1">Total Session Time</span>
            </div>
          </div>
        </section>

        {/* Dynamic Navigation/Filter Bar & Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Navigator Panel */}
          <aside className="lg:col-span-4 space-y-6">
            <Card className="sticky top-28 p-6 space-y-6" elevation={1}>
              {/* Review Filters */}
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-heading mb-3">
                  Filter Questions
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'all', label: 'All', count: review.answers.length, color: 'border-gray-200 hover:border-gray-300 bg-gray-50/50 dark:bg-gray-900/50 dark:border-gray-800' },
                    { id: 'correct', label: 'Correct', count: review.answers.filter(a => a.is_correct === true).length, color: 'border-emerald-200 hover:border-emerald-300 bg-emerald-50/30 dark:bg-emerald-950/5 dark:border-emerald-900/20' },
                    { id: 'incorrect', label: 'Incorrect', count: review.answers.filter(a => a.is_correct === false).length, color: 'border-rose-200 hover:border-rose-300 bg-rose-50/30 dark:bg-rose-950/5 dark:border-rose-900/20' },
                    { id: 'unanswered', label: 'Unanswered', count: review.answers.filter(a => a.selected_option_id === null && a.answer_text === null).length, color: 'border-amber-200 hover:border-amber-300 bg-amber-50/30 dark:bg-amber-950/5 dark:border-amber-900/20' }
                  ].map((filter) => (
                    <button
                      key={filter.id}
                      onClick={() => setActiveFilter(filter.id as any)}
                      className={`flex flex-col items-start p-3 rounded-md border text-left transition-all duration-150 ${filter.color} ${
                        activeFilter === filter.id 
                          ? 'ring-2 ring-custech-navy dark:ring-sky-500 scale-[1.02] shadow-sm' 
                          : 'opacity-70 hover:opacity-100'
                      }`}
                    >
                      <span className="text-xs text-text-muted capitalize">{filter.label}</span>
                      <span className="text-lg font-bold text-heading mt-0.5">{filter.count}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Question Navigation Grid */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-heading">
                    Question Grid
                  </h3>
                  <span className="text-xs text-text-muted">
                    Showing {filteredAnswers.length} of {review.answers.length}
                  </span>
                </div>
                
                <div className="grid grid-cols-5 gap-2">
                  {review.answers.map((ans, idx) => {
                    const isFiltered = filteredAnswers.some(f => f.question_id === ans.question_id);
                    const isSelected = selectedQuestionId === ans.question_id;
                    
                    let bgBorderClass = 'bg-gray-100 text-gray-800 border-gray-200';
                    if (ans.selected_option_id === null && ans.answer_text === null) {
                      bgBorderClass = 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-900/40';
                    } else if (ans.is_correct) {
                      bgBorderClass = 'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-900/40';
                    } else {
                      bgBorderClass = 'bg-rose-100 text-rose-800 border-rose-200 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-900/40';
                    }

                    return (
                      <button
                        key={ans.question_id}
                        onClick={() => {
                          setSelectedQuestionId(ans.question_id);
                          // Scroll element into view smoothly if responsive
                          const element = document.getElementById(`q-card-${ans.question_id}`);
                          if (element) {
                            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          }
                        }}
                        className={`w-11 h-11 border-2 rounded-md font-semibold text-sm flex items-center justify-center transition-all duration-150 ${bgBorderClass} ${
                          isSelected 
                            ? 'ring-2 ring-custech-navy dark:ring-sky-400 ring-offset-2 scale-110 shadow-md' 
                            : 'hover:scale-105'
                        } ${!isFiltered ? 'opacity-30' : ''}`}
                      >
                        {idx + 1}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Side Stats */}
              <div className="pt-4 border-t border-border-default dark:border-gray-800 space-y-3 text-xs text-body">
                <div className="flex justify-between">
                  <span>Start Time:</span>
                  <span className="font-semibold text-heading">
                    {new Date(review.start_time).toLocaleTimeString('en-NG', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>End Time:</span>
                  <span className="font-semibold text-heading">
                    {review.end_time ? new Date(review.end_time).toLocaleTimeString('en-NG', { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Avg. Time/Question:</span>
                  <span className="font-semibold text-heading">
                    {formatDuration(Math.round(review.duration_taken / review.answers.length))}
                  </span>
                </div>
              </div>
            </Card>
          </aside>

          {/* Right Column: Dynamic Side-by-Side Question Comparison Lists */}
          <section className="lg:col-span-8 space-y-6">
            {filteredAnswers.length === 0 ? (
              <Card className="p-12 text-center" elevation={1}>
                <BookOpen size={48} weight="duotone" className="text-text-disabled mx-auto mb-4" />
                <h3 className="text-lg font-bold text-heading mb-1">No Questions Match Filter</h3>
                <p className="text-body text-sm mb-4">Try clearing or selecting a different response status filter above.</p>
                <Button variant="outline" size="sm" onClick={() => setActiveFilter('all')}>
                  Reset Filter
                </Button>
              </Card>
            ) : (
              filteredAnswers.map((ans, idx) => {
                const globalIndex = review.answers.findIndex(a => a.question_id === ans.question_id) + 1;
                const isSelected = selectedQuestionId === ans.question_id;

                return (
                  <Card
                    id={`q-card-${ans.question_id}`}
                    key={ans.question_id}
                    elevation={1}
                    className={`p-6 border-l-4 transition-all duration-300 ${
                      ans.selected_option_id === null && ans.answer_text === null
                        ? 'border-l-amber-500'
                        : ans.is_correct
                        ? 'border-l-emerald-500'
                        : 'border-l-rose-500'
                    } ${isSelected ? 'ring-2 ring-custech-navy dark:ring-sky-500 ring-offset-1 scale-[1.01] shadow-elevation-2' : ''}`}
                  >
                    {/* Question Header */}
                    <div className="flex items-start justify-between gap-4 border-b border-border-default dark:border-gray-800/80 pb-4 mb-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-heading text-base">Question {globalIndex}</span>
                          <span className={`inline-flex px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                            ans.selected_option_id === null && ans.answer_text === null
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/20 dark:text-amber-400'
                              : ans.is_correct
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400'
                              : 'bg-rose-100 text-rose-800 dark:bg-rose-950/20 dark:text-rose-400'
                          }`}>
                            {ans.selected_option_id === null && ans.answer_text === null 
                              ? 'Unanswered' 
                              : ans.is_correct 
                              ? 'Correct' 
                              : 'Incorrect'}
                          </span>
                        </div>
                        <p className="text-xs text-text-muted mt-1">Time Spent: {formatDuration(ans.time_spent)}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-bold text-heading block">
                          {ans.points_earned} Points
                        </span>
                        <span className="text-xs text-text-muted">Earned</span>
                      </div>
                    </div>

                    {/* Side-by-Side Review Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Left Side: Question Stem and Options */}
                      <div className="space-y-4">
                        <div className="font-medium text-heading text-sm whitespace-pre-wrap">
                          {ans.question_text}
                        </div>

                        {ans.options && ans.options.length > 0 ? (
                          <div className="space-y-2">
                            {ans.options.map((opt) => {
                              const wasSelected = ans.selected_option_id === opt.id;
                              const isCorrect = opt.is_correct;
                              
                              let optStyles = 'border-border-default dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50';
                              let badge = null;

                              if (wasSelected && isCorrect) {
                                optStyles = 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/15 text-emerald-900 dark:text-emerald-300 font-medium';
                                badge = (
                                  <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                                    <CheckCircle size={14} weight="fill" /> Selected (Correct)
                                  </span>
                                );
                              } else if (wasSelected && !isCorrect) {
                                optStyles = 'border-rose-500 bg-rose-50/50 dark:bg-rose-950/15 text-rose-900 dark:text-rose-300 font-medium';
                                badge = (
                                  <span className="flex items-center gap-1 text-[11px] font-bold text-rose-600 dark:text-rose-400">
                                    <XCircle size={14} weight="fill" /> Selected (Incorrect)
                                  </span>
                                );
                              } else if (!wasSelected && isCorrect) {
                                optStyles = 'border-emerald-300 bg-emerald-50/20 dark:bg-emerald-950/5 dark:border-emerald-900/40 text-emerald-800 dark:text-emerald-400 font-medium';
                                badge = (
                                  <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
                                    Correct Answer
                                  </span>
                                );
                              }

                              return (
                                <div
                                  key={opt.id}
                                  className={`p-3 border rounded-md text-xs transition-all duration-150 flex items-start justify-between gap-3 ${optStyles}`}
                                >
                                  <div className="flex items-start gap-2">
                                    <span className="w-5 h-5 flex items-center justify-center rounded-full bg-black/5 dark:bg-white/5 font-semibold text-[10px] shrink-0 mt-0.5">
                                      {opt.id.slice(-1).toUpperCase()}
                                    </span>
                                    <span>{opt.option_text}</span>
                                  </div>
                                  {badge && <span className="shrink-0 mt-0.5">{badge}</span>}
                                </div>
                              );
                            })}
                          </div>
                        ) : ans.answer_text ? (
                          <div className="p-3 bg-gray-50 dark:bg-gray-900/60 rounded border border-border-default dark:border-gray-800">
                            <p className="text-xs text-text-muted uppercase font-bold tracking-wider mb-1">Student Answer:</p>
                            <p className="text-sm font-semibold text-heading">{ans.answer_text}</p>
                          </div>
                        ) : (
                          <div className="p-3 bg-amber-50/50 dark:bg-amber-950/5 rounded border border-amber-200/50 text-xs text-amber-800 dark:text-amber-400">
                            No answer was provided for this question.
                          </div>
                        )}
                      </div>

                      {/* Right Side: Correct Answer Verification & In-depth Explanation */}
                      <div className="flex flex-col justify-between space-y-4 md:border-l md:border-border-default md:dark:border-gray-800/80 md:pl-6">
                        <div className="space-y-3">
                          <h4 className="text-xs uppercase tracking-wider font-bold text-text-muted">Verification Status</h4>
                          
                          <div className={`p-4 border rounded-md text-xs space-y-2 ${getStatusColor(ans.is_correct, ans.selected_option_id)}`}>
                            <div className="flex justify-between items-center font-bold">
                              <span>Response Type:</span>
                              <span className="uppercase text-[10px]">
                                {ans.selected_option_id === null && ans.answer_text === null ? 'Skipped' : ans.is_correct ? 'Correct' : 'Incorrect'}
                              </span>
                            </div>
                            
                            <div className="flex justify-between">
                              <span>Selected:</span>
                              <span className="font-semibold">
                                {ans.selected_option_id 
                                  ? `Option ${ans.selected_option_id.slice(-1).toUpperCase()}` 
                                  : ans.answer_text 
                                  ? 'Text Response' 
                                  : 'None'}
                              </span>
                            </div>
                            
                            {ans.correct_option_id && (
                              <div className="flex justify-between border-t border-black/5 dark:border-white/5 pt-2 mt-2">
                                <span>Correct Option:</span>
                                <span className="font-bold text-emerald-700 dark:text-emerald-400">
                                  Option {ans.correct_option_id.slice(-1).toUpperCase()}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {ans.explanation ? (
                          <div className="p-4 bg-custech-navy/5 dark:bg-sky-950/5 rounded-md border border-custech-navy/10 dark:border-sky-900/10">
                            <div className="flex items-center gap-1.5 text-custech-navy dark:text-sky-400 font-bold text-xs uppercase tracking-wider mb-2">
                              <BookOpen size={16} />
                              <span>Lecturer's Explanation</span>
                            </div>
                            <p className="text-xs text-text-body leading-relaxed whitespace-pre-wrap italic">
                              "{ans.explanation}"
                            </p>
                          </div>
                        ) : (
                          <div className="p-4 bg-gray-50/50 dark:bg-gray-900/20 rounded-md border border-dashed border-border-default dark:border-gray-800 text-xs text-center text-text-muted italic">
                            No explanation provided for this question.
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })
            )}
          </section>
        </div>
      </main>
    </div>
  );
};

export default StudentResultsReview;
