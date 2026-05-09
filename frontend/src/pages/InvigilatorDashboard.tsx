import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Warning, 
  CheckCircle, 
  XCircle,
  Eye,
  Pause,
  Play,
  Stop,
  ChatCircle,
  ChartLine,
  Clock,
  MapPin,
  Camera,
  User
} from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Timer from '../components/ui/Timer';

interface Student {
  id: string;
  name: string;
  matricNumber: string;
  courseCode: string;
  photo?: string;
  progress: {
    answered: number;
    total: number;
  };
  status: 'normal' | 'warning' | 'critical';
  statusMessage: string;
  lastActive: Date;
  proctoringEvents: ProctoringEvent[];
}

interface ProctoringEvent {
  id: string;
  timestamp: Date;
  type: 'focus_lost' | 'multiple_faces' | 'left_screen' | 'suspicious_movement';
  confidence: number;
  snapshot?: string;
  description: string;
}

interface Alert {
  id: string;
  studentId: string;
  studentName: string;
  event: ProctoringEvent;
  timestamp: Date;
}

const InvigilatorDashboard: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [showAlertsPanel, setShowAlertsPanel] = useState(true);
  const [stats, setStats] = useState({
    totalActive: 0,
    flagged: 0,
    incidents: 0,
    completed: 0
  });
  const [loading, setLoading] = useState(true);

  // Mock data - replace with actual WebSocket/API calls
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // TODO: Replace with actual API calls
        // const response = await fetch('/api/v1/invigilator/dashboard');
        // const data = await response.json();
        
        const mockStudents: Student[] = [
          {
            id: '1',
            name: 'Chiamaka Okafor',
            matricNumber: 'MIC/2024/023',
            courseCode: 'GST 111',
            progress: { answered: 34, total: 60 },
            status: 'normal',
            statusMessage: 'Normal',
            lastActive: new Date(),
            proctoringEvents: []
          },
          {
            id: '2',
            name: 'Ahmed Ibrahim',
            matricNumber: 'CSC/2024/015',
            courseCode: 'GST 111',
            progress: { answered: 28, total: 60 },
            status: 'warning',
            statusMessage: 'Multiple faces detected',
            lastActive: new Date(Date.now() - 30000),
            proctoringEvents: [
              {
                id: 'e1',
                timestamp: new Date(Date.now() - 30000),
                type: 'multiple_faces',
                confidence: 87,
                description: 'Multiple faces detected (87% confidence)'
              }
            ]
          },
          {
            id: '3',
            name: 'Fatima Adamu',
            matricNumber: 'BCH/2024/008',
            courseCode: 'GST 111',
            progress: { answered: 45, total: 60 },
            status: 'critical',
            statusMessage: 'Left screen 3 times',
            lastActive: new Date(Date.now() - 120000),
            proctoringEvents: [
              {
                id: 'e2',
                timestamp: new Date(Date.now() - 120000),
                type: 'left_screen',
                confidence: 92,
                description: 'Student left examination area'
              },
              {
                id: 'e3',
                timestamp: new Date(Date.now() - 180000),
                type: 'left_screen',
                confidence: 88,
                description: 'Student left examination area'
              },
              {
                id: 'e4',
                timestamp: new Date(Date.now() - 240000),
                type: 'left_screen',
                confidence: 95,
                description: 'Student left examination area'
              }
            ]
          },
          {
            id: '4',
            name: 'David Chuks',
            matricNumber: 'PHY/2024/012',
            courseCode: 'GST 111',
            progress: { answered: 52, total: 60 },
            status: 'normal',
            statusMessage: 'Normal',
            lastActive: new Date(),
            proctoringEvents: []
          }
        ];
        
        const mockAlerts: Alert[] = [
          {
            id: 'a1',
            studentId: '2',
            studentName: 'Ahmed Ibrahim',
            event: mockStudents[1].proctoringEvents[0],
            timestamp: new Date(Date.now() - 30000)
          },
          {
            id: 'a2',
            studentId: '3',
            studentName: 'Fatima Adamu',
            event: mockStudents[2].proctoringEvents[0],
            timestamp: new Date(Date.now() - 120000)
          }
        ];
        
        setStudents(mockStudents);
        setAlerts(mockAlerts);
        
        // Calculate stats
        const newStats = {
          totalActive: mockStudents.length,
          flagged: mockStudents.filter(s => s.status === 'warning').length,
          incidents: mockStudents.filter(s => s.status === 'critical').length,
          completed: 0 // Would be calculated from actual exam completion data
        };
        
        setStats(newStats);
        
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();

    // Set up WebSocket for real-time updates
    // TODO: Implement WebSocket connection
    const wsInterval = setInterval(() => {
      // Simulate real-time updates
      console.log('Checking for updates...');
    }, 5000);

    return () => clearInterval(wsInterval);
  }, []);

  const handleStudentAction = async (studentId: string, action: 'message' | 'pause' | 'terminate') => {
    try {
      // TODO: Implement actual student action API calls
      console.log(`Action ${action} for student ${studentId}`);
      
      // Update local state optimistically
      if (action === 'terminate') {
        setStudents(prev => prev.filter(s => s.id !== studentId));
        setAlerts(prev => prev.filter(a => a.studentId !== studentId));
      }
    } catch (error) {
      console.error('Failed to perform student action:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'status-dot green';
      case 'warning': return 'status-dot amber';
      case 'critical': return 'status-dot red';
      default: return 'status-dot green';
    }
  };

  const getStatusBgColor = (status: string) => {
    switch (status) {
      case 'normal': return 'bg-green-50 border-green-200';
      case 'warning': return 'bg-amber-50 border-amber-200';
      case 'critical': return 'bg-red-50 border-red-200';
      default: return 'bg-green-50 border-green-200';
    }
  };

  const getStatusTextColor = (status: string) => {
    switch (status) {
      case 'normal': return 'text-success';
      case 'warning': return 'text-warning';
      case 'critical': return 'text-danger';
      default: return 'text-success';
    }
  };

  // Sort students by status (critical first, then warning, then normal)
  const sortedStudents = [...students].sort((a, b) => {
    const statusOrder = { critical: 0, warning: 1, normal: 2 };
    return statusOrder[a.status] - statusOrder[b.status];
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-grey flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-blue-800 mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading monitoring dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-grey">
      {/* Header */}
      <header className="bg-surface-white shadow-elevation-1 h-16 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <ChartLine size={24} weight="bold" className="text-primary-blue-800" />
          <h1 className="text-xl font-semibold text-text-primary">
            Live Examination Monitoring
          </h1>
        </div>
        
        <div className="flex items-center gap-3">
          <Button
            variant="tertiary"
            size="sm"
            onClick={() => setShowAlertsPanel(!showAlertsPanel)}
          >
            <Warning size={16} weight="bold" className="mr-2" />
            Alerts ({alerts.length})
          </Button>
          <div className="text-sm text-text-secondary">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-surface-white border-b border-surface-grey-dark px-6 py-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card elevation={0} className="p-4 text-center">
            <div className="text-2xl font-bold text-primary-blue-800">{stats.totalActive}</div>
            <div className="text-sm text-text-secondary">Total Active Students</div>
          </Card>
          <Card elevation={0} className="p-4 text-center">
            <div className="text-2xl font-bold text-warning">{stats.flagged}</div>
            <div className="text-sm text-text-secondary">Students Flagged</div>
          </Card>
          <Card elevation={0} className="p-4 text-center">
            <div className="text-2xl font-bold text-danger">{stats.incidents}</div>
            <div className="text-sm text-text-secondary">Confirmed Incidents</div>
          </Card>
          <Card elevation={0} className="p-4 text-center">
            <div className="text-2xl font-bold text-success">{stats.completed}</div>
            <div className="text-sm text-text-secondary">Exams Completed</div>
          </Card>
        </div>
      </div>

      {/* Main Content */}
      <main className="container-fluid py-6">
        <div className="flex gap-6">
          {/* Student Grid */}
          <div className={`flex-1 ${showAlertsPanel ? 'lg:mr-80' : ''}`}>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {sortedStudents.map((student) => (
                <Card 
                  key={student.id} 
                  elevation={1} 
                  className={`p-4 border-2 cursor-pointer transition-all duration-150 hover:shadow-elevation-2 ${getStatusBgColor(student.status)}`}
                  onClick={() => setSelectedStudent(student)}
                >
                  <div className="flex items-start gap-3">
                    {/* Student Photo */}
                    <div className="flex-shrink-0">
                      {student.photo ? (
                        <img 
                          src={student.photo} 
                          alt={student.name}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-12 h-12 bg-primary-blue-100 rounded-full flex items-center justify-center">
                          <User size={20} weight="bold" className="text-primary-blue-800" />
                        </div>
                      )}
                    </div>
                    
                    {/* Student Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-text-primary truncate">
                        {student.name}
                      </h3>
                      <p className="text-sm text-text-secondary">
                        {student.matricNumber}
                      </p>
                      <p className="text-sm text-text-secondary">
                        {student.courseCode}
                      </p>
                    </div>
                    
                    {/* Status Indicator */}
                    <div className="flex flex-col items-center gap-1">
                      <div className={getStatusColor(student.status)}></div>
                      <span className={`text-xs font-medium ${getStatusTextColor(student.status)}`}>
                        {student.status}
                      </span>
                    </div>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-text-secondary">Progress</span>
                      <span className="text-text-primary font-medium">
                        {student.progress.answered}/{student.progress.total}
                      </span>
                    </div>
                    <div className="w-full bg-surface-grey-dark rounded-full h-2">
                      <div 
                        className="bg-primary-blue-800 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${(student.progress.answered / student.progress.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  {/* Status Message */}
                  <div className="mt-3 flex items-center gap-2">
                    <span className={`text-sm ${getStatusTextColor(student.status)}`}>
                      {student.statusMessage}
                    </span>
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="mt-3 flex gap-2">
                    <Button
                      variant="tertiary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStudentAction(student.id, 'message');
                      }}
                    >
                      <ChatCircle size={14} weight="bold" />
                    </Button>
                    <Button
                      variant="tertiary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStudentAction(student.id, 'pause');
                      }}
                    >
                      <Pause size={14} weight="bold" />
                    </Button>
                    <Button
                      variant="tertiary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStudentAction(student.id, 'terminate');
                      }}
                      className="text-danger hover:text-red-700"
                    >
                      <Stop size={14} weight="bold" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
            
            {students.length === 0 && (
              <Card elevation={1} className="p-12 text-center">
                <Users size={48} weight="duotone" className="text-text-disabled mx-auto mb-4" />
                <h3 className="text-lg font-medium text-text-primary mb-2">
                  No active examinations
                </h3>
                <p className="text-text-secondary">
                  Student monitoring data will appear here when examinations are in progress.
                </p>
              </Card>
            )}
          </div>

          {/* Alerts Panel */}
          {showAlertsPanel && (
            <aside className="hidden lg:block w-80">
              <Card elevation={2} className="h-fit sticky top-6">
                <div className="p-4 border-b border-surface-grey-dark">
                  <h2 className="font-semibold text-text-primary flex items-center gap-2">
                    <Warning size={20} weight="bold" className="text-warning" />
                    Live Alerts
                  </h2>
                </div>
                
                <div className="max-h-96 overflow-y-auto">
                  {alerts.length > 0 ? (
                    <div className="divide-y divide-surface-grey-dark">
                      {alerts.map((alert) => (
                        <div 
                          key={alert.id}
                          className="p-4 hover:bg-surface-grey cursor-pointer transition-colors duration-150"
                          onClick={() => {
                            const student = students.find(s => s.id === alert.studentId);
                            if (student) setSelectedStudent(student);
                          }}
                        >
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 mt-1">
                              <div className={`status-dot ${alert.event.type === 'multiple_faces' ? 'amber' : 'red'}`}></div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-text-primary">
                                {alert.studentName}
                              </p>
                              <p className="text-xs text-text-secondary mt-1">
                                {alert.event.description}
                              </p>
                              <p className="text-xs text-text-secondary mt-1">
                                {new Date(alert.timestamp).toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center">
                      <CheckCircle size={48} weight="duotone" className="text-success mx-auto mb-4" />
                      <h3 className="text-sm font-medium text-text-primary mb-2">
                        No alerts
                      </h3>
                      <p className="text-xs text-text-secondary">
                        All students are proceeding normally
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </aside>
          )}
        </div>
      </main>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card elevation={3} className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-text-primary">
                  Student Details
                </h3>
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={() => setSelectedStudent(null)}
                >
                  ×
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Student Info */}
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    {selectedStudent.photo ? (
                      <img 
                        src={selectedStudent.photo} 
                        alt={selectedStudent.name}
                        className="w-16 h-16 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-16 h-16 bg-primary-blue-100 rounded-full flex items-center justify-center">
                        <User size={24} weight="bold" className="text-primary-blue-800" />
                      </div>
                    )}
                    <div>
                      <h4 className="font-semibold text-text-primary">
                        {selectedStudent.name}
                      </h4>
                      <p className="text-sm text-text-secondary">
                        {selectedStudent.matricNumber}
                      </p>
                      <p className="text-sm text-text-secondary">
                        {selectedStudent.courseCode}
                      </p>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-text-secondary">Status:</span>
                      <span className={`badge badge-${selectedStudent.status === 'normal' ? 'success' : selectedStudent.status === 'warning' ? 'warning' : 'danger'}`}>
                        {selectedStudent.statusMessage}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 mb-2">
                      <Clock size={16} weight="regular" className="text-text-secondary" />
                      <span className="text-sm text-text-secondary">
                        Last active: {selectedStudent.lastActive.toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium text-text-secondary mb-2">Progress</div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Questions Answered</span>
                      <span className="font-medium">
                        {selectedStudent.progress.answered}/{selectedStudent.progress.total}
                      </span>
                    </div>
                    <div className="w-full bg-surface-grey-dark rounded-full h-2">
                      <div 
                        className="bg-primary-blue-800 h-2 rounded-full"
                        style={{ width: `${(selectedStudent.progress.answered / selectedStudent.progress.total) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                
                {/* Proctoring Events */}
                <div>
                  <h5 className="font-medium text-text-primary mb-3">Proctoring Events</h5>
                  {selectedStudent.proctoringEvents.length > 0 ? (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {selectedStudent.proctoringEvents.map((event) => (
                        <div key={event.id} className="p-3 bg-surface-grey rounded">
                          <div className="flex items-center gap-2 mb-1">
                            <Camera size={14} weight="bold" className="text-text-secondary" />
                            <span className="text-sm font-medium text-text-primary">
                              {event.type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className="text-xs text-text-secondary">
                              ({event.confidence}% confidence)
                            </span>
                          </div>
                          <p className="text-xs text-text-secondary mb-1">
                            {event.description}
                          </p>
                          <p className="text-xs text-text-secondary">
                            {event.timestamp.toLocaleTimeString()}
                          </p>
                          {event.snapshot && (
                            <div className="mt-2">
                              <img 
                                src={event.snapshot} 
                                alt="Proctoring snapshot"
                                className="w-full h-20 object-cover rounded border border-surface-grey-dark"
                              />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle size={32} weight="duotone" className="text-success mx-auto mb-2" />
                      <p className="text-sm text-text-secondary">
                        No proctoring events recorded
                      </p>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Actions */}
              <div className="mt-6 flex gap-3 justify-end">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleStudentAction(selectedStudent.id, 'message')}
                >
                  <ChatCircle size={16} weight="bold" className="mr-2" />
                  Send Message
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleStudentAction(selectedStudent.id, 'pause')}
                >
                  <Pause size={16} weight="bold" className="mr-2" />
                  Pause Exam
                </Button>
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={() => handleStudentAction(selectedStudent.id, 'terminate')}
                  className="border-danger text-danger hover:bg-red-50"
                >
                  <Stop size={16} weight="bold" className="mr-2" />
                  Terminate Exam
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default InvigilatorDashboard;
