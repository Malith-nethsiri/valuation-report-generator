import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Eye, EyeOff, Mail, Lock, User, Phone, ArrowRight,
  Shield, Check, X, AlertCircle, Sparkles, UserPlus
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Label } from '../components/Label';

// Password strength checker
const getPasswordStrength = (password: string) => {
  let score = 0;
  const checks = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    numbers: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  score = Object.values(checks).filter(Boolean).length;

  const strength = score <= 2 ? 'weak' : score <= 3 ? 'medium' : score <= 4 ? 'strong' : 'excellent';
  return { score, checks, strength };
};

// Validation schema
const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/\d/, 'Password must contain at least one number')
    .regex(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/, 'Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)'),
  confirmPassword: z.string().min(1, 'Please confirm your password'),
  fullName: z
    .string()
    .min(2, 'Full name must be at least 2 characters')
    .max(100, 'Full name must be less than 100 characters'),
  phone: z.string().optional(),
  termsAccepted: z.boolean().refine((val) => val === true, {
    message: 'You must accept the terms and conditions',
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

const RegisterPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentStep, setCurrentStep] = useState(1);

  const { register: registerUser } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isValid, touchedFields },
    watch,
    trigger,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: 'onChange',
    defaultValues: {
      termsAccepted: false,
    },
  });

  const watchedPassword = watch('password');
  const watchedEmail = watch('email');
  const watchedFullName = watch('fullName');
  const watchedPhone = watch('phone');
  const watchedConfirmPassword = watch('confirmPassword');

  const passwordStrength = watchedPassword ? getPasswordStrength(watchedPassword) : null;

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError('');

    try {
      await registerUser(data.email, data.password, data.fullName, data.phone);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStepValidation = async (step: number) => {
    let fieldsToValidate: Array<keyof RegisterFormData> = [];

    switch (step) {
      case 1:
        fieldsToValidate = ['fullName', 'email'];
        break;
      case 2:
        fieldsToValidate = ['password', 'confirmPassword'];

        // Additional check: ensure password meets all criteria
        if (watchedPassword) {
          const strength = getPasswordStrength(watchedPassword);
          const allCriteriaMet = Object.values(strength.checks).every(Boolean);

          if (!allCriteriaMet) {
            toast.error('Please ensure your password meets all requirements', {
              duration: 4000,
              icon: '🔒'
            });
            return; // Prevent advancement
          }
        }
        break;
      case 3:
        fieldsToValidate = ['termsAccepted'];
        break;
    }

    const isStepValid = await trigger(fieldsToValidate);
    if (isStepValid && step < 3) {
      setCurrentStep(step + 1);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-gradient-to-br from-emerald-400/20 to-green-600/20 blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-gradient-to-br from-blue-400/20 to-indigo-600/20 blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/3 left-1/3 w-64 h-64 rounded-full bg-gradient-to-br from-purple-400/10 to-pink-600/10 blur-3xl animate-spin [animation-duration:25s]"></div>
      </div>

      {/* Main register container */}
      <div className="w-full max-w-md relative">
        {/* Progress indicator */}
        <div className="mb-8 bg-white/60 backdrop-blur-sm rounded-2xl p-4 shadow-lg border border-white/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Step {currentStep} of 3</span>
            <span className="text-sm text-gray-500">{Math.round((currentStep / 3) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="h-2 bg-gradient-to-r from-emerald-500 to-green-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${(currentStep / 3) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Glassmorphism card */}
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8 relative overflow-hidden">
          {/* Card background gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/50 via-transparent to-emerald-500/5 pointer-events-none"></div>

          {/* Content */}
          <div className="relative z-10">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 mb-6 shadow-lg shadow-emerald-500/25">
                <UserPlus className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-emerald-900 to-green-900 bg-clip-text text-transparent">
                Create Account
              </h1>
              <p className="text-gray-600 mt-2">Join thousands of professionals</p>
            </div>

            {/* Error message */}
            {error && (
              <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-100 animate-fadeIn">
                <p className="text-red-600 text-sm text-center font-medium">{error}</p>
              </div>
            )}

            {/* Registration form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Step 1: Personal Information */}
              {currentStep === 1 && (
                <div className="space-y-6 animate-slideInRight">
                  <div className="space-y-2">
                    <Label htmlFor="fullName" className="text-gray-700 font-medium">
                      Full Name *
                    </Label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <User className={`h-5 w-5 transition-colors duration-200 ${
                          watchedFullName ? 'text-emerald-500' : 'text-gray-400'
                        }`} />
                      </div>
                      <Input
                        id="fullName"
                        type="text"
                        autoComplete="name"
                        className={`pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 ${
                          errors.fullName ? 'border-red-300 bg-red-50/50' : touchedFields.fullName && !errors.fullName ? 'border-green-300 bg-green-50/50' : ''
                        }`}
                        placeholder="Enter your full name"
                        {...register('fullName')}
                      />
                    </div>
                    {errors.fullName && (
                      <p className="text-red-500 text-sm mt-1 animate-slideDown">{errors.fullName.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-gray-700 font-medium">
                      Email Address *
                    </Label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Mail className={`h-5 w-5 transition-colors duration-200 ${
                          watchedEmail ? 'text-emerald-500' : 'text-gray-400'
                        }`} />
                      </div>
                      <Input
                        id="email"
                        type="email"
                        autoComplete="email"
                        className={`pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 ${
                          errors.email ? 'border-red-300 bg-red-50/50' : touchedFields.email && !errors.email ? 'border-green-300 bg-green-50/50' : ''
                        }`}
                        placeholder="Enter your email"
                        {...register('email')}
                      />
                    </div>
                    {errors.email && (
                      <p className="text-red-500 text-sm mt-1 animate-slideDown">{errors.email.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone" className="text-gray-700 font-medium">
                      Phone Number (Optional)
                    </Label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Phone className={`h-5 w-5 transition-colors duration-200 ${
                          watchedPhone ? 'text-emerald-500' : 'text-gray-400'
                        }`} />
                      </div>
                      <Input
                        id="phone"
                        type="tel"
                        autoComplete="tel"
                        className="pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        placeholder="Enter your phone number"
                        {...register('phone')}
                      />
                    </div>
                  </div>

                  <Button
                    type="button"
                    onClick={() => handleStepValidation(1)}
                    className="w-full h-14 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-semibold rounded-2xl shadow-lg shadow-emerald-500/25 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] group"
                  >
                    <div className="flex items-center justify-center">
                      Continue
                      <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-200" />
                    </div>
                  </Button>
                </div>
              )}

              {/* Step 2: Security */}
              {currentStep === 2 && (
                <div className="space-y-6 animate-slideInRight">
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-gray-700 font-medium">
                      Password *
                    </Label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Lock className={`h-5 w-5 transition-colors duration-200 ${
                          watchedPassword ? 'text-emerald-500' : 'text-gray-400'
                        }`} />
                      </div>
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        autoComplete="new-password"
                        className={`pl-12 pr-14 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 ${
                          errors.password ? 'border-red-300 bg-red-50/50' : ''
                        }`}
                        placeholder="Create a strong password"
                        {...register('password')}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors duration-200"
                      >
                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>

                    {/* Password strength indicator */}
                    {watchedPassword && passwordStrength && (
                      <div className="mt-3 p-3 rounded-xl bg-gray-50/50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">Password Strength</span>
                          <span className={`text-sm font-bold capitalize ${
                            passwordStrength.strength === 'weak' ? 'text-red-500' :
                            passwordStrength.strength === 'medium' ? 'text-yellow-500' :
                            passwordStrength.strength === 'strong' ? 'text-blue-500' :
                            'text-green-500'
                          }`}>
                            {passwordStrength.strength}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                          <div
                            className={`h-2 rounded-full transition-all duration-300 ${
                              passwordStrength.strength === 'weak' ? 'bg-red-400 w-1/4' :
                              passwordStrength.strength === 'medium' ? 'bg-yellow-400 w-2/4' :
                              passwordStrength.strength === 'strong' ? 'bg-blue-400 w-3/4' :
                              'bg-green-400 w-full'
                            }`}
                          ></div>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {[
                            { key: 'length', text: '8+ characters' },
                            { key: 'lowercase', text: 'Lowercase' },
                            { key: 'uppercase', text: 'Uppercase' },
                            { key: 'numbers', text: 'Numbers' },
                            { key: 'special', text: 'Special char' },
                          ].map(({ key, text }) => (
                            <div key={key} className="flex items-center space-x-2">
                              {passwordStrength.checks[key as keyof typeof passwordStrength.checks] ? (
                                <Check className="h-3 w-3 text-green-500" />
                              ) : (
                                <X className="h-3 w-3 text-red-400" />
                              )}
                              <span className={passwordStrength.checks[key as keyof typeof passwordStrength.checks] ? 'text-green-600' : 'text-gray-500'}>
                                {text}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {errors.password && (
                      <p className="text-red-500 text-sm mt-1 animate-slideDown">{errors.password.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword" className="text-gray-700 font-medium">
                      Confirm Password *
                    </Label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Shield className={`h-5 w-5 transition-colors duration-200 ${
                          watchedConfirmPassword ? 'text-emerald-500' : 'text-gray-400'
                        }`} />
                      </div>
                      <Input
                        id="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        autoComplete="new-password"
                        className={`pl-12 pr-14 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 ${
                          errors.confirmPassword ? 'border-red-300 bg-red-50/50' :
                          watchedConfirmPassword && watchedPassword === watchedConfirmPassword ? 'border-green-300 bg-green-50/50' : ''
                        }`}
                        placeholder="Confirm your password"
                        {...register('confirmPassword')}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors duration-200"
                      >
                        {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                    {errors.confirmPassword && (
                      <p className="text-red-500 text-sm mt-1 animate-slideDown">{errors.confirmPassword.message}</p>
                    )}
                  </div>

                  <div className="flex space-x-3">
                    <Button
                      type="button"
                      onClick={() => setCurrentStep(1)}
                      className="flex-1 h-12 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-2xl transition-all duration-200"
                    >
                      Back
                    </Button>
                    <Button
                      type="button"
                      onClick={() => handleStepValidation(2)}
                      disabled={
                        !watchedPassword ||
                        !watchedConfirmPassword ||
                        !passwordStrength ||
                        Object.values(passwordStrength.checks).some(check => !check)
                      }
                      className="flex-1 h-12 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-semibold rounded-2xl shadow-lg shadow-emerald-500/25 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all duration-200"
                    >
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Step 3: Terms & Final */}
              {currentStep === 3 && (
                <div className="space-y-6 animate-slideInRight">
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <input
                        id="termsAccepted"
                        type="checkbox"
                        className="mt-1 h-5 w-5 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 focus:ring-2"
                        {...register('termsAccepted')}
                      />
                      <Label htmlFor="termsAccepted" className="text-sm text-gray-700 leading-5">
                        I agree to the{' '}
                        <button type="button" className="text-emerald-600 hover:text-emerald-700 underline">
                          Terms of Service
                        </button>{' '}
                        and{' '}
                        <button type="button" className="text-emerald-600 hover:text-emerald-700 underline">
                          Privacy Policy
                        </button>
                      </Label>
                    </div>
                    {errors.termsAccepted && (
                      <p className="text-red-500 text-sm animate-slideDown">{errors.termsAccepted.message}</p>
                    )}
                  </div>

                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-emerald-800">
                        <p className="font-medium mb-1">Ready to create your account?</p>
                        <p className="text-emerald-700">
                          You'll receive an email confirmation and can start creating reports immediately.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex space-x-3">
                    <Button
                      type="button"
                      onClick={() => setCurrentStep(2)}
                      className="flex-1 h-12 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-2xl transition-all duration-200"
                    >
                      Back
                    </Button>
                    <Button
                      type="submit"
                      disabled={!isValid || isLoading}
                      className="flex-1 h-12 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-semibold rounded-2xl shadow-lg shadow-emerald-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 group"
                    >
                      {isLoading ? (
                        <div className="flex items-center justify-center">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                          Creating...
                        </div>
                      ) : (
                        <div className="flex items-center justify-center">
                          Create Account
                          <Sparkles className="ml-2 h-4 w-4 group-hover:rotate-12 transition-transform duration-200" />
                        </div>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </form>

            {/* Sign in link */}
            <div className="text-center mt-8 pt-6 border-t border-gray-200/50">
              <p className="text-gray-600 text-sm">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="text-emerald-600 hover:text-emerald-700 font-semibold transition-colors duration-200 hover:underline"
                >
                  Sign in here
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Additional decorative elements */}
        <div className="absolute -top-4 -left-4 w-24 h-24 rounded-full bg-gradient-to-br from-emerald-400/20 to-green-600/20 blur-xl"></div>
        <div className="absolute -bottom-4 -right-4 w-32 h-32 rounded-full bg-gradient-to-br from-blue-400/20 to-indigo-600/20 blur-xl"></div>
      </div>
    </div>
  );
};

export default RegisterPage;