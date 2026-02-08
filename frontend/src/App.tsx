import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import ProfessionalProfilePage from './pages/ProfessionalProfilePage';
import ReportTypeSelection from './pages/ReportTypeSelection';
import PropertyReportForm from './pages/PropertyReportForm';
import MultiPropertyForm from './pages/MultiPropertyForm';
import VehicleReportPage from './pages/VehicleReportPage';
import VehicleLibraryPage from './pages/VehicleLibraryPage';
import ReportEditRouter from './components/ReportEditRouter';
import { DataCollectionForm } from './components/DataCollectionForm';
import TestComponents from './pages/TestComponents';
import { FileText, ArrowRight, Shield, Users, Zap } from 'lucide-react';
import { clearLegacyDrafts } from './utils/migrateLegacyDrafts';

// Ultra-modern Landing Page
const LandingPage: React.FC = () => {
    return (
        <div className="min-h-screen bg-gradient-to-br from-violet-50 via-white to-cyan-50 relative overflow-hidden">
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-gradient-to-br from-violet-400/10 to-purple-600/10 blur-3xl animate-pulse"></div>
                <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-gradient-to-br from-blue-400/10 to-indigo-600/10 blur-3xl animate-pulse delay-1000"></div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-gradient-to-br from-cyan-400/5 to-blue-600/5 blur-3xl animate-spin [animation-duration:30s]"></div>
            </div>

            <div className="container mx-auto px-4 py-8 md:py-16 relative z-10">
                {/* Header */}
                <div className="text-center mb-16 animate-fadeIn">
                    <div className="flex justify-center mb-6">
                        <div className="p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-3xl shadow-2xl shadow-violet-500/25 animate-float">
                            <FileText className="h-10 w-10 text-white" />
                        </div>
                    </div>
                    <h1 className="text-5xl md:text-7xl font-black gradient-text-primary mb-6">
                        Valuation Report
                    </h1>
                    <h2 className="text-2xl md:text-3xl font-bold text-gray-800 mb-6">
                        Valuation Report Generation Platform
                    </h2>
                    <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-12 leading-relaxed">
                        Transform your data collection process with our modern platform.
                        Create residential property reports with multi-step workflows,
                        user management, and document generation.
                    </p>

                    {/* CTA Buttons */}
                    <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
                        <Link
                            to="/register"
                            className="group w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white text-lg font-semibold rounded-2xl shadow-2xl shadow-violet-500/25 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]"
                        >
                            Register
                            <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-200" />
                        </Link>
                        <Link
                            to="/login"
                            className="group w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 bg-white/80 backdrop-blur-sm hover:bg-white text-gray-800 text-lg font-semibold rounded-2xl shadow-xl border border-gray-200/50 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]"
                        >
                            Sign In
                        </Link>
                    </div>
                </div>

                {/* Features Grid */}
                <div className="grid md:grid-cols-3 gap-8 mb-16">
                    {[
                        {
                            icon: Shield,
                            title: 'Secure & Private',
                            description: 'Bank-level security with encrypted data storage and user authentication.',
                            color: 'from-blue-500 to-indigo-600'
                        },
                        {
                            icon: Users,
                            title: 'Multi-User Platform',
                            description: 'Team collaboration with user profiles, permissions, and shared reports.',
                            color: 'from-emerald-500 to-green-600'
                        },
                        {
                            icon: Zap,
                            title: 'Lightning Fast',
                            description: 'Modern tech stack with instant report generation and real-time updates.',
                            color: 'from-violet-500 to-purple-600'
                        }
                    ].map((feature, index) => (
                        <div
                            key={index}
                            className="group bg-white/60 backdrop-blur-sm rounded-3xl p-8 shadow-xl border border-white/20 hover:shadow-2xl transition-all duration-300 animate-scaleIn"
                            style={{ animationDelay: `${index * 0.2}s` }}
                        >
                            <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${feature.color} shadow-lg mb-6 group-hover:scale-110 transition-transform duration-300`}>
                                <feature.icon className="h-8 w-8 text-white" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 mb-4">{feature.title}</h3>
                            <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                        </div>
                    ))}
                </div>

                {/* Bottom CTA */}
                <div className="text-center bg-gradient-to-r from-violet-500/10 to-purple-600/10 backdrop-blur-sm rounded-3xl p-12 border border-violet-200/30">
                    <h3 className="text-3xl font-bold gradient-text-primary mb-4">
                        Ready to transform your workflow?
                    </h3>
                    <p className="text-gray-600 mb-8 text-lg">
                        Join the next generation of report creation tools
                    </p>
                    <Link
                        to="/register"
                        className="group inline-flex items-center justify-center px-10 py-5 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white text-xl font-bold rounded-2xl shadow-2xl shadow-violet-500/25 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]"
                    >
                        Create Your Account
                        <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform duration-200" />
                    </Link>
                </div>
            </div>
        </div>
    );
};


const LegacyFormPage: React.FC = () => {
    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
            <div className="container mx-auto px-4 py-8 md:py-16">
                <div className="text-center mb-12">
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                        Legacy Form (v0.0)
                    </h1>
                    <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                        Original form - still functional for testing while v0.1 is in development
                    </p>
                </div>
                <DataCollectionForm />
            </div>
        </div>
    );
};

const AppRoutes: React.FC = () => {
    const { user, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <Routes>
            {/* Public routes */}
            <Route
                path="/login"
                element={!user ? <LoginPage /> : <Navigate to="/dashboard" replace />}
            />
            <Route
                path="/register"
                element={!user ? <RegisterPage /> : <Navigate to="/dashboard" replace />}
            />

            {/* Testing routes */}
            <Route path="/legacy" element={<LegacyFormPage />} />
            <Route path="/test-components" element={<TestComponents />} />

            {/* Protected routes */}
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <DashboardPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/profile"
                element={
                    <ProtectedRoute>
                        <ProfilePage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/profile/professional"
                element={
                    <ProtectedRoute>
                        <ProfessionalProfilePage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/new"
                element={
                    <ProtectedRoute>
                        <ReportTypeSelection />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/new/residential_property"
                element={
                    <ProtectedRoute>
                        <PropertyReportForm reportType="residential_property" />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/new/multi_property"
                element={
                    <ProtectedRoute>
                        <MultiPropertyForm />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/multi-property/:reportId"
                element={
                    <ProtectedRoute>
                        <MultiPropertyForm />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/new/bare_land"
                element={
                    <ProtectedRoute>
                        <PropertyReportForm reportType="bare_land" />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/new/vehicle"
                element={
                    <ProtectedRoute>
                        <VehicleReportPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/vehicle/:reportId"
                element={
                    <ProtectedRoute>
                        <VehicleReportPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/vehicle-library"
                element={
                    <ProtectedRoute>
                        <VehicleLibraryPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/reports/edit/:reportId"
                element={
                    <ProtectedRoute>
                        <ReportEditRouter />
                    </ProtectedRoute>
                }
            />

            {/* Root route */}
            <Route
                path="/"
                element={user ? <Navigate to="/dashboard" replace /> : <LandingPage />}
            />

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

function App() {
    // Clear legacy localStorage drafts on app mount (one-time migration)
    useEffect(() => {
        clearLegacyDrafts();
    }, []);

    return (
        <Router>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </Router>
    );
}

export default App;
