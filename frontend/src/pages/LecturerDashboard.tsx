import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  GraduationCap,
  Plus,
  Upload,
  Pencil,
  Trash,
  CheckCircle,
  XCircle,
  ArrowCounterClockwise,
  Database,
  SignOut,
  User,
  Clock,
  Files,
  ClipboardText,
  X,
  Check,
  DownloadSimple,
  FileCsv,
  ChartBar,
  Users,
} from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import { apiRequest, logout } from '../lib/api';

interface AssignedCourse {
  id: string;
  code: string;
  title: string;
  credit_units: number;
  level: number;
  semester_type: string;
}

interface Question {
  id: string;
  question_text: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  status: 'draft' | 'submitted' | 'approved' | 'rejected';
  course_id: string;
  updated_at: string;
  options: { id: string; option_text: string; is_correct: boolean }[];
}

interface QuestionFormData {
  question_text: string;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  course_id: string;
  options: { text: string; isCorrect: boolean }[];
}

interface ExaminationApi {
  id: string;
  title: string;
  course_id: string;
  exam_date: string;
  start_time: string;
  duration_minutes: number;
  status: string;
  total_questions?: number;
}

interface StudentRow {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  matric_number: string;
  department_id: string;
  department_code?: string;
  department_name?: string;
  is_active: boolean;
}

type ActiveTab = 'overview' | 'questions' | 'exams';

const BLANK_FORM = (courseId: string): QuestionFormData => ({
  question_text: '',
  topic: '',
  difficulty: 'medium',
  course_id: courseId,
  options: [
    { text: '', isCorrect: false },
    { text: '', isCorrect: false },
    { text: '', isCorrect: false },
    { text: '', isCorrect: false },
  ],
});

const LecturerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [lecturerName, setLecturerName] = useState('Lecturer');
  const [lecturerId, setLecturerId] = useState('');

  const [assignedCourses, setAssignedCourses] = useState<AssignedCourse[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<AssignedCourse | null>(null);
  const [coursesLoading, setCoursesLoading] = useState(true);

  const [questions, setQuestions] = useState<Question[]>([]);
  const [questionsLoading, setQuestionsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDifficulty, setFilterDifficulty] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const [exams, setExams] = useState<ExaminationApi[]>([]);
  const [examsLoading, setExamsLoading] = useState(false);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [reviewingQuestion, setReviewingQuestion] = useState<Question | null>(null);
  const [formData, setFormData] = useState<QuestionFormData>(BLANK_FORM(''));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<QuestionFormData[]>([]);

  // Registered students modal states
  const [showStudentsModal, setShowStudentsModal] = useState(false);
  const [studentsModalExam, setStudentsModalExam] = useState<ExaminationApi | null>(null);
  const [examStudents, setExamStudents] = useState<StudentRow[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentsError, setStudentsError] = useState<string | null>(null);

  // Exam Results modal states
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [resultsModalExam, setResultsModalExam] = useState<ExaminationApi | null>(null);
  const [examResults, setExamResults] = useState<any[]>([]);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [resultsError, setResultsError] = useState<string | null>(null);

  // Load user info and assigned courses
  useEffect(() => {
    const raw = localStorage.getItem('authUser');
    if (raw) {
      try {
        const u = JSON.parse(raw) as { first_name?: string; last_name?: string; username?: string; id?: string };
        const fullName = `${u.first_name || ''} ${u.last_name || ''}`.trim();
        setLecturerName(fullName || u.username || 'Lecturer');
        setLecturerId(u.id || '');
      } catch { /* ignore */ }
    }
  }, []);

  useEffect(() => {
    if (!lecturerId) return;
    const loadCourses = async () => {
      setCoursesLoading(true);
      try {
        const data = await apiRequest<AssignedCourse[]>(`/api/v1/academics/lecturers/${lecturerId}/courses`);
        setAssignedCourses(data);
        if (data.length > 0) setSelectedCourse(data[0]);
      } catch {
        setAssignedCourses([]);
      } finally {
        setCoursesLoading(false);
      }
    };
    loadCourses();
  }, [lecturerId]);

  const loadQuestions = useCallback(async (courseId: string) => {
    setQuestionsLoading(true);
    try {
      const data = await apiRequest<Question[]>(`/api/v1/questions?course_id=${courseId}&limit=200`);
      setQuestions(Array.isArray(data) ? data : []);
    } catch {
      setQuestions([]);
    } finally {
      setQuestionsLoading(false);
    }
  }, []);

  const loadExams = useCallback(async (courseId: string) => {
    setExamsLoading(true);
    try {
      const data = await apiRequest<ExaminationApi[]>(`/api/v1/examinations/?course_id=${courseId}&limit=50`);
      setExams(Array.isArray(data) ? data : []);
    } catch {
      setExams([]);
    } finally {
      setExamsLoading(false);
    }
  }, []);

  const handleViewStudents = async (exam: ExaminationApi) => {
    setStudentsModalExam(exam);
    setShowStudentsModal(true);
    setStudentsLoading(true);
    setStudentsError(null);
    try {
      const data = await apiRequest<StudentRow[]>(`/api/v1/examinations/${exam.id}/registered-students`);
      setExamStudents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load registered students', err);
      setStudentsError('Failed to load registered students. Please check your network connection.');
      setExamStudents([]);
    } finally {
      setStudentsLoading(false);
    }
  };

  const handleViewResults = async (exam: ExaminationApi) => {
    setResultsModalExam(exam);
    setShowResultsModal(true);
    setResultsLoading(true);
    setResultsError(null);
    try {
      const data = await apiRequest<{ results: any[] }>(`/api/v1/examinations/${exam.id}/results?format=detail`);
      setExamResults(Array.isArray(data.results) ? data.results : []);
    } catch (err) {
      console.error('Failed to load exam results', err);
      setResultsError('Failed to load exam results. Please check your network connection.');
      setExamResults([]);
    } finally {
      setResultsLoading(false);
    }
  };

  const handleExportCSV = async (examId: string) => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`/api/v1/examinations/${examId}/results/export`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error(`Failed to export: ${response.statusText}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `results_${examId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to export results');
    }
  };

  useEffect(() => {
    if (!selectedCourse) return;
    loadQuestions(selectedCourse.id);
    loadExams(selectedCourse.id);
  }, [selectedCourse, loadQuestions, loadExams]);

  const handleLogout = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  // Filtered questions
  const filteredQuestions = questions.filter(q => {
    const matchSearch = !searchQuery || q.question_text.toLowerCase().includes(searchQuery.toLowerCase()) || q.topic.toLowerCase().includes(searchQuery.toLowerCase());
    const matchDiff = !filterDifficulty || q.difficulty === filterDifficulty;
    const matchStatus = !filterStatus || q.status === filterStatus;
    return matchSearch && matchDiff && matchStatus;
  });

  // Stats
  const stats = {
    total: questions.length,
    approved: questions.filter(q => q.status === 'approved').length,
    draft: questions.filter(q => q.status === 'draft').length,
    submitted: questions.filter(q => q.status === 'submitted').length,
  };

  // Form handlers
  const handleOpenAdd = () => {
    setFormData(BLANK_FORM(selectedCourse?.id || ''));
    setShowAddModal(true);
  };

  const handleOpenEdit = (q: Question) => {
    setEditingQuestion(q);
    setFormData({
      question_text: q.question_text,
      topic: q.topic,
      difficulty: q.difficulty,
      course_id: q.course_id,
      options: q.options.map(o => ({ text: o.option_text, isCorrect: o.is_correct })),
    });
    setShowEditModal(true);
  };

  const handleCloseModals = () => {
    setShowAddModal(false);
    setShowEditModal(false);
    setShowImportModal(false);
    setShowReviewModal(false);
    setEditingQuestion(null);
    setReviewingQuestion(null);
    setCsvFile(null);
    setImportPreview([]);
  };

  const validateForm = (fd: QuestionFormData) => {
    if (!fd.question_text.trim() || !fd.topic.trim()) return false;
    if (fd.options.some(o => !o.text.trim())) return false;
    if (!fd.options.some(o => o.isCorrect)) return false;
    return true;
  };

  const handleCreateQuestion = async () => {
    if (!validateForm(formData)) {
      alert('Fill in all fields and select a correct answer.');
      return;
    }
    setIsSubmitting(true);
    try {
      const resp = await apiRequest<Question>('/api/v1/questions', {
        method: 'POST',
        body: JSON.stringify({
          question_text: formData.question_text,
          topic: formData.topic,
          difficulty: formData.difficulty,
          course_id: formData.course_id,
          options: formData.options.map(o => ({ option_text: o.text, is_correct: o.isCorrect })),
        }),
      });
      setQuestions(prev => [resp, ...prev]);
      handleCloseModals();
    } catch (err: any) {
      alert(err.message || 'Failed to create question.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateQuestion = async () => {
    if (!editingQuestion || !validateForm(formData)) {
      alert('Fill in all fields and select a correct answer.');
      return;
    }
    setIsSubmitting(true);
    try {
      const resp = await apiRequest<Question>(`/api/v1/questions/${editingQuestion.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          question_text: formData.question_text,
          topic: formData.topic,
          difficulty: formData.difficulty,
          options: formData.options.map(o => ({ option_text: o.text, is_correct: o.isCorrect })),
        }),
      });
      setQuestions(prev => prev.map(q => q.id === editingQuestion.id ? resp : q));
      handleCloseModals();
    } catch (err: any) {
      alert(err.message || 'Failed to update question.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteQuestion = async (id: string) => {
    if (!confirm('Delete this question?')) return;
    try {
      await apiRequest(`/api/v1/questions/${id}`, { method: 'DELETE' });
      setQuestions(prev => prev.filter(q => q.id !== id));
    } catch (err: any) {
      alert(err.message || 'Failed to delete question.');
    }
  };

  const handleSubmitForReview = async (id: string) => {
    try {
      await apiRequest(`/api/v1/questions/${id}/submit-for-review`, { method: 'POST' });
      setQuestions(prev => prev.map(q => q.id === id ? { ...q, status: 'submitted' } : q));
    } catch (err: any) {
      alert(err.message || 'Failed to submit for review.');
    }
  };

  // CSV import
  const handleCsvDownload = () => {
    const tpl = 'question_text,topic,difficulty,option_a,option_b,option_c,option_d,correct_answer\n"Sample question?","Topic","easy","Option A","Option B","Option C","Option D","A"';
    const blob = new Blob([tpl], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'questions_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const isCsv = file.name.toLowerCase().endsWith('.csv');
    if (!isCsv) { alert('Please select a CSV file.'); return; }
    setCsvFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const lines = text.split('\n').filter(l => l.trim());
      if (lines.length < 2) { alert('CSV is empty or invalid.'); return; }
      const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
      const parsed: QuestionFormData[] = [];
      for (let i = 1; i < lines.length; i++) {
        const vals: string[] = [];
        let cur = ''; let inQ = false;
        for (const ch of lines[i]) {
          if (ch === '"') inQ = !inQ;
          else if (ch === ',' && !inQ) { vals.push(cur.trim()); cur = ''; }
          else cur += ch;
        }
        vals.push(cur.trim());
        const get = (name: string) => {
          const idx = headers.indexOf(name);
          return idx >= 0 ? (vals[idx] || '').replace(/"/g, '') : '';
        };
        const correct = get('correct_answer').toUpperCase().charCodeAt(0) - 65;
        parsed.push({
          question_text: get('question_text'),
          topic: get('topic'),
          difficulty: (get('difficulty').toLowerCase() || 'medium') as 'easy' | 'medium' | 'hard',
          course_id: selectedCourse?.id || '',
          options: ['option_a', 'option_b', 'option_c', 'option_d'].map((k, idx) => ({
            text: get(k),
            isCorrect: idx === correct,
          })),
        });
      }
      setImportPreview(parsed);
    };
    reader.readAsText(file);
  };

  const handleImportQuestions = async () => {
    if (!importPreview.length) return;
    setIsSubmitting(true);
    let ok = 0; let fail = 0;
    for (const q of importPreview) {
      try {
        const resp = await apiRequest<Question>('/api/v1/questions', {
          method: 'POST',
          body: JSON.stringify({
            question_text: q.question_text,
            topic: q.topic,
            difficulty: q.difficulty,
            course_id: q.course_id,
            options: q.options.map(o => ({ option_text: o.text, is_correct: o.isCorrect })),
          }),
        });
        setQuestions(prev => [resp, ...prev]);
        ok++;
      } catch { fail++; }
    }
    alert(`Imported ${ok} questions${fail > 0 ? `, ${fail} failed` : ''}.`);
    if (ok > 0) handleCloseModals();
    setIsSubmitting(false);
  };

  const diffColor = (d: string) => d === 'easy' ? 'bg-custech-green bg-opacity-20 text-custech-green' : d === 'medium' ? 'bg-custech-gold bg-opacity-20 text-custech-primary' : 'bg-danger bg-opacity-20 text-danger';
  const statusColor = (s: string) => s === 'approved' ? 'bg-custech-green bg-opacity-20 text-custech-green' : s === 'submitted' ? 'bg-custech-navy bg-opacity-20 text-custech-navy' : s === 'rejected' ? 'bg-danger bg-opacity-20 text-danger' : 'bg-light text-muted';

  return (
    <div className="min-h-screen bg-light flex">
      {/* Sidebar */}
      <aside className="w-64 bg-dark text-white flex flex-col fixed h-full shadow-2xl z-20">
        <div className="p-6 border-b border-darker">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-custech-gradient rounded-xl flex items-center justify-center">
              <GraduationCap size={24} weight="bold" className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">Custech</h1>
              <p className="text-xs text-muted">Lecturer Portal</p>
            </div>
          </div>
        </div>

        {/* Course selector */}
        <div className="px-4 py-3 border-b border-darker">
          <label className="text-xs text-muted uppercase tracking-wider block mb-1">Active Course</label>
          {coursesLoading ? (
            <p className="text-xs text-muted">Loading courses...</p>
          ) : assignedCourses.length === 0 ? (
            <p className="text-xs text-muted">No courses assigned.</p>
          ) : (
            <select
              value={selectedCourse?.id || ''}
              onChange={e => {
                const c = assignedCourses.find(x => x.id === e.target.value);
                if (c) setSelectedCourse(c);
              }}
              className="w-full bg-darker text-white text-sm px-2 py-1.5 rounded border border-muted focus:outline-none"
            >
              {assignedCourses.map(c => (
                <option key={c.id} value={c.id}>{c.code} — {c.title}</option>
              ))}
            </select>
          )}
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${activeTab === 'overview' ? 'bg-custech-primary text-white' : 'text-gray-300 hover:bg-darker hover:text-white'}`}
          >
            <ChartBar size={20} />
            <span className="font-medium text-sm">Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${activeTab === 'questions' ? 'bg-custech-primary text-white' : 'text-gray-300 hover:bg-darker hover:text-white'}`}
          >
            <Database size={20} />
            <span className="font-medium text-sm">Question Bank</span>
          </button>
          <button
            onClick={() => setActiveTab('exams')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${activeTab === 'exams' ? 'bg-custech-primary text-white' : 'text-gray-300 hover:bg-darker hover:text-white'}`}
          >
            <ClipboardText size={20} />
            <span className="font-medium text-sm">Examinations</span>
          </button>
        </nav>

        <div className="p-4 border-t border-darker">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 bg-custech-gold-gradient rounded-full flex items-center justify-center flex-shrink-0">
              <User size={18} weight="bold" className="text-white" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white truncate">{lecturerName}</p>
              <p className="text-xs text-muted">Lecturer</p>
            </div>
          </div>
          <button
            onClick={async () => { await logout(); navigate('/', { replace: true }); }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-custech-gold hover:bg-darker hover:text-white transition-all text-sm font-medium"
          >
            <SignOut size={16} weight="bold" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-64">
        <header className="bg-white shadow-sm border-b border-default sticky top-0 z-10">
          <div className="px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-heading">
                  {activeTab === 'overview' ? 'Overview' : activeTab === 'questions' ? 'Question Bank' : 'Examinations'}
                </h2>
                <p className="text-sm text-body mt-0.5">{selectedCourse?.code} — {selectedCourse?.title}</p>
              </div>
              {activeTab === 'questions' && (
                <div className="flex items-center gap-3">
                  <Button
                    variant="light"
                    size="sm"
                    onClick={() => navigate('/lecturer/questions')}
                  >
                    Open Full Question Bank
                  </Button>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="p-8">
          {/* No course assigned */}
          {!selectedCourse && !coursesLoading && (
            <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-default">
              <BookOpen size={48} className="text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-heading mb-2">No Courses Assigned</h3>
              <p className="text-body text-sm">You have not been assigned to any courses yet. Please contact your administrator.</p>
            </div>
          )}

          {/* Overview Tab */}
          {activeTab === 'overview' && selectedCourse && (
            <div className="space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: 'Total Questions', value: stats.total, color: 'bg-custech-navy' },
                  { label: 'Approved', value: stats.approved, color: 'bg-custech-green' },
                  { label: 'Pending Review', value: stats.submitted, color: 'bg-custech-primary' },
                  { label: 'Drafts', value: stats.draft, color: 'bg-custech-gold' },
                ].map(s => (
                  <div key={s.label} className="bg-white rounded-2xl p-6 shadow-sm border border-default">
                    <p className="text-sm text-body">{s.label}</p>
                    <p className="text-3xl font-bold text-heading mt-1">{questionsLoading ? '…' : s.value}</p>
                    <div className={`mt-3 h-1 rounded-full ${s.color} opacity-60`}></div>
                  </div>
                ))}
              </div>

              {/* Assigned Courses */}
              <div className="bg-white rounded-2xl shadow-sm border border-default p-6">
                <h3 className="font-semibold text-heading mb-4">My Assigned Courses</h3>
                {assignedCourses.length === 0 ? (
                  <p className="text-muted text-sm">No courses assigned.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {assignedCourses.map(c => (
                      <div
                        key={c.id}
                        onClick={() => { setSelectedCourse(c); setActiveTab('questions'); }}
                        className={`flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all ${selectedCourse?.id === c.id ? 'border-custech-primary bg-custech-primary bg-opacity-10' : 'border-default hover:border-custech-navy hover:bg-light'}`}
                      >
                        <div>
                          <p className="font-semibold text-heading">{c.code}</p>
                          <p className="text-sm text-body">{c.title}</p>
                        </div>
                        <div className="text-right">
                          <span className="text-xs bg-light text-muted px-2 py-1 rounded">{c.level}L</span>
                          <p className="text-xs text-muted mt-1">{c.semester_type}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recent questions */}
              <div className="bg-white rounded-2xl shadow-sm border border-default p-6">
                <h3 className="font-semibold text-heading mb-4">Recent Questions</h3>
                {questionsLoading ? (
                  <p className="text-muted text-sm">Loading...</p>
                ) : questions.length === 0 ? (
                  <p className="text-muted text-sm">No questions yet. Start by adding questions to your course.</p>
                ) : (
                  <div className="space-y-2">
                    {questions.slice(0, 5).map(q => (
                      <div key={q.id} className="flex items-center justify-between p-3 bg-light rounded-xl">
                        <p className="text-sm text-body truncate flex-1 mr-4">{q.question_text}</p>
                        <span className={`text-xs px-2 py-1 rounded-full font-medium flex-shrink-0 ${statusColor(q.status)}`}>{q.status}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Question Bank Tab */}
          {activeTab === 'questions' && selectedCourse && (
            <div className="space-y-4">
              {/* Filters */}
              <div className="bg-white rounded-2xl shadow-sm border border-default p-4">
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    placeholder="Search questions..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="flex-1 px-4 py-2 bg-light border border-default rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-custech-navy"
                  />
                  <select value={filterDifficulty} onChange={e => setFilterDifficulty(e.target.value)} className="px-3 py-2 bg-light border border-default rounded-xl text-sm focus:outline-none">
                    <option value="">All Difficulties</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                  <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="px-3 py-2 bg-light border border-default rounded-xl text-sm focus:outline-none">
                    <option value="">All Statuses</option>
                    <option value="draft">Draft</option>
                    <option value="submitted">Submitted</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>

              {/* Questions Table */}
              <div className="bg-white rounded-2xl shadow-sm border border-default overflow-hidden">
                {questionsLoading ? (
                  <div className="p-12 text-center text-muted">Loading questions...</div>
                ) : filteredQuestions.length === 0 ? (
                  <div className="p-12 text-center">
                    <Database size={40} className="text-muted mx-auto mb-3" />
                    <p className="font-semibold text-heading">No questions found</p>
                    <p className="text-sm text-body mt-1">Add your first question or import from CSV.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-light border-b border-default">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-muted uppercase">Question</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-muted uppercase">Topic</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-muted uppercase">Difficulty</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-muted uppercase">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-semibold text-muted uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-default">
                        {filteredQuestions.map(q => (
                          <tr key={q.id} className="hover:bg-light transition-colors">
                            <td className="px-6 py-4 max-w-xs">
                              <p className="truncate text-heading font-medium" title={q.question_text}>{q.question_text}</p>
                            </td>
                            <td className="px-6 py-4">
                              <span className="bg-custech-navy bg-opacity-10 text-custech-navy text-xs px-2 py-1 rounded-full">{q.topic || '—'}</span>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${diffColor(q.difficulty)}`}>{q.difficulty}</span>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor(q.status)}`}>{q.status}</span>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-1">
                                <button onClick={() => handleOpenEdit(q)} className="p-1.5 text-muted hover:text-custech-navy hover:bg-light rounded-lg" title="Edit">
                                  <Pencil size={16} weight="bold" />
                                </button>
                                {q.status === 'draft' && (
                                  <button onClick={() => handleSubmitForReview(q.id)} className="p-1.5 text-muted hover:text-purple-600 hover:bg-light rounded-lg" title="Submit for review">
                                    <CheckCircle size={16} weight="bold" />
                                  </button>
                                )}
                                <button onClick={() => { setReviewingQuestion(q); setShowReviewModal(true); }} className="p-1.5 text-muted hover:text-emerald-600 hover:bg-light rounded-lg" title="Preview">
                                  <ClipboardText size={16} weight="bold" />
                                </button>
                                <button onClick={() => handleDeleteQuestion(q.id)} className="p-1.5 text-muted hover:text-danger hover:bg-light rounded-lg" title="Delete">
                                  <Trash size={16} weight="bold" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Exams Tab */}
          {activeTab === 'exams' && selectedCourse && (
            <div className="space-y-4">
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                {examsLoading ? (
                  <div className="p-12 text-center text-slate-400">Loading examinations...</div>
                ) : exams.length === 0 ? (
                  <div className="p-12 text-center">
                    <ClipboardText size={40} className="text-slate-300 mx-auto mb-3" />
                    <p className="font-semibold text-slate-600">No examinations scheduled</p>
                    <p className="text-sm text-slate-400 mt-1">Examinations for this course will appear here once created by the Exam Officer.</p>
                  </div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Exam Title</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Date</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Duration</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {exams.map(ex => (
                        <tr key={ex.id} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-medium text-slate-800">{ex.title}</td>
                          <td className="px-6 py-4 text-slate-600">{ex.exam_date ? new Date(ex.exam_date).toLocaleDateString() : '—'}</td>
                          <td className="px-6 py-4 text-slate-600">{ex.duration_minutes} min</td>
                          <td className="px-6 py-4">
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${ex.status === 'published' ? 'bg-emerald-100 text-emerald-700' : ex.status === 'completed' ? 'bg-slate-100 text-slate-700' : 'bg-amber-100 text-amber-700'}`}>
                              {ex.status || 'draft'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleViewStudents(ex)}
                                className="inline-flex items-center gap-1 px-2 py-1 bg-custech-primary/10 text-custech-primary hover:bg-custech-primary hover:text-white rounded-lg transition-colors font-medium text-xs"
                                title="View Registered Students"
                              >
                                <Users size={14} />
                                Students
                              </button>
                              <button
                                onClick={() => handleViewResults(ex)}
                                className="inline-flex items-center gap-1 px-2 py-1 bg-custech-green/10 text-custech-green hover:bg-custech-green hover:text-white rounded-lg transition-colors font-medium text-xs"
                                title="View Graded Results"
                              >
                                <ChartBar size={14} />
                                Results
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Add Question Modal */}
      {showAddModal && (
        <QuestionModal
          title="Add New Question"
          formData={formData}
          setFormData={setFormData}
          onSubmit={handleCreateQuestion}
          onClose={handleCloseModals}
          isSubmitting={isSubmitting}
          submitLabel="Create Question"
        />
      )}

      {/* Edit Question Modal */}
      {showEditModal && editingQuestion && (
        <QuestionModal
          title="Edit Question"
          formData={formData}
          setFormData={setFormData}
          onSubmit={handleUpdateQuestion}
          onClose={handleCloseModals}
          isSubmitting={isSubmitting}
          submitLabel="Save Changes"
        />
      )}

      {/* Preview / Review Modal */}
      {showReviewModal && reviewingQuestion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-xl w-full max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b">
              <h3 className="font-semibold text-lg text-slate-800">Question Preview</h3>
              <button onClick={handleCloseModals} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
            </div>
            <div className="p-5 space-y-4">
              <p className="text-slate-800 font-medium">{reviewingQuestion.question_text}</p>
              <div className="space-y-2">
                {reviewingQuestion.options.map((opt, i) => (
                  <div key={opt.id} className={`flex items-center gap-3 p-3 rounded-xl border ${opt.is_correct ? 'border-emerald-400 bg-emerald-50' : 'border-slate-200'}`}>
                    <span className="font-bold text-sm text-slate-500">{String.fromCharCode(65 + i)}.</span>
                    <span className="text-sm text-slate-700">{opt.option_text}</span>
                    {opt.is_correct && <Check size={16} className="text-emerald-600 ml-auto" weight="bold" />}
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-3 pt-2">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${diffColor(reviewingQuestion.difficulty)}`}>{reviewingQuestion.difficulty}</span>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusColor(reviewingQuestion.status)}`}>{reviewingQuestion.status}</span>
                {reviewingQuestion.topic && <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full">{reviewingQuestion.topic}</span>}
              </div>
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              {reviewingQuestion.status === 'draft' && (
                <button
                  onClick={async () => { await handleSubmitForReview(reviewingQuestion.id); handleCloseModals(); }}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium"
                >
                  Submit for Review
                </button>
              )}
              <button onClick={handleCloseModals} className="px-4 py-2 border border-slate-200 rounded-lg text-sm">Close</button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b">
              <h3 className="font-semibold text-lg text-slate-800">Import Questions from CSV</h3>
              <button onClick={handleCloseModals} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
                <FileCsv size={24} className="text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-900 text-sm">Required CSV columns:</p>
                  <p className="text-xs text-blue-700 mt-0.5">question_text, topic, difficulty, option_a, option_b, option_c, option_d, correct_answer</p>
                  <button onClick={handleCsvDownload} className="text-xs text-blue-600 hover:text-blue-800 font-medium mt-2 flex items-center gap-1">
                    <DownloadSimple size={14} /> Download template
                  </button>
                </div>
              </div>
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors">
                <Upload size={32} className="text-slate-400 mx-auto mb-3" />
                <p className="text-sm text-slate-500 mb-3">{csvFile ? csvFile.name : 'Click to select a CSV file'}</p>
                <input type="file" accept=".csv" onChange={handleFileChange} className="hidden" id="csv-import" />
                <label htmlFor="csv-import" className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium cursor-pointer">
                  Select File
                </label>
              </div>
              {importPreview.length > 0 && (
                <div>
                  <p className="font-medium text-slate-800 text-sm mb-2">Preview ({importPreview.length} questions)</p>
                  <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100">
                    {importPreview.map((q, i) => (
                      <div key={i} className="px-4 py-3">
                        <p className="text-sm font-medium text-slate-800 truncate">{q.question_text}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{q.topic} • {q.difficulty} • {q.options.filter(o => o.isCorrect).length === 1 ? '✓ Answer set' : '✗ No answer'}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="p-5 border-t flex justify-end gap-2">
              <button onClick={handleCloseModals} className="px-4 py-2 border border-slate-200 rounded-lg text-sm">Cancel</button>
              <button
                onClick={handleImportQuestions}
                disabled={isSubmitting || importPreview.length === 0}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium"
              >
                {isSubmitting ? 'Importing...' : `Import ${importPreview.length} Questions`}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Registered Students Modal */}
      {showStudentsModal && studentsModalExam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-fade-in">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/50">
              <div>
                <h3 className="font-semibold text-lg text-slate-800">
                  Registered Students
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Examination: <span className="font-medium text-slate-600">{studentsModalExam.title}</span>
                </p>
              </div>
              <button 
                onClick={() => setShowStudentsModal(false)} 
                className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1 min-h-[300px]">
              {studentsLoading ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
                  <div className="w-10 h-10 border-4 border-custech-primary border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm font-medium">Fetching registered students list...</p>
                </div>
              ) : studentsError ? (
                <div className="text-center py-16 text-red-500 space-y-2">
                  <XCircle size={40} className="mx-auto" />
                  <p className="font-semibold">{studentsError}</p>
                </div>
              ) : examStudents.length === 0 ? (
                <div className="text-center py-16 text-slate-400">
                  <Users size={48} className="mx-auto mb-3 text-slate-300" />
                  <p className="font-semibold text-slate-600">No registered students found</p>
                  <p className="text-sm text-slate-400 mt-1">No students have registered for this exam course under the current session.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Summary card inside modal */}
                  <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-400 block font-medium uppercase tracking-wider">Total Registrations</span>
                      <span className="text-xl font-bold text-slate-800">{examStudents.length} students</span>
                    </div>
                    <div className="bg-slate-200/55 p-2 rounded-lg text-slate-500">
                      <Users size={20} />
                    </div>
                  </div>

                  {/* Student list table inside modal */}
                  <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
                    <div className="overflow-x-auto max-h-[45vh]">
                      <table className="w-full text-sm text-left border-collapse">
                        <thead className="bg-slate-50 text-slate-500 text-xs font-semibold border-b border-slate-200 sticky top-0 z-10">
                          <tr>
                            <th className="px-5 py-3.5">S/N</th>
                            <th className="px-5 py-3.5">Matric Number</th>
                            <th className="px-5 py-3.5">Name</th>
                            <th className="px-5 py-3.5">Email</th>
                            <th className="px-5 py-3.5">Department</th>
                            <th className="px-5 py-3.5">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-slate-700">
                          {examStudents.map((student, idx) => (
                            <tr key={student.id} className="hover:bg-slate-50/50 transition-colors">
                              <td className="px-5 py-3.5 font-medium text-slate-400">{idx + 1}</td>
                              <td className="px-5 py-3.5 font-semibold text-custech-primary">{student.matric_number}</td>
                              <td className="px-5 py-3.5 font-medium text-slate-800">{student.first_name} {student.last_name}</td>
                              <td className="px-5 py-3.5 text-slate-500">{student.email}</td>
                              <td className="px-5 py-3.5 text-slate-500">
                                {student.department_code ? `${student.department_code} - ${student.department_name}` : student.department_id || '—'}
                              </td>
                              <td className="px-5 py-3.5">
                                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                                  student.is_active 
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/50' 
                                    : 'bg-red-50 text-red-700 border border-red-200/50'
                                }`}>
                                  {student.is_active ? 'Active' : 'Inactive'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-5 border-t border-slate-100 flex justify-end bg-slate-50/50">
              <button 
                onClick={() => setShowStudentsModal(false)} 
                className="px-4 py-2 border border-slate-200 hover:bg-slate-100 text-slate-700 rounded-lg text-sm font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Exam Results Modal */}
      {showResultsModal && resultsModalExam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-fade-in">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/50">
              <div>
                <h3 className="font-semibold text-lg text-slate-800">
                  Student Results
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Examination: <span className="font-medium text-slate-600">{resultsModalExam.title}</span>
                </p>
              </div>
              <button 
                onClick={() => setShowResultsModal(false)} 
                className="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1 min-h-[300px]">
              {resultsLoading ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
                  <div className="w-10 h-10 border-4 border-custech-primary border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-sm font-medium">Fetching examination results...</p>
                </div>
              ) : resultsError ? (
                <div className="text-center py-16 text-red-500 space-y-2">
                  <XCircle size={40} className="mx-auto" />
                  <p className="font-semibold">{resultsError}</p>
                </div>
              ) : examResults.length === 0 ? (
                <div className="text-center py-16 text-slate-400">
                  <ChartBar size={48} className="mx-auto mb-3 text-slate-300" />
                  <p className="font-semibold text-slate-600">No results found</p>
                  <p className="text-sm text-slate-400 mt-1">No students have taken or submitted results for this exam yet.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Summary card inside modal */}
                  <div className="bg-slate-50 border border-slate-200/60 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-400 block font-medium uppercase tracking-wider">Total Submissions</span>
                      <span className="text-xl font-bold text-slate-800">{examResults.length} students graded</span>
                    </div>
                    <button
                      onClick={() => handleExportCSV(resultsModalExam.id)}
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-custech-green hover:bg-emerald-700 text-white rounded-lg transition-colors font-semibold text-sm shadow"
                    >
                      <DownloadSimple size={16} weight="bold" />
                      Export to CSV
                    </button>
                  </div>

                  {/* Results table inside modal */}
                  <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
                    <div className="overflow-x-auto max-h-[45vh]">
                      <table className="w-full text-sm text-left border-collapse">
                        <thead className="bg-slate-50 text-slate-500 text-xs font-semibold border-b border-slate-200 sticky top-0 z-10">
                          <tr>
                            <th className="px-5 py-3.5">S/N</th>
                            <th className="px-5 py-3.5">Matric No</th>
                            <th className="px-5 py-3.5">Student Name</th>
                            <th className="px-5 py-3.5">Score</th>
                            <th className="px-5 py-3.5">Percentage</th>
                            <th className="px-5 py-3.5">Grade</th>
                            <th className="px-5 py-3.5">Date Taken</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 text-slate-700">
                          {examResults.map((res, idx) => (
                            <tr key={res.matric_number} className="hover:bg-slate-50/50 transition-colors">
                              <td className="px-5 py-3.5 font-medium text-slate-400">{idx + 1}</td>
                              <td className="px-5 py-3.5 font-semibold text-custech-primary">{res.matric_number}</td>
                              <td className="px-5 py-3.5 font-medium text-slate-800">{res.student_name}</td>
                              <td className="px-5 py-3.5 font-medium text-slate-700">{res.score} / {res.total_questions}</td>
                              <td className="px-5 py-3.5 font-semibold text-slate-800">{res.percentage}%</td>
                              <td className="px-5 py-3.5">
                                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold ${
                                  res.grade === 'A' || res.grade === 'B'
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/50' 
                                    : res.grade === 'F'
                                    ? 'bg-red-50 text-red-700 border border-red-200/50'
                                    : 'bg-amber-50 text-amber-700 border border-amber-200/50'
                                }`}>
                                  {res.grade}
                                </span>
                              </td>
                              <td className="px-5 py-3.5 text-slate-500">
                                {new Date(res.date_taken).toLocaleDateString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-5 border-t border-slate-100 flex justify-end bg-slate-50/50">
              <button 
                onClick={() => setShowResultsModal(false)} 
                className="px-4 py-2 border border-slate-200 hover:bg-slate-100 text-slate-700 rounded-lg text-sm font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Shared Question Form Modal
interface QuestionModalProps {
  title: string;
  formData: QuestionFormData;
  setFormData: React.Dispatch<React.SetStateAction<QuestionFormData>>;
  onSubmit: () => void;
  onClose: () => void;
  isSubmitting: boolean;
  submitLabel: string;
}

const QuestionModal: React.FC<QuestionModalProps> = ({ title, formData, setFormData, onSubmit, onClose, isSubmitting, submitLabel }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div className="flex items-center justify-between p-5 border-b">
        <h3 className="font-semibold text-lg text-slate-800">{title}</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Question Text *</label>
          <textarea
            className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm min-h-[100px] focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Enter question..."
            value={formData.question_text}
            onChange={e => setFormData(prev => ({ ...prev, question_text: e.target.value }))}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Topic *</label>
            <input
              className="w-full border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Algebra"
              value={formData.topic}
              onChange={e => setFormData(prev => ({ ...prev, topic: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Difficulty *</label>
            <select
              className="w-full border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.difficulty}
              onChange={e => setFormData(prev => ({ ...prev, difficulty: e.target.value as 'easy' | 'medium' | 'hard' }))}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Answer Options * <span className="text-xs text-slate-400">(select the correct one)</span></label>
          <div className="space-y-2">
            {formData.options.map((opt, i) => (
              <div key={i} className="flex items-center gap-3">
                <input
                  type="radio"
                  name="correct"
                  checked={opt.isCorrect}
                  onChange={() => setFormData(prev => ({ ...prev, options: prev.options.map((o, j) => ({ ...o, isCorrect: j === i })) }))}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="w-6 text-sm font-semibold text-slate-500">{String.fromCharCode(65 + i)}.</span>
                <input
                  className="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={`Option ${String.fromCharCode(65 + i)}`}
                  value={opt.text}
                  onChange={e => setFormData(prev => ({ ...prev, options: prev.options.map((o, j) => j === i ? { ...o, text: e.target.value } : o) }))}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="p-5 border-t flex justify-end gap-2">
        <button onClick={onClose} disabled={isSubmitting} className="px-4 py-2 border border-slate-200 rounded-lg text-sm">Cancel</button>
        <button
          onClick={onSubmit}
          disabled={isSubmitting}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium"
        >
          {isSubmitting ? 'Saving...' : submitLabel}
        </button>
      </div>
    </div>
  </div>
);

export default LecturerDashboard;
