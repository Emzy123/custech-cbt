import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Question,
  ChartBar,
  Student,
  SignOut,
  BookOpen,
  User,
  Calendar,
  Clock
} from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Timer from '../components/ui/Timer';
import { apiRequest, logout } from '../lib/api';

interface Exam {
  id: string;
  courseCode: string;
  courseTitle: string;
  date: string;
  time: string;
  venue: string;
  duration: number; // in minutes
  isWithin24Hours?: boolean;
}

interface Result {
  id: string;
  courseCode: string;
  courseTitle: string;
  score: number | null;
  grade: string | null;
  dateTaken: string;
  maxScore: number;
  status: 'released' | 'embargoed';
  message: string | null;
}

interface ResultApi {
  instance_id: string;
  exam_id: string;
  exam_title: string;
  course_id: string;
  status: 'released' | 'embargoed';
  submitted_at: string | null;
  score: number | null;
  max_score?: number;
  grade: string | null;
  percentage: number | null;
  message: string | null;
}

interface ExaminationApi {
  id: string;
  title: string;
  course_id: string;
  exam_date: string;
  start_time: string;
  duration_minutes: number;
}

const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  
  const [nextExam, setNextExam] = useState<Exam | null>(null);
  const [upcomingExams, setUpcomingExams] = useState<Exam[]>([]);
  const [recentResults, setRecentResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);

  const [studentName, setStudentName] = useState('Student');
  const [matricNumber, setMatricNumber] = useState('');

  useEffect(() => {
    // Update current time every minute
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const storedUserRaw = localStorage.getItem('authUser');
        if (storedUserRaw) {
          const storedUser = JSON.parse(storedUserRaw) as { first_name?: string; last_name?: string; username?: string };
          const fullName = `${storedUser.first_name || ''} ${storedUser.last_name || ''}`.trim();
          setStudentName(fullName || storedUser.username || 'Student');
          setMatricNumber(storedUser.username || '');
        }

        const exams = await apiRequest<ExaminationApi[]>('/api/v1/examinations?limit=10');
        const now = new Date();
        const mapped: Exam[] = exams.map((exam) => {
          const startAt = new Date(exam.start_time);
          const examDate = exam.exam_date || startAt.toISOString().slice(0, 10);
          const examTime = startAt.toTimeString().slice(0, 5);
          const examDateTime = new Date(`${examDate}T${examTime}`);
          const diffMs = examDateTime.getTime() - now.getTime();
          const within24h = diffMs > 0 && diffMs <= 24 * 60 * 60 * 1000;
          return {
            id: exam.id,
            courseCode: exam.course_id || '',
            courseTitle: exam.title,
            date: examDate,
            time: examTime,
            venue: 'TBA',
            duration: exam.duration_minutes,
            isWithin24Hours: within24h,
          };
        });

        const upcoming = mapped.filter((exam) => new Date(`${exam.date}T${exam.time}`) > now);
        setNextExam(upcoming.length > 0 ? upcoming[0] : null);
        setUpcomingExams(upcoming.slice(0, 5));

        // Fetch real results (embargo-aware)
        try {
          const rawResults = await apiRequest<ResultApi[]>('/api/v1/examinations/my/results');
          const mappedResults: Result[] = rawResults.map((r) => ({
            id: r.instance_id,
            courseCode: r.course_id || '',
            courseTitle: r.exam_title,
            score: r.score,
            grade: r.grade,
            dateTaken: r.submitted_at || new Date().toISOString(),
            maxScore: r.max_score ?? 100,
            status: r.status,
            message: r.message,
          }));
          setRecentResults(mappedResults.slice(0, 6));
        } catch {
          setRecentResults([]);
        }
      } catch (error) {
        setNextExam(null);
        setUpcomingExams([]);
        setRecentResults([]);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const getTimeUntilExam = (examDate: string, examTime: string): string => {
    const examDateTime = new Date(`${examDate}T${examTime}`);
    const now = new Date();
    const diff = examDateTime.getTime() - now.getTime();
    
    if (diff <= 0) return 'Started';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days} day${days > 1 ? 's' : ''}`;
    }
    
    return `${hours}h ${minutes}m`;
  };

  const getScoreColor = (score: number, maxScore: number): string => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 70) return 'text-success';
    if (percentage >= 50) return 'text-warning';
    return 'text-danger';
  };

  const handleSignOut = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-grey flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-blue-800 mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-grey">
      {/* Skip to main content for accessibility */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>

      {/* Top Navigation */}
      <header className="bg-surface-white shadow-elevation-1 h-16 flex items-center px-6 relative z-10">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-blue-800 rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">CU</span>
            </div>
            <span className="text-primary-blue-800 font-semibold hidden sm:block">
              CUSTECH Exam Portal
            </span>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-4">
          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 p-2 rounded-md hover:bg-surface-grey transition-colors duration-150"
              aria-expanded={userMenuOpen}
              aria-haspopup="true"
            >
              <div className="w-8 h-8 bg-primary-blue-100 rounded-full flex items-center justify-center">
                <User size={16} weight="bold" className="text-primary-blue-800" />
              </div>
              <span className="text-sm font-medium text-text-primary hidden md:block">
                {studentName}
              </span>
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-surface-white rounded-md shadow-elevation-2 py-2 z-50">
                <a
                  href="#"
                  className="flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-surface-grey transition-colors duration-150"
                >
                  <User size={16} weight="regular" />
                  My Profile
                </a>
                <a
                  href="#"
                  className="flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-surface-grey transition-colors duration-150"
                >
                  <Question size={16} weight="regular" />
                  Help
                </a>
                <hr className="my-2 border-surface-grey-dark" />
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-surface-grey transition-colors duration-150 w-full text-left"
                >
                  <SignOut size={16} weight="regular" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main id="main-content" className="container-fluid py-8">
        {/* Welcome Banner */}
        <div className="mb-8">
          <h1 className="text-3xl font-semibold text-text-primary mb-2">
            Welcome back, {studentName.split(' ')[0]}
          </h1>
          <p className="text-text-secondary">
            Here's your examination overview for this semester.
          </p>
        </div>

        {/* Next Exam Card */}
        {nextExam && nextExam.isWithin24Hours && (
          <Card elevation={2} className="mb-8 border-l-4 border-info">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar size={20} weight="bold" className="text-info" />
                  <span className="text-sm font-medium text-info">Next Exam</span>
                </div>
                <h3 className="text-xl font-semibold text-text-primary mb-1">
                  {nextExam.courseCode} – {nextExam.courseTitle}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div className="flex items-center gap-2">
                    <Clock size={16} weight="regular" className="text-text-secondary" />
                    <span className="text-sm text-text-secondary">
                      {new Date(nextExam.date).toLocaleDateString('en-NG', { 
                        weekday: 'short', 
                        month: 'short', 
                        day: 'numeric' 
                      })}, {nextExam.time}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <BookOpen size={16} weight="regular" className="text-text-secondary" />
                    <span className="text-sm text-text-secondary">{nextExam.venue}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Timer timeRemaining={nextExam.duration * 60} />
                    <span className="text-sm text-text-secondary">Duration</span>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-center gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-blue-800">
                    {getTimeUntilExam(nextExam.date, nextExam.time)}
                  </div>
                  <div className="text-sm text-text-secondary">until exam starts</div>
                </div>
                <Button variant="primary" size="md" onClick={() => navigate(`/exam/${nextExam.id}`)}>
                  Start Exam
                </Button>
              </div>
            </div>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Results */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-semibold text-text-primary mb-4 flex items-center gap-2">
              <ChartBar size={20} weight="bold" />
              Recent Results
            </h2>
            
            {recentResults.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recentResults.map((result) => (
                  <Card key={result.id} elevation={1} className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold text-text-primary">
                          {result.courseCode}
                        </h3>
                        <p className="text-sm text-text-secondary line-clamp-1">
                          {result.courseTitle}
                        </p>
                      </div>
                      {result.status === 'released' ? (
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${getScoreColor(result.score ?? 0, result.maxScore)}`}>
                            {result.score}
                          </div>
                          <div className="text-sm text-text-secondary">/ {result.maxScore}</div>
                        </div>
                      ) : (
                        <span className="badge badge-warning text-xs">Embargoed</span>
                      )}
                    </div>
                    
                    {result.status === 'released' ? (
                      <div className="flex justify-between items-center">
                        <span className={`badge badge-${result.grade === 'A' ? 'success' : result.grade === 'B' ? 'warning' : 'info'}`}>
                          Grade: {result.grade}
                        </span>
                        <span className="text-xs text-text-secondary">
                          {new Date(result.dateTaken).toLocaleDateString('en-NG', {
                            month: 'short',
                            day: 'numeric'
                          })}
                        </span>
                      </div>
                    ) : (
                      <p className="text-xs text-text-secondary mt-2">{result.message}</p>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <Card elevation={1} className="p-8 text-center">
                <ChartBar size={48} weight="duotone" className="text-text-disabled mx-auto mb-4" />
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  No results yet
                </h3>
                <p className="text-text-secondary">
                  Your examination results will appear here once available.
                </p>
              </Card>
            )}
          </div>

          {/* Upcoming Exams */}
          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-4 flex items-center gap-2">
              <Calendar size={20} weight="bold" />
              Upcoming Exams
            </h2>
            
            {upcomingExams.length > 0 ? (
              <div className="space-y-3">
                {upcomingExams.map((exam) => (
                  <Card
                    key={exam.id}
                    elevation={1}
                    className="p-4 cursor-pointer hover:shadow-elevation-2 transition-shadow duration-150"
                    onClick={() => navigate(`/exam/${exam.id}`)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold text-text-primary">
                          {exam.courseCode}
                        </h3>
                        <p className="text-sm text-text-secondary line-clamp-1">
                          {exam.courseTitle}
                        </p>
                      </div>
                    </div>
                    
                    <div className="space-y-1 text-sm text-text-secondary">
                      <div className="flex items-center gap-2">
                        <Calendar size={14} weight="regular" />
                        <span>
                          {new Date(exam.date).toLocaleDateString('en-NG', { 
                            weekday: 'short', 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock size={14} weight="regular" />
                        <span>{exam.time} • {exam.venue}</span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card elevation={1} className="p-8 text-center">
                <Calendar size={48} weight="duotone" className="text-text-disabled mx-auto mb-4" />
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  No upcoming exams
                </h3>
                <p className="text-text-secondary">
                  Your examination schedule will appear here once published.
                </p>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default StudentDashboard;
