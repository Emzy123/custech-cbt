import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Settings, Calendar, Users, MapPin, FileText, CheckCircle, AlertTriangle, 
  Printer, Download, Loader2, Plus, Trash2, GraduationCap, Bell, Clock,
  LayoutDashboard, BookOpen, BarChart3, ChevronRight, User, LogOut,
  ClipboardList, School, FileCheck, TrendingUp, Activity, MoreHorizontal
} from 'lucide-react';
import { apiRequest, logout } from '../lib/api';

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

const ExamOfficerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'wizard' | 'blueprint' | 'venue' | 'slips' | 'results'>('wizard');
  const [activeExamId, setActiveExamId] = useState<string>(localStorage.getItem('activeExamId') || '');

  // Data states
  const [courses, setCourses] = useState<Course[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
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

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [coursesData, venuesData, examsData] = await Promise.all([
          apiRequest<Course[]>('/api/v1/academics/courses'),
          apiRequest<Venue[]>('/api/v1/venues'),
          apiRequest<Exam[]>('/api/v1/examinations'),
        ]);
        setCourses(coursesData);
        setVenues(venuesData);
        setExams(examsData);

        // If there's an active exam, load its details
        if (activeExamId) {
          await loadExamDetails(activeExamId);
        }
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
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

    setIsSubmitting(true);
    try {
      const response = await apiRequest<{ id: string }>('/api/v1/examinations', {
        method: 'POST',
        body: JSON.stringify({
          title: examForm.title,
          course_id: examForm.course_id,
          exam_date: examForm.date,
          start_time: `${examForm.time}:00`,
          duration_minutes: parseInt(examForm.duration),
        }),
      });

      setActiveExamId(response.id);
      localStorage.setItem('activeExamId', response.id);
      
      // Refresh exams list
      const updatedExams = await apiRequest<Exam[]>('/api/v1/examinations');
      setExams(updatedExams);
      
      alert('Exam created successfully!');
      setActiveTab('blueprint');
    } catch (error) {
      alert('Failed to create exam. Please try again.');
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
      await apiRequest(`/api/v1/examinations/${activeExamId}/blueprint`, {
        method: 'PUT',
        body: JSON.stringify({
          total_questions: blueprintConfig.totalQuestions,
          topics: blueprintConfig.topics,
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
      await apiRequest(`/api/v1/examinations/${activeExamId}/venues`, {
        method: 'POST',
        body: JSON.stringify({
          venue_ids: selectedVenues,
        }),
      });

      // Run allocation algorithm
      await apiRequest(`/api/v1/examinations/${activeExamId}/allocate`, {
        method: 'POST',
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
      await apiRequest(`/api/v1/examinations/${activeExamId}/settings`, {
        method: 'PUT',
        body: JSON.stringify({
          result_release_mode: resultSettings.releaseMode,
          embargo_enabled: resultSettings.embargoEnabled,
          release_date: resultSettings.releaseDate || null,
          passing_score: resultSettings.passingScore,
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      {/* Professional Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col fixed h-full">
        {/* Logo */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <School size={24} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-white leading-tight">Custech</h1>
              <p className="text-xs text-slate-400">Exam Management</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
          <div className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Examination
          </div>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.id === 'slips' && activeExamId && (
                <span className="ml-auto w-2 h-2 bg-emerald-400 rounded-full"></span>
              )}
            </button>
          ))}

          <div className="px-3 mt-8 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Resources
          </div>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-all text-sm font-medium">
            <BookOpen size={20} />
            <span>Courses</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-all text-sm font-medium">
            <MapPin size={20} />
            <span>Venues</span>
            <span className="ml-auto text-xs text-slate-500">{venues.length}</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-all text-sm font-medium">
            <Users size={20} />
            <span>Students</span>
          </button>

          <div className="px-3 mt-8 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Quick Stats
          </div>
          <div className="px-3 py-2 space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Active Exams</span>
              <span className="font-semibold text-emerald-400">{stats.active}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Scheduled</span>
              <span className="font-semibold text-blue-400">{stats.scheduled}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Capacity</span>
              <span className="font-semibold text-slate-200">{stats.totalCapacity.toLocaleString()}</span>
            </div>
          </div>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center">
              <User size={20} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">Exam Officer</p>
              <p className="text-xs text-slate-400">Administrator</p>
            </div>
            <button 
              onClick={async () => { await logout(); navigate('/', { replace: true }); }}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 min-h-screen">
        {/* Top Header */}
        <header className="bg-slate-900/50 backdrop-blur-md border-b border-slate-800 sticky top-0 z-30">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h2 className="text-2xl font-bold text-white">
                {tabs.find(t => t.id === activeTab)?.label}
              </h2>
              <p className="text-sm text-slate-400 mt-0.5">
                {activeTab === 'wizard' && 'Create and schedule examinations'}
                {activeTab === 'blueprint' && 'Configure question distribution'}
                {activeTab === 'venue' && 'Allocate examination venues'}
                {activeTab === 'slips' && 'Generate and distribute exam slips'}
                {activeTab === 'results' && 'Configure result release settings'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
                <Bell size={20} />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg text-sm text-slate-400">
                <Clock size={14} />
                <span>{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="p-8">
          {/* Stats Overview - Show on all tabs */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">Total Exams</p>
                  <p className="text-3xl font-bold text-white mt-1">{stats.totalExams}</p>
                </div>
                <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center">
                  <ClipboardList size={24} className="text-indigo-400" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm">
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <TrendingUp size={14} />
                  {stats.scheduled}
                </span>
                <span className="text-slate-500">scheduled</span>
              </div>
            </div>

            <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">Active Now</p>
                  <p className="text-3xl font-bold text-white mt-1">{stats.active}</p>
                </div>
                <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                  <Activity size={24} className="text-emerald-400" />
                </div>
              </div>
              <div className="mt-4">
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div 
                    className="bg-emerald-500 h-2 rounded-full transition-all" 
                    style={{ width: `${stats.totalExams ? (stats.active / stats.totalExams) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">Total Venues</p>
                  <p className="text-3xl font-bold text-white mt-1">{stats.totalVenues}</p>
                </div>
                <div className="w-12 h-12 bg-amber-500/20 rounded-xl flex items-center justify-center">
                  <MapPin size={24} className="text-amber-400" />
                </div>
              </div>
              <div className="mt-4 text-sm text-slate-500">
                {stats.totalCapacity.toLocaleString()} total seats
              </div>
            </div>

            <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">Completed</p>
                  <p className="text-3xl font-bold text-white mt-1">{stats.completed}</p>
                </div>
                <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center">
                  <FileCheck size={24} className="text-purple-400" />
                </div>
              </div>
              <div className="mt-4 text-sm text-slate-500">
                Exams finished this session
              </div>
            </div>
          </div>

          {/* Tab Content */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            {/* Navigation Tabs */}
            <div className="flex space-x-1 bg-slate-800/50 p-1 rounded-xl mb-6 overflow-x-auto">
              {tabs.map((tab) => (
                <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content Areas */}
        <div className="bg-gray-800/40 border border-gray-700/50 backdrop-blur-xl rounded-2xl p-6 shadow-2xl transition-all">
          
          {/* Exam Wizard */}
          {activeTab === 'wizard' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <h2 className="text-2xl font-semibold">Schedule Examination</h2>
                <span className="px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-sm font-medium border border-indigo-500/30">
                  Step 1 of 5
                </span>
              </div>
              
              {/* Active Exam Selector */}
              {exams.length > 0 && (
                <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700">
                  <label className="block text-sm font-medium text-gray-400 mb-2">Continue with existing exam</label>
                  <select 
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 outline-none transition-all text-white"
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
                  <label className="block text-sm font-medium text-gray-400 mb-2">Examination Title *</label>
                  <input 
                    type="text" 
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-600" 
                    placeholder="e.g. GST 101 Mid-Semester Exam" 
                    value={examForm.title}
                    onChange={(e) => setExamForm(prev => ({ ...prev, title: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Course *</label>
                  <select 
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white"
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
                  <label className="block text-sm font-medium text-gray-400 mb-2">Date *</label>
                  <input 
                    type="date" 
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white" 
                    value={examForm.date}
                    onChange={(e) => setExamForm(prev => ({ ...prev, date: e.target.value }))}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Start Time *</label>
                    <input 
                      type="time" 
                      className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white" 
                      value={examForm.time}
                      onChange={(e) => setExamForm(prev => ({ ...prev, time: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Duration (min) *</label>
                    <input 
                      type="number" 
                      className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white" 
                      placeholder="120" 
                      value={examForm.duration}
                      onChange={(e) => setExamForm(prev => ({ ...prev, duration: e.target.value }))}
                    />
                  </div>
                </div>
              </div>
              <div className="flex justify-end pt-4">
                <button 
                  onClick={handleCreateExam}
                  disabled={isSubmitting}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-8 py-3 rounded-xl font-medium transition-all shadow-lg shadow-indigo-500/20 active:scale-95 flex items-center gap-2"
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
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <h2 className="text-2xl font-semibold">Question Blueprint</h2>
                <span className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm font-medium border border-purple-500/30">
                  Step 2 of 5
                </span>
              </div>
              <div className="bg-gray-900/50 rounded-xl p-6 border border-gray-700">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-medium text-gray-300">Topic Distribution</h3>
                  <div className="flex items-center gap-4">
                    <div className="text-sm font-medium text-gray-400">
                      Total Questions
                    </div>
                    <input 
                      type="number" 
                      value={blueprintConfig.totalQuestions}
                      onChange={(e) => setBlueprintConfig(prev => ({ ...prev, totalQuestions: parseInt(e.target.value) || 0 }))}
                      className="w-20 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-center text-sm text-white"
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
                        className="w-1/3 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600"
                      />
                      <div className="flex-1 bg-gray-800 h-4 rounded-full overflow-hidden border border-gray-700">
                        <div 
                          className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full transition-all" 
                          style={{ width: `${topic.percentage}%` }}
                        ></div>
                      </div>
                      <div className="w-32 flex gap-2 items-center">
                        <input 
                          type="number" 
                          value={topic.percentage}
                          onChange={(e) => handleTopicChange(i, 'percentage', parseInt(e.target.value) || 0)}
                          className="w-16 bg-gray-900 border border-gray-700 rounded-lg px-2 py-1 text-center text-sm text-white" 
                        />
                        <span className="text-xs text-gray-500">%</span>
                        <button
                          onClick={() => removeTopic(i)}
                          className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                          title="Remove topic"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-8 flex justify-between items-center">
                  <button 
                    onClick={addTopic}
                    className="bg-gray-800 hover:bg-gray-700 border border-gray-600 text-white px-4 py-2 rounded-xl transition-all flex items-center gap-2"
                  >
                    <Plus size={16} />
                    Add Topic
                  </button>
                  <button 
                    onClick={handleSaveBlueprint}
                    disabled={isSubmitting || !activeExamId}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-6 py-2 rounded-xl transition-all flex items-center gap-2"
                  >
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    Save Blueprint & Continue
                  </button>
                </div>
                
                {!activeExamId && (
                  <p className="text-amber-400 text-sm mt-4">Please create an exam in Step 1 first.</p>
                )}
              </div>
            </div>
          )}

          {/* Venue Allocation */}
          {activeTab === 'venue' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <h2 className="text-2xl font-semibold">Venue Allocation</h2>
                <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm font-medium border border-blue-500/30">
                  Step 3 of 5
                </span>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="col-span-2 bg-gray-900/50 rounded-xl border border-gray-700 overflow-hidden">
                  <div className="p-4 border-b border-gray-700 bg-gray-800/50 flex justify-between items-center">
                    <h3 className="font-medium">Available Venues</h3>
                    <span className="text-xs font-semibold bg-gray-700 px-2 py-1 rounded text-gray-300">
                      Selected: {selectedVenues.length} venues
                    </span>
                  </div>
                  <table className="w-full text-sm text-left text-gray-400">
                    <thead className="bg-gray-800/30 text-gray-300 uppercase">
                      <tr>
                        <th className="px-6 py-3">Select</th>
                        <th className="px-6 py-3">Venue</th>
                        <th className="px-6 py-3">Capacity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {venues.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                            No venues available. Please add venues in the Admin dashboard.
                          </td>
                        </tr>
                      ) : (
                        venues.map((venue) => (
                          <tr 
                            key={venue.id} 
                            className={`border-b border-gray-700/50 ${selectedVenues.includes(venue.id) ? 'bg-indigo-500/10' : 'bg-gray-800/10'}`}
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
                                className="w-4 h-4 rounded border-gray-600 text-indigo-500 focus:ring-indigo-500"
                              />
                            </td>
                            <td className="px-6 py-4 font-medium text-white">{venue.name}</td>
                            <td className="px-6 py-4">{venue.capacity} seats</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="bg-gray-900/50 rounded-xl border border-gray-700 p-6 flex flex-col justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-white mb-4">Allocation Summary</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Registered Students:</span>
                        <span className="font-bold text-white">{registeredStudents || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Selected Capacity:</span>
                        <span className="font-bold text-white">
                          {venues
                            .filter(v => selectedVenues.includes(v.id))
                            .reduce((sum, v) => sum + v.capacity, 0)} seats
                        </span>
                      </div>
                      <div className="w-full bg-gray-800 h-2 rounded-full mt-4">
                        <div 
                          className="bg-blue-500 h-full rounded-full transition-all" 
                          style={{ 
                            width: registeredStudents 
                              ? `${Math.min(100, (venues.filter(v => selectedVenues.includes(v.id)).reduce((sum, v) => sum + v.capacity, 0) / registeredStudents) * 100)}%` 
                              : '0%' 
                          }}
                        ></div>
                      </div>
                      <div className="text-xs text-right text-gray-500 mt-1">
                        {selectedVenues.length} venues selected
                      </div>
                    </div>
                  </div>
                  
                  {!activeExamId && (
                    <p className="text-amber-400 text-sm mt-4">Create an exam first.</p>
                  )}
                  
                  {venueStatus === 'pending' ? (
                    <button 
                      onClick={handleAllocateVenues}
                      disabled={allocating || selectedVenues.length === 0 || !activeExamId}
                      className="w-full mt-8 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-3 rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20 active:scale-95 flex justify-center items-center gap-2"
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
                    <div className="mt-8 bg-green-500/20 border border-green-500/30 text-green-400 p-4 rounded-xl flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-medium">Allocation Complete</h4>
                        <p className="text-sm mt-1 text-green-400/80">Successfully assigned 782 students to 3 venues with unique exam numbers.</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Exam Slips */}
          {activeTab === 'slips' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <h2 className="text-2xl font-semibold">Exam Slips & Documents</h2>
                <span className="px-3 py-1 bg-green-500/20 text-green-300 rounded-full text-sm font-medium border border-green-500/30">
                  Step 4 of 5
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-2xl p-6 group hover:border-indigo-500/50 transition-all">
                  <div className="w-12 h-12 bg-indigo-500/20 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Printer className="w-6 h-6 text-indigo-400" />
                  </div>
                  <h3 className="text-xl font-medium text-white mb-2">Bulk Slip Generation</h3>
                  <p className="text-gray-400 text-sm mb-6">Generate a consolidated PDF containing exam slips for all 782 allocated students. Optimized for double-sided printing.</p>
                  <button
                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-3 rounded-xl font-medium transition-all shadow-lg flex justify-center items-center gap-2"
                    onClick={() => activeExamId && downloadFile(`${API_BASE}/examinations/${activeExamId}/slips`, `exam_slips_${activeExamId}.pdf`)}
                    disabled={!activeExamId}
                  >
                    <Download className="w-5 h-5" />
                    Download All Slips (PDF)
                  </button>
                </div>
                
                <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-2xl p-6 group hover:border-purple-500/50 transition-all">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Users className="w-6 h-6 text-purple-400" />
                  </div>
                  <h3 className="text-xl font-medium text-white mb-2">Attendance Register</h3>
                  <p className="text-gray-400 text-sm mb-6">Generate venue-specific attendance sheets with student photos, seat allocations, and signature columns.</p>
                  <button
                    className="w-full bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl font-medium transition-all shadow-lg flex justify-center items-center gap-2"
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
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between border-b border-gray-700 pb-4">
                <h2 className="text-2xl font-semibold">Post-Exam & Result Settings</h2>
                <span className="px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-sm font-medium border border-amber-500/30">
                  Step 5 of 5
                </span>
              </div>
              
              <div className="max-w-2xl space-y-6">
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-700">
                  <h3 className="text-lg font-medium mb-4">Result Release Mode</h3>
                  <div className="space-y-3">
                    <label className="flex items-center gap-3 p-3 border border-gray-700 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                      <input 
                        type="radio" 
                        name="releaseMode" 
                        className="w-4 h-4 text-indigo-500 focus:ring-indigo-500 bg-gray-900 border-gray-600" 
                        checked={resultSettings.releaseMode === 'manual'}
                        onChange={() => setResultSettings(prev => ({ ...prev, releaseMode: 'manual' }))}
                      />
                      <div>
                        <div className="font-medium text-white">Manual Release</div>
                        <div className="text-sm text-gray-400">Exam Officer must explicitly trigger result publication.</div>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 p-3 border border-gray-700 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                      <input 
                        type="radio" 
                        name="releaseMode" 
                        className="w-4 h-4 text-indigo-500 focus:ring-indigo-500 bg-gray-900 border-gray-600" 
                        checked={resultSettings.releaseMode === 'automatic'}
                        onChange={() => setResultSettings(prev => ({ ...prev, releaseMode: 'automatic' }))}
                      />
                      <div>
                        <div className="font-medium text-white">Automatic Release</div>
                        <div className="text-sm text-gray-400">Results are automatically published at a scheduled time.</div>
                      </div>
                      {resultSettings.releaseMode === 'automatic' && (
                        <input
                          type="datetime-local"
                          value={resultSettings.releaseDate}
                          onChange={(e) => setResultSettings(prev => ({ ...prev, releaseDate: e.target.value }))}
                          className="ml-4 bg-gray-900 border border-gray-600 rounded px-3 py-1 text-sm text-white"
                        />
                      )}
                    </label>
                    <label className="flex items-center gap-3 p-3 border border-gray-700 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                      <input 
                        type="radio" 
                        name="releaseMode" 
                        className="w-4 h-4 text-indigo-500 focus:ring-indigo-500 bg-gray-900 border-gray-600" 
                        checked={resultSettings.releaseMode === 'immediate'}
                        onChange={() => setResultSettings(prev => ({ ...prev, releaseMode: 'immediate' }))}
                      />
                      <div>
                        <div className="font-medium text-white">Immediate Feedback</div>
                        <div className="text-sm text-gray-400">Students see their score immediately upon submission.</div>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-700">
                  <h3 className="text-lg font-medium mb-4">Passing Score</h3>
                  <div className="flex items-center gap-4">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={resultSettings.passingScore}
                      onChange={(e) => setResultSettings(prev => ({ ...prev, passingScore: parseInt(e.target.value) || 0 }))}
                      className="w-24 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white"
                    />
                    <span className="text-gray-400">% minimum to pass</span>
                  </div>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/30 p-5 rounded-xl flex items-start gap-4">
                  <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-amber-500">Embargo Policy Active</h4>
                    <p className="text-sm text-amber-500/80 mt-1">
                      Results for this examination are subject to Senate approval. Enabling immediate feedback will bypass this embargo.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        id="embargo" 
                        className="rounded bg-gray-900 border-gray-600 text-amber-500 focus:ring-amber-500" 
                        checked={resultSettings.embargoEnabled}
                        onChange={(e) => setResultSettings(prev => ({ ...prev, embargoEnabled: e.target.checked }))}
                      />
                      <label htmlFor="embargo" className="text-sm text-gray-300 select-none cursor-pointer">Enforce Senate Embargo Rules</label>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <button 
                    onClick={handleSaveResultSettings}
                    disabled={isSubmitting || !activeExamId}
                    className="bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white px-8 py-3 rounded-xl font-medium transition-all shadow-lg shadow-green-500/20 active:scale-95 flex items-center gap-2"
                  >
                    {isSubmitting && <Loader2 className="w-5 h-5 animate-spin" />}
                    Finalize Examination Setup
                  </button>
                </div>
                
                {!activeExamId && (
                  <p className="text-amber-400 text-sm text-right">Create an exam first.</p>
                )}
              </div>
            </div>
          )}

        </div>
        </div>
      </div>
      </main>
    </div>
  );
};

export default ExamOfficerDashboard;
