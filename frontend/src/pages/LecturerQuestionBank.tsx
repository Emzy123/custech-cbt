import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Upload, 
  MagnifyingGlass,
  Funnel,
  Pencil,
  Trash,
  CheckCircle,
  XCircle,
  ArrowCounterClockwise,
  FolderOpen,
  Tag,
  ChartLine
} from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';

interface Question {
  id: string;
  stem: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  lastModified: string;
  options: {
    id: string;
    label: string;
    text: string;
    isCorrect: boolean;
  }[];
}

interface FilterState {
  topic: string;
  difficulty: string;
  status: string;
  search: string;
}

const LecturerQuestionBank: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [filteredQuestions, setFilteredQuestions] = useState<Question[]>([]);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBulkReview, setShowBulkReview] = useState(false);
  const [selectedQuestionForReview, setSelectedQuestionForReview] = useState<Question | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    topic: '',
    difficulty: '',
    status: '',
    search: ''
  });

  // Mock data - replace with actual API calls
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        // TODO: Replace with actual API call
        // const response = await fetch('/api/v1/questions/bank');
        // const data = await response.json();
        
        const mockQuestions: Question[] = [
          {
            id: '1',
            stem: 'Which of the following is NOT a component of effective communication?',
            topic: 'Communication Basics',
            difficulty: 'medium',
            status: 'approved',
            lastModified: '2026-05-06T10:30:00Z',
            options: [
              { id: 'a', label: 'A', text: 'Sender', isCorrect: false },
              { id: 'b', label: 'B', text: 'Message', isCorrect: false },
              { id: 'c', label: 'C', text: 'Noise', isCorrect: true },
              { id: 'd', label: 'D', text: 'Receiver', isCorrect: false }
            ]
          },
          {
            id: '2',
            stem: 'The process of converting ideas into words is called:',
            topic: 'Communication Process',
            difficulty: 'easy',
            status: 'submitted',
            lastModified: '2026-05-07T14:15:00Z',
            options: [
              { id: 'a', label: 'A', text: 'Encoding', isCorrect: true },
              { id: 'b', label: 'B', text: 'Decoding', isCorrect: false },
              { id: 'c', label: 'C', text: 'Transmission', isCorrect: false },
              { id: 'd', label: 'D', text: 'Feedback', isCorrect: false }
            ]
          },
          {
            id: '3',
            stem: 'Explain the concept of non-verbal communication and provide three examples.',
            topic: 'Non-verbal Communication',
            difficulty: 'hard',
            status: 'rejected',
            lastModified: '2026-05-05T09:45:00Z',
            options: []
          },
          {
            id: '4',
            stem: 'What is the primary purpose of feedback in the communication process?',
            topic: 'Communication Process',
            difficulty: 'medium',
            status: 'draft',
            lastModified: '2026-05-07T16:20:00Z',
            options: [
              { id: 'a', label: 'A', text: 'To confuse the sender', isCorrect: false },
              { id: 'b', label: 'B', text: 'To confirm understanding', isCorrect: true },
              { id: 'c', label: 'C', text: 'To end the conversation', isCorrect: false },
              { id: 'd', label: 'D', text: 'To introduce new topics', isCorrect: false }
            ]
          }
        ];
        
        setQuestions(mockQuestions);
        setFilteredQuestions(mockQuestions);
      } catch (error) {
        console.error('Failed to load questions:', error);
      } finally {
        setLoading(false);
      }
    };

    loadQuestions();
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = questions;

    if (filters.search) {
      filtered = filtered.filter(q => 
        q.stem.toLowerCase().includes(filters.search.toLowerCase()) ||
        q.topic.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    if (filters.topic) {
      filtered = filtered.filter(q => q.topic === filters.topic);
    }

    if (filters.difficulty) {
      filtered = filtered.filter(q => q.difficulty === filters.difficulty);
    }

    if (filters.status) {
      filtered = filtered.filter(q => q.status === filters.status);
    }

    setFilteredQuestions(filtered);
  }, [filters, questions]);

  const handleFilterChange = (key: keyof FilterState, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleQuestionSelect = (questionId: string) => {
    setSelectedQuestions(prev => 
      prev.includes(questionId)
        ? prev.filter(id => id !== questionId)
        : [...prev, questionId]
    );
  };

  const handleSelectAll = () => {
    if (selectedQuestions.length === filteredQuestions.length) {
      setSelectedQuestions([]);
    } else {
      setSelectedQuestions(filteredQuestions.map(q => q.id));
    }
  };

  const handleBulkAction = async (action: 'approve' | 'reject' | 'delete') => {
    if (selectedQuestions.length === 0) return;

    try {
      // TODO: Implement actual bulk action API calls
      console.log(`Bulk ${action} for questions:`, selectedQuestions);
      
      // Update local state optimistically
      if (action === 'delete') {
        setQuestions(prev => prev.filter(q => !selectedQuestions.includes(q.id)));
      } else {
        setQuestions(prev => prev.map(q => 
          selectedQuestions.includes(q.id) 
            ? { ...q, status: action === 'approve' ? 'approved' : 'rejected' }
            : q
        ));
      }
      
      setSelectedQuestions([]);
    } catch (error) {
      console.error(`Failed to bulk ${action} questions:`, error);
    }
  };

  const handleReviewQuestion = (question: Question) => {
    setSelectedQuestionForReview(question);
    setShowBulkReview(true);
  };

  const handleQuestionReviewAction = async (action: 'approve' | 'reject' | 'request_changes', feedback?: string) => {
    if (!selectedQuestionForReview) return;

    try {
      // TODO: Implement actual review API call
      console.log(`Review action: ${action}`, selectedQuestionForReview.id, feedback);
      
      // Update local state
      setQuestions(prev => prev.map(q => 
        q.id === selectedQuestionForReview.id 
          ? { ...q, status: action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'submitted' }
          : q
      ));
      
      setShowBulkReview(false);
      setSelectedQuestionForReview(null);
    } catch (error) {
      console.error('Failed to review question:', error);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'badge-success';
      case 'medium': return 'badge-warning';
      case 'hard': return 'badge-danger';
      default: return 'badge-info';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'badge-success';
      case 'submitted': return 'badge-info';
      case 'rejected': return 'badge-danger';
      case 'draft': return 'badge-warning';
      default: return 'badge-info';
    }
  };

  const getUniqueTopics = () => {
    return Array.from(new Set(questions.map(q => q.topic)));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-grey flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-blue-800 mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading question bank...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-grey">
      {/* Header */}
      <header className="bg-surface-white shadow-elevation-1 h-16 flex items-center px-6">
        <div className="flex items-center gap-4">
          <FolderOpen size={24} weight="bold" className="text-primary-blue-800" />
          <h1 className="text-xl font-semibold text-text-primary">
            Question Bank: GST 111
          </h1>
        </div>
        
        <div className="ml-auto flex items-center gap-3">
          <Button variant="secondary" size="sm">
            <Upload size={16} weight="bold" className="mr-2" />
            Import CSV
          </Button>
          <Button variant="primary" size="sm">
            <Plus size={16} weight="bold" className="mr-2" />
            Add Question
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="container-fluid py-6">
        {/* Filters */}
        <Card elevation={1} className="p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative">
              <MagnifyingGlass size={16} weight="regular" className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary" />
              <Input
                placeholder="Search questions..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="pl-10"
              />
            </div>
            
            <select
              value={filters.topic}
              onChange={(e) => handleFilterChange('topic', e.target.value)}
              className="form-input"
            >
              <option value="">All Topics</option>
              {getUniqueTopics().map(topic => (
                <option key={topic} value={topic}>{topic}</option>
              ))}
            </select>
            
            <select
              value={filters.difficulty}
              onChange={(e) => handleFilterChange('difficulty', e.target.value)}
              className="form-input"
            >
              <option value="">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="form-input"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </Card>

        {/* Bulk Actions */}
        {selectedQuestions.length > 0 && (
          <Card elevation={1} className="p-4 mb-6 bg-blue-50 border border-blue-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-800">
                {selectedQuestions.length} question{selectedQuestions.length > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <Button variant="tertiary" size="sm" onClick={() => setSelectedQuestions([])}>
                  Clear Selection
                </Button>
                <Button variant="secondary" size="sm" onClick={() => handleBulkAction('approve')}>
                  <CheckCircle size={16} weight="bold" className="mr-1" />
                  Approve
                </Button>
                <Button variant="secondary" size="sm" onClick={() => handleBulkAction('reject')}>
                  <XCircle size={16} weight="bold" className="mr-1" />
                  Reject
                </Button>
                <Button variant="tertiary" size="sm" onClick={() => handleBulkAction('delete')}>
                  <Trash size={16} weight="bold" className="mr-1" />
                  Delete
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Questions Table */}
        <Card elevation={1} className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-grey border-b border-surface-grey-dark">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedQuestions.length === filteredQuestions.length && filteredQuestions.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-surface-grey-dark"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Question
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Topic
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Difficulty
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Last Modified
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-surface-white divide-y divide-surface-grey-dark">
                {filteredQuestions.map((question) => (
                  <tr key={question.id} className="hover:bg-surface-grey transition-colors duration-150">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedQuestions.includes(question.id)}
                        onChange={() => handleQuestionSelect(question.id)}
                        className="rounded border-surface-grey-dark"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-text-primary max-w-xs truncate">
                        {question.stem}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="badge badge-info">
                        {question.topic}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`badge ${getDifficultyColor(question.difficulty)}`}>
                        {question.difficulty}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`badge ${getStatusColor(question.status)}`}>
                        {question.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-text-secondary">
                      {new Date(question.lastModified).toLocaleDateString('en-NG', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="tertiary"
                          size="sm"
                          onClick={() => handleReviewQuestion(question)}
                        >
                          <Pencil size={14} weight="bold" />
                        </Button>
                        {question.status === 'submitted' && (
                          <Button
                            variant="tertiary"
                            size="sm"
                            onClick={() => handleReviewQuestion(question)}
                          >
                            <ChartLine size={14} weight="bold" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredQuestions.length === 0 && (
            <div className="text-center py-12">
              <FolderOpen size={48} weight="duotone" className="text-text-disabled mx-auto mb-4" />
              <h3 className="text-lg font-medium text-text-primary mb-2">
                No questions found
              </h3>
              <p className="text-text-secondary mb-4">
                {questions.length === 0 
                  ? "Get started by adding your first question to the bank."
                  : "Try adjusting your filters to find what you're looking for."
                }
              </p>
              {questions.length === 0 && (
                <Button variant="primary" size="sm">
                  <Plus size={16} weight="bold" className="mr-2" />
                  Add Question
                </Button>
              )}
            </div>
          )}
        </Card>
      </main>

      {/* Review Modal */}
      {showBulkReview && selectedQuestionForReview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h3 className="text-xl font-semibold text-text-primary mb-4">
                Review Question
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-text-secondary">Question</label>
                  <p className="text-text-primary mt-1">{selectedQuestionForReview.stem}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-text-secondary">Topic</label>
                  <p className="text-text-primary mt-1">{selectedQuestionForReview.topic}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-text-secondary">Difficulty</label>
                  <span className={`badge ${getDifficultyColor(selectedQuestionForReview.difficulty)} ml-2`}>
                    {selectedQuestionForReview.difficulty}
                  </span>
                </div>
                
                {selectedQuestionForReview.options.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-text-secondary">Options</label>
                    <div className="mt-2 space-y-2">
                      {selectedQuestionForReview.options.map((option) => (
                        <div key={option.id} className="flex items-center gap-2">
                          <span className="font-medium">{option.label}.</span>
                          <span>{option.text}</span>
                          {option.isCorrect && (
                            <span className="badge badge-success">Correct</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div>
                  <label className="text-sm font-medium text-text-secondary">Current Status</label>
                  <span className={`badge ${getStatusColor(selectedQuestionForReview.status)} ml-2`}>
                    {selectedQuestionForReview.status}
                  </span>
                </div>
              </div>
              
              <div className="mt-6 flex gap-3 justify-end">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowBulkReview(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleQuestionReviewAction('request_changes')}
                >
                  <ArrowCounterClockwise size={16} weight="bold" className="mr-2" />
                  Request Changes
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleQuestionReviewAction('reject')}
                  className="border-danger text-danger hover:bg-red-50"
                >
                  <XCircle size={16} weight="bold" className="mr-2" />
                  Reject
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleQuestionReviewAction('approve')}
                >
                  <CheckCircle size={16} weight="bold" className="mr-2" />
                  Approve
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default LecturerQuestionBank;
