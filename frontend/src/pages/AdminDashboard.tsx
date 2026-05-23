import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest, logout } from '../lib/api';
import { Plus, Search, Trash2, Lock, UserPlus, RefreshCw, Shield, Users, Building2, BookOpen, GraduationCap, FileText, Activity, Settings, X, ChevronDown, ChevronRight, LogOut, UserCheck, User } from 'lucide-react';

// --- Interfaces ---
interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;
  gender?: string;
  is_verified: boolean;
  is_active: boolean;
  last_login_at?: string;
  created_at?: string;
  roles: string[];
}

interface Session {
  id: string;
  session_code: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

interface Semester {
  id: string;
  academic_session_id: string;
  semester_type: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

interface Department {
  id: string;
  code: string;
  name: string;
  faculty_code?: string;
}

interface Course {
  id: string;
  code: string;
  title: string;
  description?: string;
  credit_units: number;
  level: number;
  semester_type: string;
}

type TabType = 'overview' | 'users' | 'academics' | 'courses';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState<{ full_name: string; role: string } | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('authUser');
      if (raw) {
        const parsed = JSON.parse(raw);
        setUserProfile({
          full_name: parsed.full_name || parsed.username || 'Administrator',
          role: parsed.role || 'Super Admin'
        });
      }
    } catch (e) {
      // ignore
    }
  }, []);

  const menuItems: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <Activity size={20} /> },
    { id: 'users', label: 'User Management', icon: <Users size={20} /> },
    { id: 'academics', label: 'Academic Structure', icon: <Building2 size={20} /> },
    { id: 'courses', label: 'Courses & Lecturers', icon: <BookOpen size={20} /> },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="flex h-screen bg-light">
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-dark text-white flex flex-col transition-all duration-300`}>
        <div className="p-4 flex items-center justify-between">
          {!sidebarCollapsed && <h1 className="text-xl font-bold tracking-tight">CBT Admin</h1>}
          <button 
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 hover:bg-darker rounded"
          >
            {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
        <nav className="flex-1 mt-4">
          <ul className="space-y-1 px-2">
            {menuItems.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                    activeTab === item.id ? 'bg-custech-primary text-white' : 'text-gray-300 hover:bg-darker hover:text-white'
                  }`}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  {item.icon}
                  {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                </button>
              </li>
            ))}
            <li className="my-4 px-2">
              <div className="h-px bg-darker animate-pulse" />
            </li>
            <li>
              <button
                onClick={() => {
                  localStorage.setItem('adminActiveConsole', 'exam');
                  window.dispatchEvent(new Event('adminConsoleSwitched'));
                }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white font-medium bg-custech-gradient hover:opacity-90 active:scale-[0.98] transition-all shadow-md group relative overflow-hidden"
                title={sidebarCollapsed ? "Switch to Exams" : undefined}
              >
                <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <Shield size={20} className="text-custech-gold" />
                {!sidebarCollapsed && <span className="text-sm font-semibold tracking-wide">Switch to Exams</span>}
              </button>
            </li>
          </ul>
        </nav>
        <div className="p-4 border-t border-darker flex flex-col gap-3">
          {/* User Profile Card */}
          {userProfile && (
            <div className="flex items-center gap-3 p-2 bg-darker rounded-lg border border-darker/50 hover:border-custech-primary/30 transition-all duration-300">
              <div className="w-9 h-9 bg-custech-gradient rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                <User size={18} className="text-custech-gold" />
              </div>
              {!sidebarCollapsed && (
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-white truncate">{userProfile.full_name}</p>
                  <p className="text-[10px] text-gray-400 truncate uppercase tracking-wider">{userProfile.role}</p>
                </div>
              )}
            </div>
          )}

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-custech-gold hover:bg-darker hover:text-white transition-colors"
          >
            <LogOut size={20} />
            {!sidebarCollapsed && <span className="text-sm">Logout</span>}
          </button>
          {!sidebarCollapsed && (
            <div className="text-xs text-muted">
              Admin Panel v1.0
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-light">
        <header className="bg-white border-b border-default px-6 py-4 sticky top-0 z-10">
          <h2 className="text-2xl font-semibold text-heading">
            {menuItems.find(m => m.id === activeTab)?.label || 'Dashboard'}
          </h2>
        </header>

        <main className="p-6">
          {activeTab === 'overview' && <OverviewSection />}
          {activeTab === 'users' && <UsersSection />}
          {activeTab === 'academics' && <AcademicsSection />}
          {activeTab === 'courses' && <CoursesSection />}
        </main>
      </div>
    </div>
  );
}

// --- Users Section ---
function UsersSection() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '', email: '', password: '', first_name: '', last_name: '',
    phone_number: '', gender: 'OTHER', role: 'STUDENT'
  });
  const [roleModal, setRoleModal] = useState<{ show: boolean; user: User | null }>({ show: false, user: null });
  const [newRole, setNewRole] = useState('STUDENT');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<User[]>(`/api/v1/users/?search=${search}&limit=100`);
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, [search]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/v1/users/', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      setShowModal(false);
      setFormData({ username: '', email: '', password: '', first_name: '', last_name: '', phone_number: '', gender: 'OTHER', role: 'STUDENT' });
      fetchUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to create user');
    }
  };

  const handleDelete = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await apiRequest(`/api/v1/users/${userId}`, { method: 'DELETE' });
      fetchUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to delete user');
    }
  };

  const handleToggleActive = async (user: User) => {
    try {
      await apiRequest(`/api/v1/users/${user.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !user.is_active })
      });
      fetchUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to update user');
    }
  };

  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roleModal.user) return;
    try {
      await apiRequest(`/api/v1/users/${roleModal.user.id}/roles`, {
        method: 'POST',
        body: JSON.stringify({ role: newRole })
      });
      setRoleModal({ show: false, user: null });
      fetchUsers();
    } catch (err: any) {
      alert(err.message || 'Failed to assign role');
    }
  };

  const handleResetPassword = async (userId: string) => {
    const newPassword = prompt('Enter new password (min 8 characters):');
    if (!newPassword || newPassword.length < 8) return;
    try {
      await apiRequest(`/api/v1/users/${userId}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ new_password: newPassword })
      });
      alert('Password reset successfully. User must log in again.');
    } catch (err: any) {
      alert(err.message || 'Failed to reset password');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-muted" size={18} />
            <input
              type="text"
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 border border-default rounded-lg focus:ring-2 focus:ring-custech-navy focus:border-custech-navy"
            />
          </div>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-custech-primary text-white px-4 py-2 rounded-lg hover:bg-custech-primary hover:shadow-lg flex items-center gap-2"
        >
          <Plus size={18} /> Add User
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-default overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-muted uppercase bg-light">
            <tr>
              <th className="px-6 py-3">User</th>
              <th className="px-6 py-3">Email</th>
              <th className="px-6 py-3">Roles</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Last Login</th>
              <th className="px-6 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center">Loading...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center text-body">No users found</td></tr>
            ) : (
              users.map((user) => (
                <tr key={user.id} className="border-b hover:bg-light">
                  <td className="px-6 py-4">
                    <div className="font-medium text-heading">{user.full_name}</div>
                    <div className="text-body">@{user.username}</div>
                  </td>
                  <td className="px-6 py-4">{user.email}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map(role => (
                        <span key={role} className="bg-custech-navy bg-opacity-10 text-custech-navy text-xs px-2 py-0.5 rounded">
                          {role}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleToggleActive(user)}
                      className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-custech-green bg-opacity-20 text-custech-green' : 'bg-danger bg-opacity-20 text-danger'}`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </td>
                  <td className="px-6 py-4 text-body">
                    {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setRoleModal({ show: true, user })}
                        className="text-custech-navy hover:text-custech-primary"
                        title="Assign Role"
                      >
                        <Shield size={16} />
                      </button>
                      <button
                        onClick={() => handleResetPassword(user.id)}
                        className="text-custech-navy hover:text-custech-primary"
                        title="Reset Password"
                      >
                        <Lock size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="text-red-600 hover:text-red-800"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create User Modal */}
      {showModal && (
        <Modal title="Create New User" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
              <input
                type="text"
                placeholder="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
              <input
                type="text"
                placeholder="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
              <input
                type="password"
                placeholder="Password (min 8 chars)"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
                minLength={8}
              />
              <input
                type="tel"
                placeholder="Phone Number"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="STUDENT">Student</option>
              <option value="LECTURER">Lecturer</option>
              <option value="EXAM_OFFICER">Exam Officer</option>
              <option value="INVIGILATOR">Invigilator</option>
              <option value="ADMINISTRATOR">Administrator</option>
              <option value="SUPER_ADMIN">Super Admin</option>
            </select>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Create User</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Assign Role Modal */}
      {roleModal.show && roleModal.user && (
        <Modal title={`Assign Role to ${roleModal.user.full_name}`} onClose={() => setRoleModal({ show: false, user: null })}>
          <form onSubmit={handleAssignRole} className="space-y-4">
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="STUDENT">Student</option>
              <option value="LECTURER">Lecturer</option>
              <option value="EXAM_OFFICER">Exam Officer</option>
              <option value="INVIGILATOR">Invigilator</option>
              <option value="ADMINISTRATOR">Administrator</option>
              <option value="SUPER_ADMIN">Super Admin</option>
            </select>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setRoleModal({ show: false, user: null })} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Assign Role</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// --- Overview Section ---
function OverviewSection() {
  const [stats, setStats] = useState({ users: 0, courses: 0, departments: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [users, courses, departments] = await Promise.all([
          apiRequest<unknown[]>('/api/v1/users/?limit=200').catch(() => []),
          apiRequest<unknown[]>('/api/v1/academics/courses').catch(() => []),
          apiRequest<unknown[]>('/api/v1/academics/departments').catch(() => []),
        ]);
        setStats({
          users: Array.isArray(users) ? users.length : 0,
          courses: Array.isArray(courses) ? courses.length : 0,
          departments: Array.isArray(departments) ? departments.length : 0,
        });
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const cards = [
    { label: 'Total Users', value: stats.users, icon: <Users size={24} />, color: 'bg-blue-500' },
    { label: 'Courses', value: stats.courses, icon: <BookOpen size={24} />, color: 'bg-green-500' },
    { label: 'Departments', value: stats.departments, icon: <Building2 size={24} />, color: 'bg-purple-500' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="bg-white p-6 rounded-xl shadow-sm border border-default">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-body">{card.label}</p>
                <p className="text-2xl font-bold mt-1">{loading ? '-' : card.value}</p>
              </div>
              <div className={`${card.color} text-white p-3 rounded-lg`}>{card.icon}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="bg-white p-6 rounded-xl shadow-sm border border-default">
        <h3 className="text-lg font-medium text-heading mb-4">Welcome to CBT Admin Dashboard</h3>
        <p className="text-body">Use the sidebar to navigate through different management sections.</p>
        <ul className="mt-4 space-y-2 text-sm text-body">
          <li>• <strong>User Management:</strong> Create and manage users, assign roles</li>
          <li>• <strong>Academic Structure:</strong> Manage sessions, semesters, departments</li>
          <li>• <strong>Courses:</strong> Add and edit courses, link to departments</li>
        </ul>
      </div>
    </div>
  );
}

// --- Academics Section ---
function AcademicsSection() {
  const [activeSubTab, setActiveSubTab] = useState<'sessions' | 'semesters' | 'departments'>('sessions');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchData(); }, [activeSubTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeSubTab === 'sessions') {
        const data = await apiRequest<Session[]>('/api/v1/academics/sessions');
        setSessions(data);
      } else if (activeSubTab === 'semesters') {
        const data = await apiRequest<Semester[]>('/api/v1/academics/semesters');
        setSemesters(data);
      } else {
        const data = await apiRequest<Department[]>('/api/v1/academics/departments');
        setDepartments(data);
      }
    } catch (err) {
      console.error('Failed to load data', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2 bg-white p-1 rounded-lg border border-gray-200 w-fit">
        {(['sessions', 'semesters', 'departments'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveSubTab(tab)}
            className={`px-4 py-2 rounded-md text-sm capitalize ${
              activeSubTab === tab ? 'bg-indigo-600 text-white' : 'text-body hover:bg-gray-100'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeSubTab === 'sessions' && (
        <SessionsTable sessions={sessions} loading={loading} onRefresh={fetchData} />
      )}
      {activeSubTab === 'semesters' && (
        <SemestersTable semesters={semesters} loading={loading} onRefresh={fetchData} />
      )}
      {activeSubTab === 'departments' && (
        <DepartmentsTable departments={departments} loading={loading} onRefresh={fetchData} />
      )}
    </div>
  );
}

function SessionsTable({ sessions, loading, onRefresh }: { sessions: Session[]; loading: boolean; onRefresh: () => void }) {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ session_code: '', start_date: '', end_date: '', is_current: false });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/v1/academics/sessions', {
        method: 'POST',
        body: JSON.stringify({
          ...formData,
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString()
        })
      });
      setShowModal(false);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to create session');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowModal(true)} className="bg-custech-primary text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus size={18} /> Add Session
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-default overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-light">
            <tr><th className="px-6 py-3">Session Code</th><th className="px-6 py-3">Start Date</th><th className="px-6 py-3">End Date</th><th className="px-6 py-3">Status</th></tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={4} className="px-6 py-4 text-center">Loading...</td></tr> :
              sessions.length === 0 ? <tr><td colSpan={4} className="px-6 py-4 text-center text-body">No sessions found</td></tr> :
              sessions.map(s => (
                <tr key={s.id} className="border-b">
                  <td className="px-6 py-4 font-medium">{s.session_code}</td>
                  <td className="px-6 py-4">{new Date(s.start_date).toLocaleDateString()}</td>
                  <td className="px-6 py-4">{new Date(s.end_date).toLocaleDateString()}</td>
                  <td className="px-6 py-4">
                    {s.is_current ? <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Current</span> : <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">Inactive</span>}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      {showModal && (
        <Modal title="Create Academic Session" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <input placeholder="Session Code (e.g., 2025/2026)" value={formData.session_code} onChange={e => setFormData({...formData, session_code: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
            <div className="grid grid-cols-2 gap-4">
              <input type="date" value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
              <input type="date" value={formData.end_date} onChange={e => setFormData({...formData, end_date: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={formData.is_current} onChange={e => setFormData({...formData, is_current: e.target.checked})} />
              <span>Set as current session</span>
            </label>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Create</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function SemestersTable({ semesters, loading, onRefresh }: { semesters: Semester[]; loading: boolean; onRefresh: () => void }) {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ academic_session_id: '', semester_type: 'FIRST', start_date: '', end_date: '', is_current: false });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/v1/academics/semesters', {
        method: 'POST',
        body: JSON.stringify({
          ...formData,
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString()
        })
      });
      setShowModal(false);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to create semester');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowModal(true)} className="bg-custech-primary text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus size={18} /> Add Semester
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-default overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-light">
            <tr><th className="px-6 py-3">Semester</th><th className="px-6 py-3">Session ID</th><th className="px-6 py-3">Start Date</th><th className="px-6 py-3">End Date</th><th className="px-6 py-3">Status</th></tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={5} className="px-6 py-4 text-center">Loading...</td></tr> :
              semesters.length === 0 ? <tr><td colSpan={5} className="px-6 py-4 text-center text-body">No semesters found</td></tr> :
              semesters.map(s => (
                <tr key={s.id} className="border-b">
                  <td className="px-6 py-4 font-medium">{s.semester_type}</td>
                  <td className="px-6 py-4 text-body">{s.academic_session_id.slice(0, 8)}...</td>
                  <td className="px-6 py-4">{new Date(s.start_date).toLocaleDateString()}</td>
                  <td className="px-6 py-4">{new Date(s.end_date).toLocaleDateString()}</td>
                  <td className="px-6 py-4">
                    {s.is_current ? <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">Current</span> : <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs">Inactive</span>}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      {showModal && (
        <Modal title="Create Semester" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <input placeholder="Academic Session ID" value={formData.academic_session_id} onChange={e => setFormData({...formData, academic_session_id: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
            <select value={formData.semester_type} onChange={e => setFormData({...formData, semester_type: e.target.value})} className="w-full px-3 py-2 border rounded-lg">
              <option value="FIRST">First Semester</option>
              <option value="SECOND">Second Semester</option>
            </select>
            <div className="grid grid-cols-2 gap-4">
              <input type="date" value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
              <input type="date" value={formData.end_date} onChange={e => setFormData({...formData, end_date: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={formData.is_current} onChange={e => setFormData({...formData, is_current: e.target.checked})} />
              <span>Set as current semester</span>
            </label>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Create</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function DepartmentsTable({ departments, loading, onRefresh }: { departments: Department[]; loading: boolean; onRefresh: () => void }) {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ code: '', name: '', faculty_code: '' });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/v1/academics/departments', { method: 'POST', body: JSON.stringify(formData) });
      setShowModal(false);
      setFormData({ code: '', name: '', faculty_code: '' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to create department');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowModal(true)} className="bg-custech-primary text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus size={18} /> Add Department
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-default overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-light">
            <tr><th className="px-6 py-3">Code</th><th className="px-6 py-3">Name</th><th className="px-6 py-3">Faculty</th></tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={3} className="px-6 py-4 text-center">Loading...</td></tr> :
              departments.length === 0 ? <tr><td colSpan={3} className="px-6 py-4 text-center text-body">No departments found</td></tr> :
              departments.map(d => (
                <tr key={d.id} className="border-b">
                  <td className="px-6 py-4 font-medium">{d.code}</td>
                  <td className="px-6 py-4">{d.name}</td>
                  <td className="px-6 py-4">{d.faculty_code || '-'}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      {showModal && (
        <Modal title="Create Department" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <input placeholder="Department Code (e.g., CSC)" value={formData.code} onChange={e => setFormData({...formData, code: e.target.value})} className="w-full px-3 py-2 border rounded-lg uppercase" required maxLength={10} />
            <input placeholder="Department Name (e.g., Computer Science)" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
            <input placeholder="Faculty Code (optional)" value={formData.faculty_code} onChange={e => setFormData({...formData, faculty_code: e.target.value})} className="w-full px-3 py-2 border rounded-lg" />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Create</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// --- Courses Section ---
interface LecturerAssignment {
  assignment_id: string;
  lecturer_id: string;
  course_id: string;
  full_name: string;
  email: string;
  username: string;
}

function CoursesSection() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [assignModal, setAssignModal] = useState<{ show: boolean; course: Course | null }>({ show: false, course: null });
  const [formData, setFormData] = useState({ code: '', title: '', description: '', credit_units: 3, level: 100, semester_type: 'FIRST' });
  const [lecturers, setLecturers] = useState<User[]>([]);
  const [courseAssignments, setCourseAssignments] = useState<LecturerAssignment[]>([]);
  const [selectedLecturerId, setSelectedLecturerId] = useState('');
  const [assignLoading, setAssignLoading] = useState(false);

  useEffect(() => { fetchCourses(); fetchLecturers(); }, []);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<Course[]>('/api/v1/academics/courses');
      setCourses(data);
    } catch (err) {
      console.error('Failed to load courses', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLecturers = async () => {
    try {
      const data = await apiRequest<User[]>('/api/v1/users/?role=LECTURER&limit=200');
      setLecturers(data);
    } catch (err) {
      console.error('Failed to load lecturers', err);
    }
  };

  const openAssignModal = async (course: Course) => {
    setAssignModal({ show: true, course });
    setSelectedLecturerId('');
    setAssignLoading(true);
    try {
      const data = await apiRequest<LecturerAssignment[]>(`/api/v1/academics/courses/${course.id}/lecturers`);
      setCourseAssignments(data);
    } catch (err) {
      setCourseAssignments([]);
    } finally {
      setAssignLoading(false);
    }
  };

  const handleAssignLecturer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignModal.course || !selectedLecturerId) return;
    try {
      await apiRequest(`/api/v1/academics/courses/${assignModal.course.id}/lecturers`, {
        method: 'POST',
        body: JSON.stringify({ lecturer_id: selectedLecturerId })
      });
      const data = await apiRequest<LecturerAssignment[]>(`/api/v1/academics/courses/${assignModal.course.id}/lecturers`);
      setCourseAssignments(data);
      setSelectedLecturerId('');
    } catch (err: any) {
      alert(err.message || 'Failed to assign lecturer');
    }
  };

  const handleUnassignLecturer = async (courseId: string, lecturerId: string) => {
    if (!confirm('Remove this lecturer from the course?')) return;
    try {
      await apiRequest(`/api/v1/academics/courses/${courseId}/lecturers/${lecturerId}`, { method: 'DELETE' });
      setCourseAssignments(prev => prev.filter(a => a.lecturer_id !== lecturerId));
    } catch (err: any) {
      alert(err.message || 'Failed to remove lecturer');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/api/v1/academics/courses', {
        method: 'POST',
        body: JSON.stringify({ ...formData, level: Number(formData.level), credit_units: Number(formData.credit_units) })
      });
      setShowModal(false);
      setFormData({ code: '', title: '', description: '', credit_units: 3, level: 100, semester_type: 'FIRST' });
      fetchCourses();
    } catch (err: any) {
      alert(err.message || 'Failed to create course');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowModal(true)} className="bg-custech-primary text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus size={18} /> Add Course
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-default overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-light">
            <tr><th className="px-6 py-3">Code</th><th className="px-6 py-3">Title</th><th className="px-6 py-3">Credits</th><th className="px-6 py-3">Level</th><th className="px-6 py-3">Semester</th><th className="px-6 py-3">Actions</th></tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={6} className="px-6 py-4 text-center">Loading...</td></tr> :
              courses.length === 0 ? <tr><td colSpan={6} className="px-6 py-4 text-center text-body">No courses found</td></tr> :
              courses.map(c => (
                <tr key={c.id} className="border-b">
                  <td className="px-6 py-4 font-medium">{c.code}</td>
                  <td className="px-6 py-4">{c.title}</td>
                  <td className="px-6 py-4">{c.credit_units}</td>
                  <td className="px-6 py-4">{c.level}L</td>
                  <td className="px-6 py-4"><span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">{c.semester_type}</span></td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => openAssignModal(c)}
                      className="flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs"
                      title="Assign Lecturer"
                    >
                      <UserCheck size={16} /> Assign Lecturer
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Create Course Modal */}
      {showModal && (
        <Modal title="Create Course" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input placeholder="Course Code" value={formData.code} onChange={e => setFormData({...formData, code: e.target.value})} className="w-full px-3 py-2 border rounded-lg uppercase" required />
              <input placeholder="Credits" type="number" min={1} max={6} value={formData.credit_units} onChange={e => setFormData({...formData, credit_units: Number(e.target.value)})} className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <input placeholder="Course Title" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full px-3 py-2 border rounded-lg" required />
            <textarea placeholder="Description (optional)" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} className="w-full px-3 py-2 border rounded-lg" rows={3} />
            <div className="grid grid-cols-2 gap-4">
              <select value={formData.level} onChange={e => setFormData({...formData, level: Number(e.target.value)})} className="w-full px-3 py-2 border rounded-lg">
                <option value={100}>100 Level</option>
                <option value={200}>200 Level</option>
                <option value={300}>300 Level</option>
                <option value={400}>400 Level</option>
                <option value={500}>500 Level</option>
              </select>
              <select value={formData.semester_type} onChange={e => setFormData({...formData, semester_type: e.target.value})} className="w-full px-3 py-2 border rounded-lg">
                <option value="FIRST">First Semester</option>
                <option value="SECOND">Second Semester</option>
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg">Create</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Assign Lecturer Modal */}
      {assignModal.show && assignModal.course && (
        <Modal title={`Assign Lecturer — ${assignModal.course.code}: ${assignModal.course.title}`} onClose={() => setAssignModal({ show: false, course: null })}>
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-700">Currently Assigned Lecturers</h4>
            {assignLoading ? (
              <p className="text-sm text-body">Loading...</p>
            ) : courseAssignments.length === 0 ? (
              <p className="text-sm text-body">No lecturers assigned yet.</p>
            ) : (
              <div className="space-y-2">
                {courseAssignments.map(a => (
                  <div key={a.assignment_id} className="flex items-center justify-between bg-light px-3 py-2 rounded-lg">
                    <div>
                      <p className="text-sm font-medium">{a.full_name}</p>
                      <p className="text-xs text-body">{a.email}</p>
                    </div>
                    <button
                      onClick={() => handleUnassignLecturer(assignModal.course!.id, a.lecturer_id)}
                      className="text-red-500 hover:text-red-700"
                      title="Remove"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <hr />
            <form onSubmit={handleAssignLecturer} className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">Add Lecturer</label>
              <select
                value={selectedLecturerId}
                onChange={e => setSelectedLecturerId(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg text-sm"
                required
              >
                <option value="">— Select a lecturer —</option>
                {lecturers
                  .filter(l => !courseAssignments.some(a => a.lecturer_id === l.id))
                  .map(l => (
                    <option key={l.id} value={l.id}>{l.full_name} ({l.email})</option>
                  ))}
              </select>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setAssignModal({ show: false, course: null })} className="px-4 py-2 border rounded-lg text-sm">Close</button>
                <button type="submit" disabled={!selectedLecturerId} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm disabled:bg-indigo-400">Assign</button>
              </div>
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
}

// --- Modal Component ---
function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-body"><X size={20} /></button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
