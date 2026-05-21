import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import StudentDashboard from './pages/StudentDashboard';
import ExaminationInterface from './pages/ExaminationInterface';
import LecturerQuestionBank from './pages/LecturerQuestionBank';
import LecturerDashboard from './pages/LecturerDashboard';
import ImplementationRoadmap from './pages/ImplementationRoadmap';
import AdminDashboard from './pages/AdminDashboard';
import ExamOfficerDashboard from './pages/ExamOfficerDashboard';
import StudentResultsReview from './pages/StudentResultsReview';
import { getAuthToken } from './lib/api';
import './index.css';

// ── Auth helpers ──────────────────────────────────────────────────────────────

function getStoredRole(): string {
  try {
    const raw = localStorage.getItem('authUser');
    if (!raw) return '';
    const user = JSON.parse(raw) as { role?: string; roles?: string[] };
    if (user.role) return user.role.toLowerCase();
    if (Array.isArray(user.roles) && user.roles.length > 0) return user.roles[0].toLowerCase();
  } catch {
    // ignore parse errors
  }
  return '';
}

function getStoredUsername(): string {
  try {
    const raw = localStorage.getItem('authUser');
    if (!raw) return '';
    const user = JSON.parse(raw) as { username?: string };
    return user.username || '';
  } catch {
    // ignore parse errors
  }
  return '';
}

/** Destination route for each role after login. */
function roleHomeRoute(role: string): string {
  switch (role) {
    case 'admin': case 'administrator': case 'super_admin': case 'officer': case 'exam_officer': return '/admin/dashboard';
    case 'lecturer': return '/lecturer/dashboard';
    default: return '/dashboard'; // student
  }
}

// ── Route guards ──────────────────────────────────────────────────────────────

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = Boolean(getAuthToken());
  if (!isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
};

/** Guard that also enforces role. Redirects to role home if wrong role. */
const RoleRoute: React.FC<{ allowed: string[]; children: React.ReactNode }> = ({ allowed, children }) => {
  const isAuthenticated = Boolean(getAuthToken());
  if (!isAuthenticated) return <Navigate to="/" replace />;
  const role = getStoredRole();
  if (allowed.length > 0 && !allowed.includes(role)) {
    return <Navigate to={roleHomeRoute(role)} replace />;
  }
  return <>{children}</>;
};

const AdminOrOfficerDashboard: React.FC = () => {
  const username = getStoredUsername();
  if (username === 'examofficer') {
    return <ExamOfficerDashboard />;
  }
  return <AdminDashboard />;
};

// ── App ───────────────────────────────────────────────────────────────────────

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Public */}
        <Route path="/" element={<LoginPage />} />

        {/* Student */}
        <Route
          path="/dashboard"
          element={
            <RoleRoute allowed={['student', '']}>
              <StudentDashboard />
            </RoleRoute>
          }
        />
        <Route
          path="/exam/:examId"
          element={
            <ProtectedRoute>
              <ExaminationInterface />
            </ProtectedRoute>
          }
        />
        <Route
          path="/exam/:examId/instances/:instanceId/review"
          element={
            <ProtectedRoute>
              <StudentResultsReview />
            </ProtectedRoute>
          }
        />

        {/* Lecturer */}
        <Route
          path="/lecturer/dashboard"
          element={
            <RoleRoute allowed={['lecturer', 'admin', 'administrator', 'super_admin']}>
              <LecturerDashboard />
            </RoleRoute>
          }
        />
        <Route
          path="/lecturer/questions"
          element={
            <RoleRoute allowed={['lecturer', 'admin', 'administrator', 'super_admin']}>
              <LecturerQuestionBank />
            </RoleRoute>
          }
        />

        {/* Admin / Exam Officer */}
        <Route
          path="/admin/dashboard"
          element={
            <RoleRoute allowed={['admin', 'administrator', 'super_admin', 'officer', 'exam_officer']}>
              <AdminOrOfficerDashboard />
            </RoleRoute>
          }
        />

        {/* Internal */}
        <Route
          path="/implementation-roadmap"
          element={
            <ProtectedRoute>
              <ImplementationRoadmap />
            </ProtectedRoute>
          }
        />

        {/* Catch-all: redirect to role home or login */}
        <Route
          path="*"
          element={
            getAuthToken()
              ? <Navigate to={roleHomeRoute(getStoredRole())} replace />
              : <Navigate to="/" replace />
          }
        />
      </Routes>
    </div>
  );
}

export default App;
