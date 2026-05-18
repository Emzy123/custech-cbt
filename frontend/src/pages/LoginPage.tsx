import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeSlash, Student, Shield, Timer } from '@phosphor-icons/react';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { apiRequest } from '../lib/api';

interface LoginFormData {
  matricNumber: string;
  password: string;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<LoginFormData>({
    matricNumber: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  interface LoginResponse {
    access?: string;
    refresh?: string;
    access_token?: string;
    refresh_token?: string;
    user?: Record<string, unknown>;
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (error) setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiRequest<LoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: formData.matricNumber,
          password: formData.password
        }),
      });
      const accessToken = data.access ?? data.access_token;
      const refreshToken = data.refresh ?? data.refresh_token;
      if (!accessToken) {
        throw new Error('Login response did not include an access token.');
      }
      localStorage.setItem('authToken', accessToken);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      if (data.user) {
        localStorage.setItem('authUser', JSON.stringify(data.user));
      }

      // Fetch full profile to get roles
      try {
        const me = await apiRequest<{ roles?: string[]; role?: string }>('/api/v1/auth/me');
        localStorage.setItem('authUser', JSON.stringify({ ...data.user, ...me }));
        
        const roleStr = me.roles && me.roles.length > 0 ? me.roles[0].toLowerCase() : (me.role ? me.role.toLowerCase() : '');
        
        // Navigate based on role
        if (roleStr === 'admin' || roleStr === 'administrator' || roleStr === 'super_admin') {
          navigate('/admin/dashboard', { replace: true });
        } else if (roleStr === 'officer' || roleStr === 'exam_officer') {
          navigate('/officer', { replace: true });
        } else if (roleStr === 'invigilator') {
          navigate('/invigilator/dashboard', { replace: true });
        } else if (roleStr === 'lecturer') {
          navigate('/lecturer/questions', { replace: true });
        } else {
          navigate('/dashboard', { replace: true });
        }
      } catch (e) {
        // Fallback
        navigate('/dashboard', { replace: true });
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-2/5 bg-primary-blue-900 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-32 h-32 border-4 border-white rounded-full"></div>
          <div className="absolute bottom-20 right-20 w-24 h-24 border-4 border-white rounded-lg transform rotate-45"></div>
          <div className="absolute top-1/2 left-1/3 w-16 h-16 border-4 border-white rounded-full"></div>
        </div>
        
        {/* Main content */}
        <div className="relative z-10">
          <div className="text-white mb-8">
            <h1 className="text-3xl font-bold mb-2">CUSTECH</h1>
            <p className="text-lg opacity-90">Confluence University of Science & Technology, Osara</p>
          </div>
          
          <div className="text-white">
            <h2 className="text-4xl font-bold mb-4">GST Examination Portal</h2>
            <p className="text-lg opacity-80 leading-relaxed">
              Secure • Fair • Reliable
            </p>
          </div>
        </div>
        
        {/* Bottom trust indicators */}
        <div className="relative z-10 flex items-center gap-8 text-white text-sm">
          <div className="flex items-center gap-2">
            <Shield size={20} weight="bold" />
            <span>Secure</span>
          </div>
          <div className="flex items-center gap-2">
            <Timer size={20} weight="bold" />
            <span>Fair</span>
          </div>
          <div className="flex items-center gap-2">
            <Student size={20} weight="bold" />
            <span>Reliable</span>
          </div>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="flex-1 bg-surface-grey flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile branding */}
          <div className="lg:hidden text-center mb-8">
            <h1 className="text-2xl font-bold text-primary-blue-800 mb-2">CUSTECH</h1>
            <p className="text-sm text-text-secondary">GST Examination Portal</p>
          </div>

          <Card elevation={1} className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-semibold text-text-primary mb-2">Sign In</h2>
              <p className="text-text-secondary">
                Enter your matric number and password to continue
              </p>
            </div>

            {error && (
              <div 
                className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md"
                role="alert"
              >
                <p className="text-danger text-sm font-medium">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <Input
                id="matric-number"
                name="matricNumber"
                type="text"
                label="Matric Number"
                value={formData.matricNumber}
                onChange={handleInputChange}
                required
                placeholder="e.g., CSC/2024/001"
                autoComplete="username"
                disabled={isLoading}
              />

              <div className="space-y-2">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  label="Password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-9 text-text-secondary hover:text-text-primary focus:outline-none focus:text-text-primary"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeSlash size={20} weight="regular" />
                  ) : (
                    <Eye size={20} weight="regular" />
                  )}
                </button>
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  className="text-sm text-info hover:text-info-dark focus:outline-none focus:underline"
                  onClick={async () => {
                    const email = window.prompt('Enter your registered email address');
                    if (!email) return;
                    try {
                      await apiRequest(`/api/v1/auth/forgot-password?email=${encodeURIComponent(email)}`, {
                        method: 'POST'
                      });
                      setError('Password reset request sent. Check your email.');
                    } catch (err) {
                      setError(err instanceof Error ? err.message : 'Password reset request failed');
                    }
                  }}
                >
                  Forgot Password?
                </button>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                loading={isLoading}
                disabled={!formData.matricNumber || !formData.password}
                className="w-full"
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-surface-grey-dark">
              <p className="text-center text-sm text-text-secondary">
                Need help? Contact the{' '}
                <a 
                  href="mailto:ict@custech.edu.ng" 
                  className="text-info hover:text-info-dark focus:underline"
                >
                  ICT Helpdesk
                </a>
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
