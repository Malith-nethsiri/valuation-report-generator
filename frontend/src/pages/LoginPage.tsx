import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Label } from '../components/Label';

// Validation schema
const loginSchema = z.object({
    email: z.string().email('Please enter a valid email address'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const from = location.state?.from?.pathname || '/dashboard';

    const {
        register,
        handleSubmit,
        formState: { errors, isValid, touchedFields },
        watch,
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
        mode: 'onChange',
    });

    const watchedEmail = watch('email');
    const watchedPassword = watch('password');

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(''), 5000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const onSubmit = async (data: LoginFormData) => {
        setIsLoading(true);
        setError('');

        try {
            await login(data.email, data.password);
            navigate(from, { replace: true });
        } catch (err: any) {
            setError(err.message || 'Login failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center p-4 relative overflow-hidden">
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-gradient-to-br from-violet-400/20 to-purple-600/20 blur-3xl animate-pulse"></div>
                <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-gradient-to-br from-blue-400/20 to-indigo-600/20 blur-3xl animate-pulse delay-1000"></div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-gradient-to-br from-cyan-400/10 to-blue-600/10 blur-3xl animate-spin [animation-duration:20s]"></div>
            </div>

            {/* Main login container */}
            <div className="w-full max-w-md relative">
                {/* Glassmorphism card */}
                <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8 relative overflow-hidden">
                    {/* Card background gradient */}
                    <div className="absolute inset-0 bg-gradient-to-br from-white/50 via-transparent to-purple-500/5 pointer-events-none"></div>

                    {/* Content */}
                    <div className="relative z-10">
                        {/* Header */}
                        <div className="text-center mb-8">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 mb-6 shadow-lg shadow-purple-500/25">
                                <Sparkles className="w-8 h-8 text-white" />
                            </div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-purple-900 to-violet-900 bg-clip-text text-transparent">
                                Welcome Back
                            </h1>
                            <p className="text-gray-600 mt-2">Sign in to continue to your dashboard</p>
                        </div>

                        {/* Error message */}
                        {error && (
                            <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-100 animate-fadeIn">
                                <p className="text-red-600 text-sm text-center font-medium">{error}</p>
                            </div>
                        )}

                        {/* Login form */}
                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                            {/* Email field */}
                            <div className="space-y-2">
                                <Label htmlFor="email" className="text-gray-700 font-medium">
                                    Email Address
                                </Label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                        <Mail className={`h-5 w-5 transition-colors duration-200 ${watchedEmail ? 'text-violet-500' : 'text-gray-400'
                                            }`} />
                                    </div>
                                    <Input
                                        id="email"
                                        type="email"
                                        autoComplete="email"
                                        className={`pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200 ${errors.email ? 'border-red-300 bg-red-50/50' : touchedFields.email && !errors.email ? 'border-green-300 bg-green-50/50' : ''
                                            }`}
                                        placeholder="Enter your email"
                                        {...register('email')}
                                    />
                                    {touchedFields.email && !errors.email && (
                                        <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                        </div>
                                    )}
                                </div>
                                {errors.email && (
                                    <p className="text-red-500 text-sm mt-1 animate-slideDown">{errors.email.message}</p>
                                )}
                            </div>

                            {/* Password field */}
                            <div className="space-y-2">
                                <Label htmlFor="password" className="text-gray-700 font-medium">
                                    Password
                                </Label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                        <Lock className={`h-5 w-5 transition-colors duration-200 ${watchedPassword ? 'text-violet-500' : 'text-gray-400'
                                            }`} />
                                    </div>
                                    <Input
                                        id="password"
                                        type={showPassword ? 'text' : 'password'}
                                        autoComplete="current-password"
                                        className={`pl-12 pr-14 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200 ${errors.password ? 'border-red-300 bg-red-50/50' : touchedFields.password && !errors.password ? 'border-green-300 bg-green-50/50' : ''
                                            }`}
                                        placeholder="Enter your password"
                                        {...register('password')}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors duration-200"
                                    >
                                        {showPassword ? (
                                            <EyeOff className="h-5 w-5" />
                                        ) : (
                                            <Eye className="h-5 w-5" />
                                        )}
                                    </button>
                                </div>
                                {errors.password && (
                                    <p className="text-red-500 text-sm mt-1 animate-slideDown">{errors.password.message}</p>
                                )}
                            </div>

                            {/* Submit button */}
                            <Button
                                type="submit"
                                disabled={!isValid || isLoading}
                                className="w-full h-14 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white font-semibold rounded-2xl shadow-lg shadow-violet-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] group"
                            >
                                {isLoading ? (
                                    <div className="flex items-center justify-center">
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                                        Signing In...
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center">
                                        Sign In
                                        <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-200" />
                                    </div>
                                )}
                            </Button>
                        </form>

                        {/* Forgot password link */}
                        <div className="text-center mt-6">
                            <button className="text-violet-600 hover:text-violet-700 text-sm font-medium transition-colors duration-200">
                                Forgot your password?
                            </button>
                        </div>

                        {/* Sign up link */}
                        <div className="text-center mt-8 pt-6 border-t border-gray-200/50">
                            <p className="text-gray-600 text-sm">
                                Don't have an account?{' '}
                                <Link
                                    to="/register"
                                    className="text-violet-600 hover:text-violet-700 font-semibold transition-colors duration-200 hover:underline"
                                >
                                    Create one now
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>

                {/* Additional decorative elements */}
                <div className="absolute -top-4 -left-4 w-24 h-24 rounded-full bg-gradient-to-br from-violet-400/20 to-purple-600/20 blur-xl"></div>
                <div className="absolute -bottom-4 -right-4 w-32 h-32 rounded-full bg-gradient-to-br from-cyan-400/20 to-blue-600/20 blur-xl"></div>
            </div>
        </div>
    );
};

export default LoginPage;
