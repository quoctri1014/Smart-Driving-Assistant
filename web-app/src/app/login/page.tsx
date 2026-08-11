'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../stores/authStore';
import { authService } from '../../services/authService';
import { Button } from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Car } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('driver1@example.com');
  const [password, setPassword] = useState('password');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authService.login(email, password);
      const user = authService.getCurrentUser();
      if (user) {
        login(user);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-adas-bg flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-2xl bg-adas-primary flex items-center justify-center text-white">
            <Car className="w-10 h-10" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-adas-text-primary">
          Smart ADAS
        </h2>
        <p className="mt-2 text-center text-sm text-adas-text-secondary">
          Advanced Driver Assistance System
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card variant="glass">
          <CardContent className="px-4 py-8 sm:px-10">
            <form className="space-y-6" onSubmit={handleSubmit}>
              {error && (
                <div className="bg-adas-danger/10 border border-adas-danger/20 text-adas-danger p-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-adas-text-primary">
                  Email address
                </label>
                <div className="mt-1">
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-adas-border rounded-lg bg-adas-surface text-adas-text-primary focus:outline-none focus:ring-2 focus:ring-adas-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-adas-text-primary">
                  Password
                </label>
                <div className="mt-1">
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-adas-border rounded-lg bg-adas-surface text-adas-text-primary focus:outline-none focus:ring-2 focus:ring-adas-primary"
                  />
                </div>
              </div>

              <div>
                <Button type="submit" className="w-full" isLoading={loading}>
                  Sign in
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
