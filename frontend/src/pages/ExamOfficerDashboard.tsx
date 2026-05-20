import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Settings, Calendar, Users, MapPin, FileText, CheckCircle, AlertTriangle, 
  Printer, Download, Loader2, Plus, Trash2, GraduationCap, Bell, Clock,
  LayoutDashboard, BookOpen, BarChart3, ChevronRight, User, LogOut,
  ClipboardList, School, FileCheck, TrendingUp, Activity, MoreHorizontal
} from 'lucide-react';
import { apiRequest, logout, getAuthToken, ApiError } from '../lib/api';

const API_BASE = '/api/v1';

interface Course {
  id: string;
  code: string;
  title: string;
}

interface Venue {
  id: string;
  name: string;
  capacity: number;
}

interface Exam {
  id: string;
  title: string;
  course_id: string;
  exam_date: string;
  start_time: string;
  duration_minutes: number;
  status: 'draft' | 'scheduled' | 'active' | 'completed';
}

interface AcademicSession {
  id: string;
  session_code?: string;
  is_current?: boolean;
}

interface Semester {
  id: string;
  academic_session_id?: string;
  is_current?: boolean;
  semester_type?: string;
}

interface StudentRow {
  id: string;
}

const asList = <T,>(data: unknown): T[] => (Array.isArray(data) ? data : []);

const errorMessage = (err: unknown, fallback: string) =>
  err instanceof ApiError ? err.message : fallback;

const ExamOfficerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'wizard' | 'blueprint' | 'venue' | 'slips' | 'results'>('wizard');
  const [activeExamId, setActiveExamId] = useState<string>(localStorage.getItem('activeExamId') || '');

  // Data states
  const [courses, setCourses] = useState<Course[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [departments, setDepartments] = useState<{ id: string; code: string; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [academicContext, setAcademicContext] = useState<{ sessionId: string; semesterId: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form states
  const [examForm, setExamForm] = useState({
    title: '',
    course_id: '',
    date: '',
    time: '',
    duration: '120',
  });

  const [blueprintConfig, setBlueprintConfig] = useState({
    totalQuestions: 50,
    topics: [{ name: '', percentage: 20, questionCount: 10 }],
  });

  const [venueStatus, setVenueStatus] = useState<'pending' | 'allocated'>('pending');
  const [allocating, setAllocating] = useState(false);
  const [selectedVenues, setSelectedVenues] = useState<string[]>([]);
  const [registeredStudents, setRegisteredStudents] = useState(0);

  const [resultSettings, setResultSettings] = useState({
    releaseMode: 'manual' as 'manual' | 'automatic' | 'immediate',
    embargoEnabled: true,
    releaseDate: '',
    passingScore: 40,
  });

  const loadDashboardData = async () => {
    setLoading(true);
    setLoadError(null);
    const failures: string[] = [];

    const [coursesRes, venuesRes, examsRes, sessionsRes, departmentsRes, studentsRes] =
      await Promise.allSettled([
        apiRequest<unknown>('/api/v1/academics/courses'),
        apiRequest<unknown>('/api/v1/venues?is_active=true'),
        apiRequest<unknown>('/api/v1/examinations/?limit=100'),
        apiRequest<unknown>('/api/v1/academics/sessions'),
        apiRequest<unknown>('/api/v1/academics/departments'),
        apiRequest<unknown>('/api/v1/students/?limit=500'),
      ]);

    if (coursesRes.status === 'fulfilled') {
      setCourses(asList<Course>(coursesRes.value));
    } else {
      failures.push(`Courses (${errorMessage(coursesRes.reason, 'access denied')})`);
      setCourses([]);
    }

    if (venuesRes.status === 'fulfilled') {
      setVenues(asList<Venue>(venuesRes.value));
    } else {
      failures.push(`Venues (${errorMessage(venuesRes.reason, 'access denied')})`);
      setVenues([]);
    }

    if (examsRes.status === 'fulfilled') {
      setExams(asList<Exam>(examsRes.value));
    } else {
      failures.push(`Examinations (${errorMessage(examsRes.reason, 'access denied')})`);
      setExams([]);
    }

    if (departmentsRes.status === 'fulfilled') {
      setDepartments(asList(departmentsRes.value));
    } else {
      setDepartments([]);
    }

    if (studentsRes.status === 'fulfilled') {
      setRegisteredStudents(asList<StudentRow>(studentsRes.value).length);
    }

    let sessionId = '';
    let semesterId = '';
    if (sessionsRes.status === 'fulfilled') {
      const sessions = asList<AcademicSession>(sessionsRes.value);
      const currentSession = sessions.find((s) => s.is_current) ?? sessions[0];
      if (currentSession?.id) {
        sessionId = currentSession.id;
        try {
          const semData = await apiRequest<unknown>(
            `/api/v1/academics/semesters?session_id=${encodeURIComponent(sessionId)}`
          );
          const semesters = asList<Semester>(semData);
          const currentSemester = semesters.find((s) => s.is_current) ?? semesters[0];
          if (currentSemester?.id) {
            semesterId = currentSemester.id;
          }
        } catch (err) {
          failures.push(`Semesters (${errorMessage(err, 'unavailable')})`);
        }
      }
    } else {
      failures.push(`Academic sessions (${errorMessage(sessionsRes.reason, 'access denied')})`);
    }

    if (sessionId && semesterId) {
      setAcademicContext({ sessionId, semesterId });
    } else {
      setAcademicContext(null);
      failures.push('Current academic session/semester not configured');
    }

    if (failures.length > 0) {
      setLoadError(failures.join(' · '));
    }

    if (activeExamId) {
      await loadExamDetails(activeExamId);
    }
    setLoading(false);
  };

  useEffect(() => {
    void loadDashboardData();
  }, []);

  const loadExamDetails = async (examId: string) => {
    try {
      const exam = await apiRequest<Exam>(`/api/v1/examinations/${examId}`);
      setExamForm({
        title: exam.title,
        course_id: exam.course_id,
        date: exam.exam_date,
        time: exam.start_time?.slice(0, 5) || '',
        duration: String(exam.duration_minutes),
      });
    } catch (error) {
      console.error('Failed to load exam details:', error);
    }
  };

  const handleCreateExam = async () => {
    if (!examForm.title || !examForm.course_id || !examForm.date || !examForm.time) {
      alert('Please fill in all required fields');
      return;
    }
    if (!academicContext) {
      alert('Academic session is not loaded. Refresh the page or ask an admin to set the current session.');
      return;
    }

    setIsSubmitting(true);
    try {
      const duration = parseInt(examForm.duration, 10) || 120;
      const startIso = `${examForm.date}T${examForm.time}:00`;
      const payload = {
        title: examForm.title,
        course_id: examForm.course_id,
        exam_date: examForm.date,
        start_time: startIso,
        duration_minutes: duration,
        total_points: 100,
        pass_points: 40,
        academic_session_id: academicContext.sessionId,
        semester_id: academicContext.semesterId,
        question_ids: [] as string[],
      };

      const response = await apiRequest<{ id: string }>('/api/v1/examinations', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setActiveExamId(response.id);
      localStorage.setItem('activeExamId', response.id);
      
      const updatedExams = await apiRequest<unknown>('/api/v1/examinations?limit=100');
      setExams(asList<Exam>(updatedExams));
      
      alert('Exam created successfully!');
      setActiveTab('blueprint');
    } catch (error) {
      alert(errorMessage(error, 'Failed to create exam. Please try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSaveBlueprint = async () => {
    if (!activeExamId) {
      alert('Please create an exam first');
      return;
    }

    setIsSubmitting(true);
    try {
      const topics = blueprintConfig.topics.filter((t) => t.name?.trim());
      const requirements = (topics.length ? topics : [{ name: 'General', percentage: 100, questionCount: blueprintConfig.totalQuestions }]).map((t) => ({
        topic: t.name.trim(),
        difficulty: 'MEDIUM',
        cognitive_level: 'UNDERSTANDING',
        question_count: t.questionCount || Math.max(1, Math.floor(blueprintConfig.totalQuestions / Math.max(1, topics.length))),
      }));

      const questionSum = requirements.reduce((sum, r) => sum + r.question_count, 0);
      if (questionSum !== blueprintConfig.totalQuestions && requirements.length > 0) {
        requirements[0].question_count += blueprintConfig.totalQuestions - questionSum;
      }

      await apiRequest('/api/v1/exam-blueprint/', {
        method: 'POST',
        body: JSON.stringify({
          examination_id: activeExamId,
          total_questions: blueprintConfig.totalQuestions,
          total_points: blueprintConfig.totalQuestions,
          requirements,
          randomization_enabled: true,
          option_shuffle_enabled: true,
          question_order_randomization: true,
        }),
      });

      alert('Blueprint saved successfully!');
      setActiveTab('venue');
    } catch (error) {
      alert('Failed to save blueprint. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAllocateVenues = async () => {
    if (!activeExamId || selectedVenues.length === 0) {
      alert('Please select at least one venue');
      return;
    }

    setAllocating(true);
    try {
      await apiRequest(`/api/v1/examinations/${activeExamId}/allocate-venues`, {
        method: 'POST',
        body: JSON.stringify({
          venue_ids: selectedVenues,
        }),
      });

      setVenueStatus('allocated');
      alert('Venues allocated successfully!');
    } catch (error) {
      alert('Failed to allocate venues. Please try again.');
    } finally {
      setAllocating(false);
    }
  };

  const handleSaveResultSettings = async () => {
    if (!activeExamId) {
      alert('Please create an exam first');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiRequest(`/api/v1/examinations/${activeExamId}`, {
        method: 'PUT',
        body: JSON.stringify({
          release_mode: resultSettings.releaseMode === 'immediate' ? 'auto_at' : resultSettings.releaseMode,
          embargo_active: resultSettings.embargoEnabled,
          release_at: resultSettings.releaseDate ? `${resultSettings.releaseDate}T00:00:00` : null,
          pass_points: resultSettings.passingScore,
          show_results_immediately: resultSettings.releaseMode === 'immediate',
        }),
      });

      alert('Result settings saved successfully!');
    } catch (error) {
      alert('Failed to save settings. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTopicChange = (index: number, field: 'name' | 'percentage', value: string | number) => {
    setBlueprintConfig(prev => {
      const newTopics = [...prev.topics];
      newTopics[index] = { 
        ...newTopics[index], 
        [field]: value,
        questionCount: field === 'percentage' 
          ? Math.round((value as number / 100) * prev.totalQuestions)
          : newTopics[index].questionCount
      };
      return { ...prev, topics: newTopics };
    });
  };

  const addTopic = () => {
    setBlueprintConfig(prev => ({
      ...prev,
      topics: [...prev.topics, { name: '', percentage: 0, questionCount: 0 }],
    }));
  };

  const removeTopic = (index: number) => {
    setBlueprintConfig(prev => ({
      ...prev,
      topics: prev.topics.filter((_, i) => i !== index),
    }));
  };

  const downloadFile = (url: string, filename: string) => {
    const token = getAuthToken();
    const a = document.createElement('a');
    a.href = `${url}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
    a.download = filename;
    a.click();
  };

  const tabs = [
    { id: 'wizard', label: 'Exam Wizard', icon: <Calendar className="w-5 h-5" /> },
    { id: 'blueprint', label: 'Blueprint Editor', icon: <Settings className="w-5 h-5" /> },
    { id: 'venue', label: 'Venue Allocation', icon: <MapPin className="w-5 h-5" /> },
    { id: 'slips', label: 'Exam Slips', icon: <Printer className="w-5 h-5" /> },
    { id: 'results', label: 'Result Settings', icon: <FileText className="w-5 h-5" /> },
  ] as const;

  // Calculate statistics
  const stats = {
    totalExams: exams.length,
    scheduled: exams.filter(e => e.status === 'scheduled').length,
    active: exams.filter(e => e.status === 'active').length,
    completed: exams.filter(e => e.status === 'completed').length,
    totalVenues: venues.length,
    totalCapacity: venues.reduce((sum, v) => sum + v.capacity, 0),
  };

  const recentExams = [...exams].slice(0, 5);

  const inputClass =
    'w-full h-11 bg-white border-2 border-input rounded-lg px-4 text-heading placeholder:text-placeholder focus:border-custech-navy focus:ring-2 focus:ring-custech-navy/15 outline-none transition-colors';
  const labelClass = 'block text-sm font-medium text-heading mb-2';

  return (
    <div className="min-h-screen bg-light flex font-sans">
      {/* Professional Sidebar */}
      <aside className="w-64 bg-dark border-r border-darker flex flex-col fixed h-full z-20">
        {/* Logo */}
        <div className="p-6 border-b border-darker">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-custech-gradient rounded-xl flex items-center justify-center shadow-lg shadow-custech-primary/20">
              <School size={24} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-white leading-tight">Custech</h1>
              <p className="text-xs text-gray-400">Exam Management</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
          <div className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Examination
          </div>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-custech-primary text-white shadow-md'
                  : 'text-gray-400 hover:bg-darker hover:text-white'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.id === 'slips' && activeExamId && (
                <span className="ml-auto w-2 h-2 bg-custech-green rounded-full"></span>
              )}
            </button>
          ))}

          <div className="px-3 mt-8 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Resources
          </div>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:bg-darker hover:text-white transition-all text-sm font-medium">
            <BookOpen size={20} />
            <span>Courses</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:bg-darker hover:text-white transition-all text-sm font-medium">
            <MapPin size={20} />
            <span>Venues</span>
            <span className="ml-auto text-xs text-gray-500">{venues.length}</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-400 hover:bg-darker hover:text-white transition-all text-sm font-medium">
            <Users size={20} />
            <span>Students</span>
          </button>

          <div className="px-3 mt-8 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Quick Stats
          </div>
          <div className="px-3 py-2 space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Active Exams</span>
              <span className="font-semibold text-emerald-400">{stats.active}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Scheduled</span>
              <span className="font-semibold text-blue-400">{stats.scheduled}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Capacity</span>
              <span className="font-semibold text-gray-200">{stats.totalCapacity.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Courses</span>
              <span className="font-semibold text-gray-200">{courses.length}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-400">Departments</span>
              <span className="font-semibold text-gray-200">{departments.length}</span>
            </div>
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-darker">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center">
              <User size={20} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">Exam Officer</p>
              <p className="text-xs text-gray-400">Administrator</p>
            </div>
            <button 
              onClick={async () => { await logout(); navigate('/', { replace: true }); }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen bg-light">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b border-default sticky top-0 z-10">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h2 className="text-2xl font-bold text-heading">
                {tabs.find(t => t.id === activeTab)?.label}
              </h2>
              <p className="text-sm text-muted mt-0.5">
                {activeTab === 'wizard' && 'Create and schedule examinations'}
                {activeTab === 'blueprint' && 'Configure question distribution'}
                {activeTab === 'venue' && 'Allocate examination venues'}
                {activeTab === 'slips' && 'Generate and distribute exam slips'}
                {activeTab === 'results' && 'Configure result release settings'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-muted hover:text-heading transition-colors">
                <Bell size={20} />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-light rounded-lg text-sm text-muted border border-default">
                <Clock size={14} />
                <span>{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="p-8">
          {loadError && (
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              <span>
                <strong>Some data could not be loaded:</strong> {loadError}
                {' '}Log out and back in if you were recently granted officer permissions.
              </span>
              <button
                type="button"
                onClick={() => void loadDashboardData()}
                className="shrink-0 rounded-lg border border-amber-300 bg-white px-3 py-1.5 font-medium hover:bg-amber-100"
              >
                Retry
              </button>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center gap-2 py-16 text-muted">
              <Loader2 className="h-6 w-6 animate-spin" />
              Loading examination data…
            </div>
          ) : (
          <>
          {/* Stats Overview - Show on all tabs */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-2xl p-6 border border-default shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted">Total Exams</p>
                  <p className="text-3xl font-bold text-heading mt-1">{stats.totalExams}</p>
                </div>
                <div className="w-12 h-12 bg-custech-primary/10 rounded-xl flex items-center justify-center">
                  <ClipboardList size={24} className="text-custech-primary" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm">
                <span className="text-emerald-600 font-medium flex items-center gap-1">
                  <TrendingUp size={14} />
                  {stats.scheduled}
                </span>
                <span className="text-muted">scheduled</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-default shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted">Active Now</p>
                  <p className="text-3xl font-bold text-heading mt-1">{stats.active}</p>
                </div>
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <Activity size={24} className="text-emerald-600" />
                </div>
              </div>
              <div className="mt-4">
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div 
                    className="bg-emerald-500 h-2 rounded-full transition-all min-w-0" 
                    style={{ width: `${stats.totalExams ? (stats.active / stats.totalExams) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-default shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted">Total Venues</p>
                  <p className="text-3xl font-bold text-heading mt-1">{stats.totalVenues}</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                  <MapPin size={24} className="text-amber-600" />
                </div>
              </div>
              <div className="mt-4 text-sm text-muted">
                {stats.totalCapacity.toLocaleString()} total seats
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-default shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted">Completed</p>
                  <p className="text-3xl font-bold text-heading mt-1">{stats.completed}</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                  <FileCheck size={24} className="text-purple-600" />
                </div>
              </div>
              <div className="mt-4 text-sm text-muted">
                Exams finished this session
              </div>
            </div>
          </div>

          {/* Tab Content */}
          <div className="bg-white border border-default rounded-2xl shadow-sm overflow-hidden">
            {/* Navigation Tabs */}
            <div className="flex flex-wrap gap-1 bg-light p-2 border-b border-default">
              {tabs.map((tab) => (
                <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-custech-primary text-white shadow-sm'
                  : 'text-muted hover:text-heading hover:bg-white'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
            </div>

            {/* Tab Content Areas */}
            <div className="p-6 md:p-8">
          
          {/* Exam Wizard */}
          {activeTab === 'wizard' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-default pb-4">
                <h3 className="text-xl font-semibold text-heading">Schedule Examination</h3>
                <span className="px-3 py-1 bg-custech-primary/10 text-custech-primary rounded-full text-sm font-medium border border-custech-primary/20">
                  Step 1 of 5
                </span>
              </div>
              
              {/* Active Exam Selector */}
              {exams.length > 0 && (
                <div className="bg-light rounded-xl p-4 border border-default">
                  <label className={labelClass}>Continue with existing exam</label>
                  <select 
                    className={inputClass}
                    value={activeExamId}
                    onChange={(e) => {
                      setActiveExamId(e.target.value);
                      localStorage.setItem('activeExamId', e.target.value);
                      if (e.target.value) loadExamDetails(e.target.value);
                    }}
                  >
                    <option value="">Create new exam...</option>
                    {exams.map(exam => (
                      <option key={exam.id} value={exam.id}>{exam.title} ({exam.exam_date})</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className={labelClass}>Examination Title *</label>
                  <input 
                    type="text" 
                    className={inputClass}
                    placeholder="e.g. GST 101 Mid-Semester Exam" 
                    value={examForm.title}
                    onChange={(e) => setExamForm(prev => ({ ...prev, title: e.target.value }))}
                  />
                </div>
                <div>
                  <label className={labelClass}>Course *</label>
                  <select 
                    className={inputClass}
                    value={examForm.course_id}
                    onChange={(e) => setExamForm(prev => ({ ...prev, course_id: e.target.value }))}
                  >
                    <option value="">Select a course</option>
                    {courses.map(course => (
                      <option key={course.id} value={course.id}>{course.code} - {course.title}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Date *</label>
                  <input 
                    type="date" 
                    className={inputClass}
                    value={examForm.date}
                    onChange={(e) => setExamForm(prev => ({ ...prev, date: e.target.value }))}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Start Time *</label>
                    <input 
                      type="time" 
                      className={inputClass}
                      value={examForm.time}
                      onChange={(e) => setExamForm(prev => ({ ...prev, time: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Duration (min) *</label>
                    <input 
                      type="number" 
                      className={inputClass}
                      placeholder="120" 
                      value={examForm.duration}
                      onChange={(e) => setExamForm(prev => ({ ...prev, duration: e.target.value }))}
                    />
                  </div>
                </div>
              </div>
              <div className="flex justify-end pt-4 border-t border-default">
                <button 
                  onClick={handleCreateExam}
                  disabled={isSubmitting}
                  className="bg-custech-primary hover:bg-custech-primary-light disabled:opacity-50 text-white px-8 py-3 rounded-lg font-medium transition-all shadow-md active:scale-[0.98] flex items-center gap-2"
                >
                  {isSubmitting && <Loader2 className="w-5 h-5 animate-spin" />}
                  {!isSubmitting && <CheckCircle className="w-5 h-5" />}
                  {activeExamId ? 'Update & Continue' : 'Save & Continue'}
                </button>
              </div>
            </div>
          )}

          {/* Blueprint Editor */}
          {activeTab === 'blueprint' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-default pb-4">
                <h3 className="text-xl font-semibold text-heading">Question Blueprint</h3>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                  Step 2 of 5
                </span>
              </div>
              <div className="bg-light rounded-xl p-6 border border-default">
                <div className="flex justify-between items-center mb-6">
                  <h4 className="text-lg font-medium text-heading">Topic Distribution</h4>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-muted">Total Questions</span>
                    <input 
                      type="number" 
                      value={blueprintConfig.totalQuestions}
                      onChange={(e) => setBlueprintConfig(prev => ({ ...prev, totalQuestions: parseInt(e.target.value) || 0 }))}
                      className="w-20 h-10 bg-white border-2 border-input rounded-lg px-3 text-center text-sm text-heading"
                    />
                  </div>
                </div>
                
                <div className="space-y-4">
                  {blueprintConfig.topics.map((topic, i) => (
                    <div key={i} className="flex items-center gap-4">
                      <input
                        type="text"
                        value={topic.name}
                        onChange={(e) => handleTopicChange(i, 'name', e.target.value)}
                        placeholder="Topic name"
                        className="w-1/3 h-10 bg-white border-2 border-input rounded-lg px-3 text-sm text-heading placeholder:text-placeholder"
                      />
                      <div className="flex-1 bg-slate-200 h-3 rounded-full overflow-hidden">
                        <div 
                          className="bg-custech-primary h-full transition-all" 
                          style={{ width: `${topic.percentage}%` }}
                        ></div>
                      </div>
                      <div className="w-32 flex gap-2 items-center">
                        <input 
                          type="number" 
                          value={topic.percentage}
                          onChange={(e) => handleTopicChange(i, 'percentage', parseInt(e.target.value) || 0)}
                          className="w-16 h-10 bg-white border-2 border-input rounded-lg px-2 text-center text-sm text-heading" 
                        />
                        <span className="text-xs text-muted">%</span>
                        <button
                          onClick={() => removeTopic(i)}
                          className="p-1 text-muted hover:text-danger transition-colors"
                          title="Remove topic"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-8 flex justify-between items-center pt-4 border-t border-default">
                  <button 
                    onClick={addTopic}
                    className="border-2 border-default text-heading hover:bg-white px-4 py-2 rounded-lg transition-all flex items-center gap-2"
                  >
                    <Plus size={16} />
                    Add Topic
                  </button>
                  <button 
                    onClick={handleSaveBlueprint}
                    disabled={isSubmitting || !activeExamId}
                    className="bg-custech-primary hover:bg-custech-primary-light disabled:opacity-50 text-white px-6 py-2 rounded-lg transition-all flex items-center gap-2"
                  >
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    Save Blueprint & Continue
                  </button>
                </div>
                
                {!activeExamId && (
                  <p className="text-amber-700 text-sm mt-4">Please create an exam in Step 1 first.</p>
                )}
              </div>
            </div>
          )}

          {/* Venue Allocation */}
          {activeTab === 'venue' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-default pb-4">
                <h3 className="text-xl font-semibold text-heading">Venue Allocation</h3>
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                  Step 3 of 5
                </span>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="col-span-2 bg-white rounded-xl border border-default overflow-hidden">
                  <div className="p-4 border-b border-default bg-light flex justify-between items-center">
                    <h4 className="font-medium text-heading">Available Venues</h4>
                    <span className="text-xs font-semibold bg-white border border-default px-2 py-1 rounded text-muted">
                      Selected: {selectedVenues.length} venues
                    </span>
                  </div>
                  <table className="w-full text-sm text-left">
                    <thead className="bg-light text-muted uppercase text-xs">
                      <tr>
                        <th className="px-6 py-3">Select</th>
                        <th className="px-6 py-3">Venue</th>
                        <th className="px-6 py-3">Capacity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {venues.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="px-6 py-8 text-center text-muted">
                            No venues available. Please add venues in the Admin dashboard.
                          </td>
                        </tr>
                      ) : (
                        venues.map((venue) => (
                          <tr 
                            key={venue.id} 
                            className={`border-b border-default ${selectedVenues.includes(venue.id) ? 'bg-custech-primary/5' : ''}`}
                          >
                            <td className="px-6 py-4">
                              <input
                                type="checkbox"
                                checked={selectedVenues.includes(venue.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedVenues(prev => [...prev, venue.id]);
                                  } else {
                                    setSelectedVenues(prev => prev.filter(id => id !== venue.id));
                                  }
                                }}
                                className="w-4 h-4 rounded border-input text-custech-primary focus:ring-custech-navy"
                              />
                            </td>
                            <td className="px-6 py-4 font-medium text-heading">{venue.name}</td>
                            <td className="px-6 py-4 text-body">{venue.capacity} seats</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="bg-light rounded-xl border border-default p-6 flex flex-col justify-between">
                  <div>
                    <h4 className="text-lg font-medium text-heading mb-4">Allocation Summary</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted">Registered Students:</span>
                        <span className="font-bold text-heading">{registeredStudents || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted">Selected Capacity:</span>
                        <span className="font-bold text-heading">
                          {venues
                            .filter(v => selectedVenues.includes(v.id))
                            .reduce((sum, v) => sum + v.capacity, 0)} seats
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 h-2 rounded-full mt-4">
                        <div 
                          className="bg-custech-navy h-full rounded-full transition-all min-w-0" 
                          style={{ 
                            width: registeredStudents 
                              ? `${Math.min(100, (venues.filter(v => selectedVenues.includes(v.id)).reduce((sum, v) => sum + v.capacity, 0) / registeredStudents) * 100)}%` 
                              : '0%' 
                          }}
                        ></div>
                      </div>
                      <div className="text-xs text-right text-muted mt-1">
                        {selectedVenues.length} venues selected
                      </div>
                    </div>
                  </div>
                  
                  {!activeExamId && (
                    <p className="text-amber-700 text-sm mt-4">Create an exam first.</p>
                  )}
                  
                  {venueStatus === 'pending' ? (
                    <button 
                      onClick={handleAllocateVenues}
                      disabled={allocating || selectedVenues.length === 0 || !activeExamId}
                      className="w-full mt-8 bg-custech-navy hover:opacity-90 disabled:opacity-50 text-white px-4 py-3 rounded-lg font-medium transition-all flex justify-center items-center gap-2"
                    >
                      {allocating ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          Run Allocation
                        </>
                      )}
                    </button>
                  ) : (
                    <div className="mt-8 bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
                      <div>
                        <h4 className="font-medium">Allocation Complete</h4>
                        <p className="text-sm mt-1 text-emerald-700">Venues allocated successfully.</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Exam Slips */}
          {activeTab === 'slips' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-default pb-4">
                <h3 className="text-xl font-semibold text-heading">Exam Slips & Documents</h3>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                  Step 4 of 5
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white border border-default rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-custech-primary/10 rounded-xl flex items-center justify-center mb-6">
                    <Printer className="w-6 h-6 text-custech-primary" />
                  </div>
                  <h4 className="text-xl font-medium text-heading mb-2">Bulk Slip Generation</h4>
                  <p className="text-muted text-sm mb-6">Download a consolidated PDF of exam slips for allocated students.</p>
                  <button
                    className="w-full bg-custech-primary hover:bg-custech-primary-light text-white px-4 py-3 rounded-lg font-medium transition-all flex justify-center items-center gap-2 disabled:opacity-50"
                    onClick={() => activeExamId && downloadFile(`${API_BASE}/examinations/${activeExamId}/slips`, `exam_slips_${activeExamId}.pdf`)}
                    disabled={!activeExamId}
                  >
                    <Download className="w-5 h-5" />
                    Download All Slips (PDF)
                  </button>
                </div>
                
                <div className="bg-white border border-default rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                    <Users className="w-6 h-6 text-purple-600" />
                  </div>
                  <h4 className="text-xl font-medium text-heading mb-2">Results Export</h4>
                  <p className="text-muted text-sm mb-6">Export examination results as a CSV file for review or reporting.</p>
                  <button
                    className="w-full bg-custech-navy hover:opacity-90 text-white px-4 py-3 rounded-lg font-medium transition-all flex justify-center items-center gap-2 disabled:opacity-50"
                    onClick={() => activeExamId && downloadFile(`${API_BASE}/examinations/${activeExamId}/results/export`, `results_${activeExamId}.csv`)}
                    disabled={!activeExamId}
                  >
                    <Download className="w-5 h-5" />
                    Export Results (CSV)
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Results Settings */}
          {activeTab === 'results' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-default pb-4">
                <h3 className="text-xl font-semibold text-heading">Post-Exam & Result Settings</h3>
                <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-medium">
                  Step 5 of 5
                </span>
              </div>
              
              <div className="max-w-2xl space-y-6">
                <div className="bg-light p-6 rounded-xl border border-default">
                  <h4 className="text-lg font-medium text-heading mb-4">Result Release Mode</h4>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-default rounded-lg hover:bg-white cursor-pointer transition-colors bg-white">
                      <input 
                        type="radio" 
                        name="releaseMode" 
                        className="w-4 h-4 text-custech-primary focus:ring-custech-navy" 
                        checked={resultSettings.releaseMode === 'manual'}
                        onChange={() => setResultSettings(prev => ({ ...prev, releaseMode: 'manual' }))}
                      />
                      <div>
                        <div className="font-medium text-heading">Manual Release</div>
                        <div className="text-sm text-muted">Exam Officer must explicitly trigger result publication.</div>
                      </div>
                    </label>
                    <label className="flex flex-wrap items-center gap-3 p-3 border border-default rounded-lg hover:bg-white cursor-pointer transition-colors bg-white">
                      <input 
                        type="radio" 
                        name="releaseMode" 
                        className="w-4 h-4 text-custech-primary focus:ring-custech-navy" 
                        checked={resultSettings.releaseMode === 'automatic'}
                        onChange={() => setResultSettings(prev => ({ ...prev, releaseMode: 'automatic' }))}
                      />
                      <div className="flex-1 min-w-[200px]">
                        <div className="font-medium text-heading">Automatic Release</div>
                        <div className="text-sm text-muted">Results publish at a scheduled time.</div>
                      </div>
                      {resultSettings.releaseMode === 'automatic' && (
                        <input
                          type="datetime-local"
                          value={resultSettings.releaseDate}
                          onChange={(e) => setResultSettings(prev => ({ ...prev, releaseDate: e.target.value }))}
                          className={`${inputClass} w-auto ml-auto`}
                        />
                      )}
                    </label>
                    <label className="flex items-center gap-3 p-3 border border-default rounded-lg hover:bg-white cursor-pointer transition-colors bg-white">
                      <input 
                        type="radio" 
                        name="releaseMode" 
                        className="w-4 h-4 text-custech-primary focus:ring-custech-navy" 
                        checked={resultSettings.releaseMode === 'immediate'}
                        onChange={() => setResultSettings(prev => ({ ...prev, releaseMode: 'immediate' }))}
                      />
                      <div>
                        <div className="font-medium text-heading">Immediate Feedback</div>
                        <div className="text-sm text-muted">Students see their score right after submission.</div>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="bg-light p-6 rounded-xl border border-default">
                  <h4 className="text-lg font-medium text-heading mb-4">Passing Score</h4>
                  <div className="flex items-center gap-4">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={resultSettings.passingScore}
                      onChange={(e) => setResultSettings(prev => ({ ...prev, passingScore: parseInt(e.target.value) || 0 }))}
                      className="w-24 h-11 bg-white border-2 border-input rounded-lg px-3 text-heading"
                    />
                    <span className="text-muted">% minimum to pass</span>
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 p-5 rounded-xl flex items-start gap-4">
                  <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-amber-800">Embargo Policy Active</h4>
                    <p className="text-sm text-amber-700 mt-1">
                      Results may be subject to Senate approval. Immediate feedback can bypass embargo when enabled.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        id="embargo" 
                        className="rounded border-input text-custech-primary focus:ring-custech-navy" 
                        checked={resultSettings.embargoEnabled}
                        onChange={(e) => setResultSettings(prev => ({ ...prev, embargoEnabled: e.target.checked }))}
                      />
                      <label htmlFor="embargo" className="text-sm text-heading select-none cursor-pointer">Enforce Senate Embargo Rules</label>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-default">
                  <button 
                    onClick={handleSaveResultSettings}
                    disabled={isSubmitting || !activeExamId}
                    className="bg-custech-green hover:opacity-90 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-medium transition-all flex items-center gap-2"
                  >
                    {isSubmitting && <Loader2 className="w-5 h-5 animate-spin" />}
                    Finalize Examination Setup
                  </button>
                </div>
                
                {!activeExamId && (
                  <p className="text-amber-700 text-sm text-right">Create an exam first.</p>
                )}
              </div>
            </div>
          )}

            </div>
          </div>
          </>
          )}
        </div>
      </main>
    </div>
  );
};

export default ExamOfficerDashboard;
