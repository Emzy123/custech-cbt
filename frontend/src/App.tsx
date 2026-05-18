import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import StudentDashboard from './pages/StudentDashboard';
import ExaminationInterface from './pages/ExaminationInterface';
import LecturerQuestionBank from './pages/LecturerQuestionBank';
import InvigilatorDashboard from './pages/InvigilatorDashboard';
import ImplementationRoadmap from './pages/ImplementationRoadmap';
import AdminDashboard from './pages/AdminDashboard';
import ExamOfficerDashboard from './pages/ExamOfficerDashboard';
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

/** Destination route for each role after login. */
function roleHomeRoute(role: string): string {
  switch (role) {
    case 'admin': case 'administrator': case 'super_admin': return '/admin/dashboard';
    case 'officer': case 'exam_officer': return '/officer';
    case 'invigilator': return '/invigilator/dashboard';
    case 'lecturer': return '/lecturer/questions';
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

        {/* Lecturer */}
        <Route
          path="/lecturer/questions"
          element={
            <RoleRoute allowed={['lecturer', 'admin', 'administrator', 'super_admin']}>
              <LecturerQuestionBank />
            </RoleRoute>
          }
        />

        {/* Invigilator */}
        <Route
          path="/invigilator/dashboard"
          element={
            <RoleRoute allowed={['invigilator', 'admin', 'administrator', 'super_admin']}>
              <InvigilatorDashboard />
            </RoleRoute>
          }
        />

        {/* Exam Officer */}
        <Route
          path="/officer"
          element={
            <RoleRoute allowed={['officer', 'exam_officer', 'admin', 'administrator', 'super_admin']}>
              <ExamOfficerDashboard />
            </RoleRoute>
          }
        />

        {/* Admin */}
        <Route
          path="/admin/dashboard"
          element={
            <RoleRoute allowed={['admin', 'administrator', 'super_admin']}>
              <AdminDashboard />
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
