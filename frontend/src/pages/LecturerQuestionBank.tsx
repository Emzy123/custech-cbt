import React, { useState, useEffect, useCallback } from 'react';
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
  ChartLine,
  FileCsv,
  DownloadSimple,
  BookOpen,
  GraduationCap,
  Clock,
  Star,
  TrendUp,
  TrendDown,
  Calendar,
  User,
  Bell,
  SignOut,
  House,
  ChartBar,
  Files,
  ClipboardText,
  Lightbulb,
  Prohibit,
  Check,
  X,
  FileText,
  Export,
  Database
} from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import { apiRequest } from '../lib/api';

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

interface QuestionFormData {
  stem: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  options: {
    id: string;
    label: string;
    text: string;
    isCorrect: boolean;
  }[];
}

const INITIAL_FORM_DATA: QuestionFormData = {
  stem: '',
  topic: '',
  difficulty: 'medium',
  options: [
    { id: '1', label: 'A', text: '', isCorrect: false },
    { id: '2', label: 'B', text: '', isCorrect: false },
    { id: '3', label: 'C', text: '', isCorrect: false },
    { id: '4', label: 'D', text: '', isCorrect: false },
  ]
};

const LecturerQuestionBank: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [filteredQuestions, setFilteredQuestions] = useState<Question[]>([]);
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBulkReview, setShowBulkReview] = useState(false);
  const [selectedQuestionForReview, setSelectedQuestionForReview] = useState<Question | null>(null);
  
  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [formData, setFormData] = useState<QuestionFormData>(INITIAL_FORM_DATA);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<QuestionFormData[]>([]);
  
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
        const data = await apiRequest<Array<Record<string, unknown>>>('/api/v1/questions');
        const mapped: Question[] = data.map((item) => ({
          id: String(item.id || ''),
          stem: String(item.question_text || item.stem || ''),
          topic: String(item.topic || 'General'),
          difficulty: (String(item.difficulty || 'medium').toLowerCase() as 'easy' | 'medium' | 'hard'),
          status: (String(item.status || 'draft').toLowerCase() as 'draft' | 'submitted' | 'approved' | 'rejected'),
          lastModified: String(item.updated_at || item.created_at || new Date().toISOString()),
          options: Array.isArray(item.options)
            ? (item.options as Array<Record<string, unknown>>).map((opt, idx) => ({
                id: String(opt.id || idx),
                label: String.fromCharCode(65 + idx),
                text: String(opt.option_text || opt.text || ''),
                isCorrect: Boolean(opt.is_correct),
              }))
            : [],
        }));
        setQuestions(mapped);
        setFilteredQuestions(mapped);
      } catch (error) {
        setQuestions([]);
        setFilteredQuestions([]);
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
      await Promise.all(
        selectedQuestions.map(async (id) => {
          if (action === 'delete') {
            await apiRequest(`/api/v1/questions/${id}`, { method: 'DELETE' });
            return;
          }
          const decision = action === 'approve' ? 'approved' : 'rejected';
          await apiRequest(`/api/v1/questions/${id}/review`, {
            method: 'POST',
            body: JSON.stringify({ decision, comments: `Bulk ${action}` }),
          });
        })
      );
      
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
      // Keep UI unchanged on API failures.
    }
  };

  const handleReviewQuestion = (question: Question) => {
    setSelectedQuestionForReview(question);
    setShowBulkReview(true);
  };

  const handleQuestionReviewAction = async (action: 'approve' | 'reject' | 'request_changes', feedback?: string) => {
    if (!selectedQuestionForReview) return;

    try {
      const decision = action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'changes_requested';
      await apiRequest(`/api/v1/questions/${selectedQuestionForReview.id}/review`, {
        method: 'POST',
        body: JSON.stringify({ decision, comments: feedback || '' }),
      });
      
      // Update local state
      setQuestions(prev => prev.map(q => 
        q.id === selectedQuestionForReview.id 
          ? { ...q, status: action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'submitted' }
          : q
      ));
      
      setShowBulkReview(false);
      setSelectedQuestionForReview(null);
    } catch (error) {
      // Keep UI unchanged on API failures.
    }
  };

  // Add Question handlers
  const handleOpenAddModal = () => {
    setFormData(INITIAL_FORM_DATA);
    setShowAddModal(true);
  };

  const handleOpenEditModal = (question: Question) => {
    setEditingQuestion(question);
    setFormData({
      stem: question.stem,
      topic: question.topic,
      difficulty: question.difficulty,
      options: question.options.map((opt, idx) => ({
        ...opt,
        label: String.fromCharCode(65 + idx)
      }))
    });
    setShowEditModal(true);
  };

  const handleCloseModals = () => {
    setShowAddModal(false);
    setShowEditModal(false);
    setShowImportModal(false);
    setEditingQuestion(null);
    setFormData(INITIAL_FORM_DATA);
    setCsvFile(null);
    setImportPreview([]);
  };

  const handleFormChange = (field: keyof QuestionFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleOptionChange = (index: number, text: string) => {
    setFormData(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => 
        i === index ? { ...opt, text } : opt
      )
    }));
  };

  const handleCorrectOptionChange = (index: number) => {
    setFormData(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => ({
        ...opt,
        isCorrect: i === index
      }))
    }));
  };

  const validateForm = (): boolean => {
    if (!formData.stem.trim()) return false;
    if (!formData.topic.trim()) return false;
    if (formData.options.some(opt => !opt.text.trim())) return false;
    if (!formData.options.some(opt => opt.isCorrect)) return false;
    return true;
  };

  const handleSubmitQuestion = async () => {
    if (!validateForm()) {
      alert('Please fill in all required fields and select a correct answer');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        question_text: formData.stem,
        topic: formData.topic,
        difficulty: formData.difficulty,
        options: formData.options.map(opt => ({
          option_text: opt.text,
          is_correct: opt.isCorrect
        }))
      };

      const response = await apiRequest<{ id: string }>('/api/v1/questions', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      // Add to local state
      const newQuestion: Question = {
        id: response.id,
        stem: formData.stem,
        topic: formData.topic,
        difficulty: formData.difficulty,
        status: 'draft',
        lastModified: new Date().toISOString(),
        options: formData.options
      };

      setQuestions(prev => [newQuestion, ...prev]);
      handleCloseModals();
    } catch (error) {
      alert('Failed to create question. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateQuestion = async () => {
    if (!editingQuestion || !validateForm()) {
      alert('Please fill in all required fields and select a correct answer');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        question_text: formData.stem,
        topic: formData.topic,
        difficulty: formData.difficulty,
        options: formData.options.map(opt => ({
          option_text: opt.text,
          is_correct: opt.isCorrect
        }))
      };

      await apiRequest(`/api/v1/questions/${editingQuestion.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });

      // Update local state
      setQuestions(prev => prev.map(q => 
        q.id === editingQuestion.id 
          ? {
              ...q,
              stem: formData.stem,
              topic: formData.topic,
              difficulty: formData.difficulty,
              options: formData.options,
              lastModified: new Date().toISOString()
            }
          : q
      ));

      handleCloseModals();
    } catch (error) {
      alert('Failed to update question. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // CSV Import handlers
  const handleCsvTemplateDownload = () => {
    const template = 'question_text,topic,difficulty,option_a,option_b,option_c,option_d,correct_answer\n"What is the capital of France?","Geography","easy","London","Paris","Berlin","Madrid","B"\n"What is 2+2?","Mathematics","easy","3","4","5","6","B"';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'question_import_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Check MIME type or file extension
    const isCsv = file.type === 'text/csv' || 
                  file.type === 'application/vnd.ms-excel' ||
                  file.type === 'text/plain' ||
                  file.type === '' ||
                  file.name.toLowerCase().endsWith('.csv');
    
    if (isCsv) {
      setCsvFile(file);
      parseCsvFile(file);
    } else {
      alert('Please select a valid CSV file (.csv)');
    }
  };

  const parseCsvFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').filter(line => line.trim());
      
      if (lines.length < 2) {
        alert('CSV file is empty or invalid');
        return;
      }

      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
      const parsed: QuestionFormData[] = [];

      for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        // Simple CSV parsing - split by comma but handle quoted values
        const values: string[] = [];
        let current = '';
        let inQuotes = false;
        
        for (const char of line) {
          if (char === '"') {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
          } else {
            current += char;
          }
        }
        values.push(current.trim());

        const getValue = (name: string) => {
          const idx = headers.indexOf(name);
          return idx >= 0 ? values[idx]?.replace(/"/g, '') || '' : '';
        };

        const correctAnswer = getValue('correct_answer').toUpperCase();
        const correctIndex = correctAnswer.charCodeAt(0) - 65; // A=0, B=1, etc.

        parsed.push({
          stem: getValue('question_text'),
          topic: getValue('topic'),
          difficulty: (getValue('difficulty').toLowerCase() as 'easy' | 'medium' | 'hard') || 'medium',
          options: [
            { id: '1', label: 'A', text: getValue('option_a'), isCorrect: correctIndex === 0 },
            { id: '2', label: 'B', text: getValue('option_b'), isCorrect: correctIndex === 1 },
            { id: '3', label: 'C', text: getValue('option_c'), isCorrect: correctIndex === 2 },
            { id: '4', label: 'D', text: getValue('option_d'), isCorrect: correctIndex === 3 },
          ]
        });
      }

      setImportPreview(parsed);
    };
    reader.readAsText(file);
  };

  const handleImportQuestions = async () => {
    if (importPreview.length === 0) return;

    setIsSubmitting(true);
    let successCount = 0;
    let failCount = 0;

    for (const question of importPreview) {
      try {
        const payload = {
          question_text: question.stem,
          topic: question.topic,
          difficulty: question.difficulty,
          options: question.options.map(opt => ({
            option_text: opt.text,
            is_correct: opt.isCorrect
          }))
        };

        const response = await apiRequest<{ id: string }>('/api/v1/questions', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        const newQuestion: Question = {
          id: response.id,
          stem: question.stem,
          topic: question.topic,
          difficulty: question.difficulty,
          status: 'draft',
          lastModified: new Date().toISOString(),
          options: question.options
        };

        setQuestions(prev => [newQuestion, ...prev]);
        successCount++;
      } catch (error: any) {
        failCount++;
        // Check for permission error on first failure
        if (failCount === 1 && error?.status === 403) {
          const shouldClear = confirm(
            'Permission denied. Your cached permissions may be outdated.\n\n' +
            'Would you like to clear your permission cache?\n' +
            '(You will need to log in again after clearing)'
          );
          if (shouldClear) {
            try {
              await apiRequest('/api/v1/users/me/clear-cache', { method: 'POST' });
              alert('Cache cleared. Please log out and log back in to refresh permissions.');
            } catch {
              alert('Failed to clear cache. Please contact an administrator.');
            }
          }
          break; // Stop importing
        }
      }
    }

    if (failCount > 0 && failCount !== importPreview.length) {
      alert(`Import complete: ${successCount} questions imported, ${failCount} failed`);
    } else if (successCount > 0) {
      alert(`Import complete: ${successCount} questions imported successfully!`);
    }
    
    if (successCount > 0) {
      handleCloseModals();
    }
    setIsSubmitting(false);
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

  // Statistics calculations
  const stats = {
    total: questions.length,
    byStatus: {
      draft: questions.filter(q => q.status === 'draft').length,
      submitted: questions.filter(q => q.status === 'submitted').length,
      approved: questions.filter(q => q.status === 'approved').length,
      rejected: questions.filter(q => q.status === 'rejected').length,
    },
    byDifficulty: {
      easy: questions.filter(q => q.difficulty === 'easy').length,
      medium: questions.filter(q => q.difficulty === 'medium').length,
      hard: questions.filter(q => q.difficulty === 'hard').length,
    },
    topics: getUniqueTopics().length,
    approvalRate: questions.length > 0 
      ? Math.round((questions.filter(q => q.status === 'approved').length / questions.length) * 100) 
      : 0,
  };

  // Recent questions (last 5)
  const recentQuestions = [...questions]
    .sort((a, b) => new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime())
    .slice(0, 5);

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
    <div className="min-h-screen bg-slate-50 flex">
      {/* Professional Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col fixed h-full shadow-2xl">
        {/* Logo Area */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <GraduationCap size={24} weight="bold" className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">Custech</h1>
              <p className="text-xs text-slate-400">CBT System</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
          <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Main Menu
          </div>
          <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-600 text-white transition-all">
            <Database size={20} weight="fill" />
            <span className="font-medium">Question Bank</span>
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-all">
            <Files size={20} />
            <span className="font-medium">My Courses</span>
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-all">
            <ClipboardText size={20} />
            <span className="font-medium">Examinations</span>
            <span className="ml-auto bg-amber-500 text-slate-900 text-xs font-bold px-2 py-0.5 rounded-full">2</span>
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-all">
            <ChartBar size={20} />
            <span className="font-medium">Analytics</span>
          </a>

          <div className="px-3 mt-8 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Quick Actions
          </div>
          <button 
            onClick={handleOpenAddModal}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-emerald-400 hover:bg-slate-800 hover:text-emerald-300 transition-all"
          >
            <Plus size={20} weight="bold" />
            <span className="font-medium">Add Question</span>
          </button>
          <button 
            onClick={() => setShowImportModal(true)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-400 hover:bg-slate-800 hover:text-blue-300 transition-all"
          >
            <Upload size={20} weight="bold" />
            <span className="font-medium">Import CSV</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-purple-400 hover:bg-slate-800 hover:text-purple-300 transition-all">
            <Export size={20} weight="bold" />
            <span className="font-medium">Export Bank</span>
          </button>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center">
              <User size={20} weight="bold" className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">Dr. Lecturer</p>
              <p className="text-xs text-slate-400">Lecturer</p>
            </div>
            <button className="text-slate-400 hover:text-white transition-colors">
              <SignOut size={20} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 ml-64">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-30">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-800">Question Bank</h2>
              <p className="text-sm text-slate-500 mt-0.5">GST 111 - Use of English</p>
            </div>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors">
                <Bell size={20} weight="bold" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Clock size={16} />
                <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="p-8">
          {/* Statistics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Total Questions */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Total Questions</p>
                  <p className="text-3xl font-bold text-slate-800 mt-1">{stats.total}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Database size={24} className="text-blue-600" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm">
                <span className="text-emerald-600 font-medium flex items-center gap-1">
                  <TrendUp size={16} weight="bold" />
                  +{stats.byStatus.approved}
                </span>
                <span className="text-slate-400">approved</span>
              </div>
            </div>

            {/* Approval Rate */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Approval Rate</p>
                  <p className="text-3xl font-bold text-slate-800 mt-1">{stats.approvalRate}%</p>
                </div>
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <CheckCircle size={24} className="text-emerald-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div 
                    className="bg-emerald-500 h-2 rounded-full transition-all" 
                    style={{ width: `${stats.approvalRate}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Topics Covered */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Topics Covered</p>
                  <p className="text-3xl font-bold text-slate-800 mt-1">{stats.topics}</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                  <Tag size={24} className="text-amber-600" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm">
                <span className="text-slate-400">Across all courses</span>
              </div>
            </div>

            {/* Pending Review */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Pending Review</p>
                  <p className="text-3xl font-bold text-slate-800 mt-1">{stats.byStatus.submitted}</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                  <Clock size={24} className="text-purple-600" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm">
                <span className="text-purple-600 font-medium">
                  {stats.byStatus.draft} drafts
                </span>
                <span className="text-slate-400">in progress</span>
              </div>
            </div>
          </div>

          {/* Difficulty Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
              <h3 className="font-semibold text-slate-800 mb-4">Difficulty Distribution</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Easy</span>
                    <span className="font-medium text-slate-800">{stats.byDifficulty.easy}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${stats.total ? (stats.byDifficulty.easy / stats.total) * 100 : 0}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Medium</span>
                    <span className="font-medium text-slate-800">{stats.byDifficulty.medium}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${stats.total ? (stats.byDifficulty.medium / stats.total) * 100 : 0}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">Hard</span>
                    <span className="font-medium text-slate-800">{stats.byDifficulty.hard}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-red-500 h-2 rounded-full" style={{ width: `${stats.total ? (stats.byDifficulty.hard / stats.total) * 100 : 0}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800">Recent Activity</h3>
                <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">View All</button>
              </div>
              <div className="space-y-3">
                {recentQuestions.length === 0 ? (
                  <p className="text-slate-400 text-sm py-4">No recent activity</p>
                ) : (
                  recentQuestions.map((q, idx) => (
                    <div key={q.id} className="flex items-center gap-4 p-3 hover:bg-slate-50 rounded-xl transition-colors">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        q.status === 'approved' ? 'bg-emerald-100' :
                        q.status === 'submitted' ? 'bg-blue-100' :
                        q.status === 'rejected' ? 'bg-red-100' : 'bg-amber-100'
                      }`}>
                        {q.status === 'approved' ? <Check size={20} className="text-emerald-600" /> :
                         q.status === 'submitted' ? <Clock size={20} className="text-blue-600" /> :
                         q.status === 'rejected' ? <X size={20} className="text-red-600" /> :
                         <Pencil size={20} className="text-amber-600" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{q.stem}</p>
                        <p className="text-xs text-slate-500">{q.topic} • {new Date(q.lastModified).toLocaleDateString()}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        q.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                        q.status === 'submitted' ? 'bg-blue-100 text-blue-700' :
                        q.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {q.status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Filters & Actions Bar */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 mb-6">
            <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
              <div className="flex flex-col sm:flex-row gap-3 flex-1 w-full lg:w-auto">
                <div className="relative flex-1 max-w-md">
                  <MagnifyingGlass size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search questions..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm"
                  />
                </div>
                <select
                  value={filters.topic}
                  onChange={(e) => handleFilterChange('topic', e.target.value)}
                  className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">All Topics</option>
                  {getUniqueTopics().map(topic => (
                    <option key={topic} value={topic}>{topic}</option>
                  ))}
                </select>
                <select
                  value={filters.difficulty}
                  onChange={(e) => handleFilterChange('difficulty', e.target.value)}
                  className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">All Difficulties</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="submitted">Submitted</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              
              <div className="flex items-center gap-2 w-full lg:w-auto">
                <button 
                  onClick={() => setShowImportModal(true)}
                  className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors text-sm font-medium"
                >
                  <Upload size={18} weight="bold" />
                  Import
                </button>
                <button 
                  onClick={handleOpenAddModal}
                  className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors text-sm font-medium shadow-lg shadow-blue-200"
                >
                  <Plus size={18} weight="bold" />
                  Add Question
                </button>
              </div>
            </div>
          </div>

          {/* Bulk Actions */}
          {selectedQuestions.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-blue-900">
                  {selectedQuestions.length} question{selectedQuestions.length > 1 ? 's' : ''} selected
                </span>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => setSelectedQuestions([])}
                    className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800 transition-colors"
                  >
                    Clear
                  </button>
                  <button 
                    onClick={() => handleBulkAction('approve')}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    <Check size={16} weight="bold" />
                    Approve
                  </button>
                  <button 
                    onClick={() => handleBulkAction('reject')}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    <X size={16} weight="bold" />
                    Reject
                  </button>
                  <button 
                    onClick={() => handleBulkAction('delete')}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    <Trash size={16} weight="bold" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}

        {/* Questions Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4 text-left w-12">
                    <input
                      type="checkbox"
                      checked={selectedQuestions.length === filteredQuestions.length && filteredQuestions.length > 0}
                      onChange={handleSelectAll}
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Question
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Topic
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Difficulty
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Last Modified
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredQuestions.map((question) => (
                  <tr key={question.id} className="hover:bg-slate-50 transition-colors duration-150">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedQuestions.includes(question.id)}
                        onChange={() => handleQuestionSelect(question.id)}
                        className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-800 max-w-md truncate" title={question.stem}>
                        {question.stem}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                        {question.topic}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        question.difficulty === 'easy' ? 'bg-emerald-50 text-emerald-700' :
                        question.difficulty === 'medium' ? 'bg-amber-50 text-amber-700' :
                        'bg-red-50 text-red-700'
                      }`}>
                        {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                        question.status === 'approved' ? 'bg-emerald-50 text-emerald-700' :
                        question.status === 'submitted' ? 'bg-blue-50 text-blue-700' :
                        question.status === 'rejected' ? 'bg-red-50 text-red-700' : 
                        'bg-slate-100 text-slate-700'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          question.status === 'approved' ? 'bg-emerald-500' :
                          question.status === 'submitted' ? 'bg-blue-500' :
                          question.status === 'rejected' ? 'bg-red-500' : 'bg-slate-500'
                        }`}></span>
                        {question.status.charAt(0).toUpperCase() + question.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {new Date(question.lastModified).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleOpenEditModal(question)}
                          className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Edit question"
                        >
                          <Pencil size={18} weight="bold" />
                        </button>
                        <button
                          onClick={() => handleReviewQuestion(question)}
                          className="p-2 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                          title="Review question"
                        >
                          <ChartLine size={18} weight="bold" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredQuestions.length === 0 && (
            <div className="text-center py-16">
              <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Database size={40} className="text-slate-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2">
                {questions.length === 0 ? 'No questions yet' : 'No matching questions'}
              </h3>
              <p className="text-slate-500 mb-6 max-w-md mx-auto">
                {questions.length === 0 
                  ? "Your question bank is empty. Get started by adding your first question or importing from CSV."
                  : "Try adjusting your filters or search terms to find what you're looking for."
                }
              </p>
              {questions.length === 0 && (
                <div className="flex items-center justify-center gap-3">
                  <button 
                    onClick={handleOpenAddModal}
                    className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-lg shadow-blue-200"
                  >
                    <Plus size={18} weight="bold" />
                    Add Question
                  </button>
                  <button 
                    onClick={() => setShowImportModal(true)}
                    className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl font-medium transition-colors"
                  >
                    <Upload size={18} weight="bold" />
                    Import CSV
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
        </div>
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

      {/* Add Question Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-text-primary">Add New Question</h3>
                <Button variant="tertiary" size="sm" onClick={handleCloseModals}>×</Button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Question Text *</label>
                  <textarea
                    className="w-full bg-surface-white border border-surface-grey-dark rounded-lg px-4 py-3 min-h-[100px] focus:ring-2 focus:ring-primary-blue-800 focus:border-transparent outline-none resize-none"
                    placeholder="Enter your question here..."
                    value={formData.stem}
                    onChange={(e) => handleFormChange('stem', e.target.value)}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Topic *</label>
                    <Input
                      placeholder="e.g., Algebra, Grammar"
                      value={formData.topic}
                      onChange={(e) => handleFormChange('topic', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Difficulty *</label>
                    <select
                      className="w-full bg-surface-white border border-surface-grey-dark rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-primary-blue-800"
                      value={formData.difficulty}
                      onChange={(e) => handleFormChange('difficulty', e.target.value as 'easy' | 'medium' | 'hard')}
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Answer Options *</label>
                  <p className="text-xs text-text-secondary mb-3">Select the radio button next to the correct answer</p>
                  <div className="space-y-3">
                    {formData.options.map((option, index) => (
                      <div key={option.id} className="flex items-center gap-3">
                        <input
                          type="radio"
                          name="correctOption"
                          checked={option.isCorrect}
                          onChange={() => handleCorrectOptionChange(index)}
                          className="w-4 h-4 text-primary-blue-800 focus:ring-primary-blue-800"
                        />
                        <span className="w-8 font-medium text-text-secondary">{option.label}.</span>
                        <Input
                          placeholder={`Option ${option.label}`}
                          value={option.text}
                          onChange={(e) => handleOptionChange(index, e.target.value)}
                          className="flex-1"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <Button variant="secondary" size="sm" onClick={handleCloseModals} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  size="sm" 
                  onClick={handleSubmitQuestion}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  ) : (
                    <Plus size={16} weight="bold" className="mr-2" />
                  )}
                  {isSubmitting ? 'Creating...' : 'Create Question'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Edit Question Modal */}
      {showEditModal && editingQuestion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-text-primary">Edit Question</h3>
                <Button variant="tertiary" size="sm" onClick={handleCloseModals}>×</Button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Question Text *</label>
                  <textarea
                    className="w-full bg-surface-white border border-surface-grey-dark rounded-lg px-4 py-3 min-h-[100px] focus:ring-2 focus:ring-primary-blue-800 focus:border-transparent outline-none resize-none"
                    placeholder="Enter your question here..."
                    value={formData.stem}
                    onChange={(e) => handleFormChange('stem', e.target.value)}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Topic *</label>
                    <Input
                      placeholder="e.g., Algebra, Grammar"
                      value={formData.topic}
                      onChange={(e) => handleFormChange('topic', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">Difficulty *</label>
                    <select
                      className="w-full bg-surface-white border border-surface-grey-dark rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-primary-blue-800"
                      value={formData.difficulty}
                      onChange={(e) => handleFormChange('difficulty', e.target.value as 'easy' | 'medium' | 'hard')}
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Answer Options *</label>
                  <p className="text-xs text-text-secondary mb-3">Select the radio button next to the correct answer</p>
                  <div className="space-y-3">
                    {formData.options.map((option, index) => (
                      <div key={option.id} className="flex items-center gap-3">
                        <input
                          type="radio"
                          name="correctOptionEdit"
                          checked={option.isCorrect}
                          onChange={() => handleCorrectOptionChange(index)}
                          className="w-4 h-4 text-primary-blue-800 focus:ring-primary-blue-800"
                        />
                        <span className="w-8 font-medium text-text-secondary">{option.label}.</span>
                        <Input
                          placeholder={`Option ${option.label}`}
                          value={option.text}
                          onChange={(e) => handleOptionChange(index, e.target.value)}
                          className="flex-1"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <Button variant="secondary" size="sm" onClick={handleCloseModals} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  size="sm" 
                  onClick={handleUpdateQuestion}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  ) : (
                    <Pencil size={16} weight="bold" className="mr-2" />
                  )}
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-text-primary">Import Questions from CSV</h3>
                <Button variant="tertiary" size="sm" onClick={handleCloseModals}>×</Button>
              </div>
              
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <FileCsv size={24} className="text-blue-600 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-blue-900">CSV Format Requirements</h4>
                      <p className="text-sm text-blue-700 mt-1">
                        Your CSV file must include these columns: question_text, topic, difficulty, option_a, option_b, option_c, option_d, correct_answer
                      </p>
                      <button
                        onClick={handleCsvTemplateDownload}
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium mt-2 flex items-center gap-1"
                      >
                        <DownloadSimple size={14} />
                        Download template CSV
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Upload CSV File</label>
                  <div className="border-2 border-dashed border-surface-grey-dark rounded-lg p-8 text-center hover:border-primary-blue-800 transition-colors">
                    <Upload size={32} className="text-text-secondary mx-auto mb-3" />
                    <p className="text-text-secondary mb-2">
                      {csvFile ? csvFile.name : 'Drag and drop your CSV file here, or click to browse'}
                    </p>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                      className="hidden"
                      id="csv-upload"
                    />
                    <label 
                      htmlFor="csv-upload"
                      className="inline-flex items-center justify-center px-4 py-2 bg-surface-grey-dark hover:bg-surface-grey text-text-primary text-sm font-medium rounded-lg cursor-pointer transition-colors border border-surface-grey"
                    >
                      Select CSV File
                    </label>
                  </div>
                </div>

                {importPreview.length > 0 && (
                  <div>
                    <h4 className="font-medium text-text-primary mb-2">Preview ({importPreview.length} questions)</h4>
                    <div className="max-h-64 overflow-y-auto border border-surface-grey-dark rounded-lg">
                      {importPreview.map((q, idx) => (
                        <div key={idx} className="p-3 border-b border-surface-grey-dark last:border-b-0">
                          <p className="text-sm font-medium text-text-primary truncate">{q.stem}</p>
                          <div className="flex items-center gap-2 mt-1 text-xs text-text-secondary">
                            <span className="badge badge-info">{q.topic}</span>
                            <span className={`badge ${getDifficultyColor(q.difficulty)}`}>{q.difficulty}</span>
                            <span>{q.options.filter(o => o.isCorrect).length === 1 ? '✓ Correct answer set' : '✗ No correct answer'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex justify-end gap-3">
                <Button variant="secondary" size="sm" onClick={handleCloseModals} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  size="sm" 
                  onClick={handleImportQuestions}
                  disabled={isSubmitting || importPreview.length === 0}
                >
                  {isSubmitting ? (
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  ) : (
                    <Upload size={16} weight="bold" className="mr-2" />
                  )}
                  {isSubmitting ? 'Importing...' : `Import ${importPreview.length} Questions`}
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
