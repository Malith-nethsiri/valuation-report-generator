import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
    Plus, FileText, User, Settings, LogOut, Search, Bell,
    Filter, MoreVertical, Calendar, TrendingUp, Award,
    ChevronDown, Menu, X, Home, BarChart3, Users,
    Shield, Zap, Clock, Eye, AlertCircle, CheckCircle, Trash2, Edit
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { reportApi } from '../services/api';
import { Report } from '../types';
import { Button } from '../components/Button';
import { DeleteConfirmDialog } from '../components/DeleteConfirmDialog';

const DashboardPage: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [reports, setReports] = useState<Report[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [reportToDelete, setReportToDelete] = useState<Report | null>(null);

    // Check if professional profile is complete
    const isProfileComplete = () => {
        if (!user) return false;

        const requiredFields = [
            'academic_qualifications',
            'membership_level',
            'membership_number',
            'professional_designation',
            'house_number',
            'area_development',
            'locality',
            'phone_primary'
        ];

        return requiredFields.every(field => {
            const value = user[field as keyof typeof user];
            return value && value.toString().trim().length > 0;
        });
    };

    const profileComplete = isProfileComplete();

    useEffect(() => {
        const fetchReports = async () => {
            try {
                const userReports = await reportApi.getReports();
                setReports(userReports);
            } catch (error) {
                console.error('Failed to fetch reports:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchReports();
    }, []);

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const handleDeleteClick = (report: Report, e: React.MouseEvent) => {
        e.stopPropagation();
        setReportToDelete(report);
        setDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!reportToDelete) return;

        try {
            await reportApi.deleteReport(reportToDelete.id);
            setReports(reports.filter(r => r.id !== reportToDelete.id));
            setReportToDelete(null);
        } catch (error) {
            console.error('Failed to delete report:', error);
        }
    };

    const quickStats = [
        { label: 'Total Reports', value: reports.length, icon: FileText, color: 'from-blue-500 to-indigo-600' },
        { label: 'This Month', value: reports.filter(r => new Date(r.created_at).getMonth() === new Date().getMonth()).length, icon: TrendingUp, color: 'from-emerald-500 to-green-600' },
        { label: 'Completed', value: reports.filter(r => r.status === 'completed').length, icon: Award, color: 'from-violet-500 to-purple-600' },
        { label: 'Draft', value: reports.filter(r => r.status === 'draft').length, icon: Clock, color: 'from-orange-500 to-red-500' },
    ];

    const sidebarItems = [
        { icon: Home, label: 'Dashboard', active: true },
        { icon: FileText, label: 'Reports', count: reports.length },
        { icon: BarChart3, label: 'Analytics' },
        { icon: Users, label: 'Clients' },
        { icon: Settings, label: 'Settings' },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
            {/* Top Navigation Bar */}
            <nav className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        {/* Left section */}
                        <div className="flex items-center space-x-4">
                            <button
                                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                                className="lg:hidden p-2 rounded-xl hover:bg-gray-100 transition-colors duration-200"
                            >
                                {isSidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                            </button>

                            <div className="flex items-center space-x-3">
                                <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg">
                                    <FileText className="h-6 w-6 text-white" />
                                </div>
                                <div className="hidden sm:block">
                                    <h1 className="text-xl font-bold gradient-text-primary">ReportGen Pro</h1>
                                    <p className="text-xs text-gray-500">Professional Platform</p>
                                </div>
                            </div>
                        </div>

                        {/* Center section - Search */}
                        <div className="hidden md:flex flex-1 max-w-md mx-8">
                            <div className="relative w-full">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Search className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    placeholder="Search reports..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 bg-gray-100/50 border border-gray-200/50 rounded-2xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200"
                                />
                            </div>
                        </div>

                        {/* Right section */}
                        <div className="flex items-center space-x-3">
                            <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-all duration-200 relative">
                                <Bell className="h-6 w-6" />
                                <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                            </button>

                            {/* User Menu */}
                            <div className="relative">
                                <button
                                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                                    className="flex items-center space-x-3 p-2 text-gray-700 hover:bg-gray-100 rounded-2xl transition-all duration-200"
                                >
                                    <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl flex items-center justify-center text-white font-bold text-sm">
                                        {user?.full_name?.charAt(0) || 'U'}
                                    </div>
                                    <div className="hidden sm:block text-left">
                                        <p className="text-sm font-medium">{user?.full_name}</p>
                                        <p className="text-xs text-gray-500">{user?.email}</p>
                                    </div>
                                    <ChevronDown className="h-4 w-4 text-gray-400" />
                                </button>

                                {/* User Dropdown */}
                                {isUserMenuOpen && (
                                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-3xl shadow-2xl border border-gray-200/50 py-2 z-50 animate-scaleIn">
                                        <div className="px-4 py-3 border-b border-gray-100">
                                            <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                                            <p className="text-xs text-gray-500">{user?.email}</p>
                                        </div>
                                        <Link
                                            to="/profile"
                                            className="flex items-center px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors duration-200"
                                        >
                                            <User className="h-4 w-4 mr-3" />
                                            Your Profile
                                        </Link>
                                        <button className="flex items-center w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition-colors duration-200">
                                            <Settings className="h-4 w-4 mr-3" />
                                            Settings
                                        </button>
                                        <hr className="my-2" />
                                        <button
                                            onClick={handleLogout}
                                            className="flex items-center w-full px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors duration-200"
                                        >
                                            <LogOut className="h-4 w-4 mr-3" />
                                            Sign Out
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            <div className="flex">
                {/* Sidebar */}
                <aside className={`${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative z-40 w-64 h-[calc(100vh-4rem)] bg-white/60 backdrop-blur-xl border-r border-gray-200/50 transition-transform duration-300 ease-in-out`}>
                    <div className="p-6 space-y-6">
                        {/* Quick Actions */}
                        <div className="space-y-3">
                            <Button
                                onClick={() => navigate('/reports/new')}
                                className="w-full bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white font-semibold py-3 px-4 rounded-2xl shadow-lg shadow-violet-500/25 transition-all duration-200 transform hover:scale-[1.02] group"
                            >
                                <Plus className="h-5 w-5 mr-2 group-hover:rotate-90 transition-transform duration-200" />
                                Create Report
                            </Button>
                        </div>

                        {/* Navigation */}
                        <nav className="space-y-2">
                            {sidebarItems.map((item, index) => (
                                <button
                                    key={index}
                                    className={`w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium rounded-2xl transition-all duration-200 ${item.active
                                            ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/25'
                                            : 'text-gray-700 hover:bg-gray-100'
                                        }`}
                                >
                                    <div className="flex items-center">
                                        <item.icon className="h-5 w-5 mr-3" />
                                        {item.label}
                                    </div>
                                    {item.count !== undefined && (
                                        <span className={`px-2 py-1 text-xs rounded-full ${item.active ? 'bg-white/20 text-white' : 'bg-gray-200 text-gray-600'
                                            }`}>
                                            {item.count}
                                        </span>
                                    )}
                                </button>
                            ))}
                        </nav>

                        {/* Quick Stats Mini */}
                        <div className="bg-gradient-to-br from-gray-50/50 to-white/50 rounded-3xl p-4 border border-gray-200/30">
                            <h3 className="text-sm font-semibold text-gray-800 mb-3">Quick Overview</h3>
                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-gray-600">Total Reports</span>
                                    <span className="text-sm font-bold text-violet-600">{reports.length}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-gray-600">This Week</span>
                                    <span className="text-sm font-bold text-green-600">
                                        {reports.filter(r => new Date(r.created_at).getTime() > Date.now() - 7 * 24 * 60 * 60 * 1000).length}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 lg:ml-0">
                    <div className="max-w-7xl mx-auto p-6 space-y-8">
                        {/* Welcome Header */}
                        <div className="bg-gradient-to-r from-violet-500/10 via-purple-500/10 to-blue-500/10 rounded-3xl p-8 border border-violet-200/30 animate-fadeIn">
                            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between">
                                <div>
                                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                                        Welcome back, {user?.full_name?.split(' ')[0]}! 👋
                                    </h1>
                                    <p className="text-gray-600 text-lg">
                                        Ready to create some amazing reports? Let's get started.
                                    </p>
                                </div>
                                <div className="mt-4 sm:mt-0 flex space-x-3">
                                    <Button
                                        onClick={() => navigate('/reports/new')}
                                        className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white px-6 py-3 rounded-2xl font-semibold shadow-lg shadow-violet-500/25 transition-all duration-200 transform hover:scale-105"
                                    >
                                        <Plus className="h-5 w-5 mr-2" />
                                        New Report
                                    </Button>
                                </div>
                            </div>
                        </div>

                        {/* Profile Completion Banner */}
                        {!profileComplete && (
                            <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-3xl p-6 shadow-lg relative z-10 mb-8">
                                <div className="flex items-start space-x-4">
                                    <div className="flex-shrink-0">
                                        <div className="p-3 bg-amber-100 rounded-2xl">
                                            <AlertCircle className="h-6 w-6 text-amber-600" />
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                            Complete Your Professional Profile
                                        </h3>
                                        <p className="text-gray-700 mb-4">
                                            To create professional reports with custom letterheads, please complete your professional profile.
                                            This information will be used to generate personalized letterheads for all your reports.
                                        </p>
                                        <div className="flex flex-col sm:flex-row gap-3">
                                            <Button
                                                onClick={() => navigate('/profile/professional')}
                                                className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white px-6 py-2 rounded-2xl font-semibold shadow-lg shadow-amber-500/25 transition-all duration-200"
                                            >
                                                <User className="h-4 w-4 mr-2" />
                                                Complete Profile
                                            </Button>
                                            <Link
                                                to="/profile"
                                                className="inline-flex items-center px-4 py-2 text-amber-700 hover:text-amber-800 hover:bg-amber-50 rounded-2xl transition-colors duration-200 font-medium"
                                            >
                                                View Current Profile
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Quick Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            {quickStats.map((stat, index) => (
                                <div
                                    key={index}
                                    className="bg-white/60 backdrop-blur-sm rounded-3xl p-6 border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-300 animate-scaleIn group"
                                    style={{ animationDelay: `${index * 0.1}s` }}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                                            <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                                        </div>
                                        <div className={`p-3 rounded-2xl bg-gradient-to-br ${stat.color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                                            <stat.icon className="h-6 w-6 text-white" />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Recent Reports */}
                        <div className="bg-white/60 backdrop-blur-sm rounded-3xl border border-white/20 shadow-xl">
                            <div className="p-6 border-b border-gray-200/50">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-xl font-bold text-gray-900">Recent Reports</h2>
                                    <div className="flex space-x-3">
                                        <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-all duration-200">
                                            <Filter className="h-5 w-5" />
                                        </button>
                                        <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-all duration-200">
                                            <MoreVertical className="h-5 w-5" />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="p-6">
                                {isLoading ? (
                                    <div className="space-y-4">
                                        {[1, 2, 3].map((i) => (
                                            <div key={i} className="animate-shimmer h-16 bg-gray-200 rounded-2xl"></div>
                                        ))}
                                    </div>
                                ) : reports.length === 0 ? (
                                    <div className="text-center py-12">
                                        <div className="w-24 h-24 bg-gradient-to-br from-violet-100 to-purple-200 rounded-3xl flex items-center justify-center mx-auto mb-4">
                                            <FileText className="h-12 w-12 text-violet-600" />
                                        </div>
                                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No reports yet</h3>
                                        <p className="text-gray-600 mb-6">Create your first report to get started!</p>
                                        <Button
                                            onClick={() => navigate('/reports/new')}
                                            className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white px-6 py-3 rounded-2xl font-semibold"
                                        >
                                            <Plus className="h-5 w-5 mr-2" />
                                            Create Your First Report
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {[...reports].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5).map((report, index) => (
                                            <div
                                                key={report.id}
                                                className="flex items-center justify-between p-4 bg-gray-50/50 rounded-2xl border border-gray-100 hover:bg-gray-100/50 hover:border-gray-200 transition-all duration-200 cursor-pointer group"
                                                onClick={() => navigate(`/reports/${report.id}`)}
                                            >
                                                <div className="flex items-center space-x-4">
                                                    <div className={`p-2 rounded-xl ${report.status === 'completed'
                                                            ? 'bg-green-100 text-green-600'
                                                            : 'bg-orange-100 text-orange-600'
                                                        }`}>
                                                        <FileText className="h-5 w-5" />
                                                    </div>
                                                    <div>
                                                        <h3 className="font-medium text-gray-900 group-hover:text-violet-600 transition-colors duration-200">
                                                            {report.report_type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Untitled Report'}
                                                        </h3>
                                                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
                                                            {report.report_reference && (
                                                                <span className="font-mono text-xs bg-violet-50 text-violet-700 px-2 py-0.5 rounded">
                                                                    {report.report_reference}
                                                                </span>
                                                            )}
                                                            {report.applicant_full_name && (
                                                                <span className="flex items-center">
                                                                    <User className="h-3.5 w-3.5 mr-1" />
                                                                    {report.applicant_full_name}
                                                                </span>
                                                            )}
                                                            <span className="flex items-center">
                                                                <Calendar className="h-4 w-4 mr-1" />
                                                                {new Date(report.created_at).toLocaleDateString()}
                                                            </span>
                                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${report.status === 'completed'
                                                                    ? 'bg-green-100 text-green-800'
                                                                    : 'bg-orange-100 text-orange-800'
                                                                }`}>
                                                                {report.status?.charAt(0).toUpperCase() + report.status?.slice(1)}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center space-x-3">
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            navigate(`/reports/edit/${report.id}`);
                                                        }}
                                                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-200"
                                                        title="Edit Report"
                                                    >
                                                        <Edit className="h-5 w-5" />
                                                    </button>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            if (report.status === 'completed') {
                                                                reportApi.generateReportDocx(report.id);
                                                            }
                                                        }}
                                                        disabled={report.status !== 'completed'}
                                                        className={`p-2 rounded-xl transition-all duration-200 ${report.status === 'completed'
                                                                ? 'text-violet-600 hover:bg-violet-100'
                                                                : 'text-gray-400 cursor-not-allowed'
                                                            }`}
                                                    >
                                                        <Eye className="h-5 w-5" />
                                                    </button>
                                                    <button
                                                        onClick={(e) => handleDeleteClick(report, e)}
                                                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200"
                                                    >
                                                        <Trash2 className="h-5 w-5" />
                                                    </button>
                                                    <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-200">
                                                        <MoreVertical className="h-5 w-5" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}

                                        {reports.length > 5 && (
                                            <div className="pt-4 text-center">
                                                <button className="text-violet-600 hover:text-violet-700 font-medium transition-colors duration-200">
                                                    View all reports ({reports.length})
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </main>
            </div>

            {/* Mobile overlay */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/20 backdrop-blur-sm z-30 lg:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Delete Confirmation Dialog */}
            <DeleteConfirmDialog
                isOpen={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
                onConfirm={handleDeleteConfirm}
                reportReference={reportToDelete?.report_reference}
                title="Delete Report"
                description="Are you sure you want to delete this report? This action cannot be undone and all data associated with this report will be permanently removed."
            />
        </div>
    );
};

export default DashboardPage;
