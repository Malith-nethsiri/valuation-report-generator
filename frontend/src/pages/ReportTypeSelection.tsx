import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Home, Building2, ChevronRight, Star,
  Clock, Users, Award, TrendingUp, Sparkles,
  FileText, Calendar, MapPin, Shield, Layers, Landmark
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface ReportType {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ElementType;
  color: string;
  gradient: string;
  features: string[];
  estimatedTime: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  isAvailable: boolean;
  comingSoon?: boolean;
  popular?: boolean;
  recommended?: boolean;
}

const reportTypes: ReportType[] = [
  {
    id: 'residential_property',
    name: 'Residential/Commercial Property Report',
    description: 'Comprehensive property analysis and valuation report for residential and commercial properties including condition assessment, market analysis, and recommendations.',
    category: 'Real Estate',
    icon: Home,
    color: 'from-emerald-500 to-green-600',
    gradient: 'from-emerald-50 to-green-100',
    features: [
      'Property condition assessment',
      'Market value analysis',
      'Neighborhood comparison',
      'Investment recommendations',
      'Professional DOCX export'
    ],
    estimatedTime: '15-20 minutes',
    difficulty: 'Beginner',
    isAvailable: true,
    popular: true,
    recommended: true
  },
  {
    id: 'multi_property',
    name: 'Multi-Property Report',
    description: 'Value multiple properties in a single comprehensive report with summary page, individual property sections, and combined valuation totals.',
    category: 'Real Estate',
    icon: Layers,
    color: 'from-violet-500 to-purple-600',
    gradient: 'from-violet-50 to-purple-100',
    features: [
      'Multiple properties in one report',
      'Summary page with property listing',
      'Grand total valuation',
      'Property library integration',
      'Professional fee invoice',
      'Drag-drop property ordering'
    ],
    estimatedTime: '25-35 minutes',
    difficulty: 'Intermediate',
    isAvailable: true,
    popular: true
  },
  {
    id: 'bare_land',
    name: 'Bare Land Valuation Report',
    description: 'Comprehensive land-only valuation for vacant lots, development sites, and bare land properties without existing buildings.',
    category: 'Real Estate',
    icon: Landmark,
    color: 'from-amber-500 to-orange-600',
    gradient: 'from-amber-50 to-orange-100',
    features: [
      'Land extent and boundaries',
      'Development feasibility assessment',
      'Infrastructure readiness analysis',
      'Land-only valuation (no buildings)',
      'Up to 20 property photos',
      'Ongoing construction notes'
    ],
    estimatedTime: '12-15 minutes',
    difficulty: 'Beginner',
    isAvailable: true,
    popular: false
  }
];

const ReportTypeSelection: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [hoveredType, setHoveredType] = useState<string | null>(null);

  const handleSelectReport = (reportType: ReportType) => {
    if (!reportType.isAvailable) return;

    setSelectedType(reportType.id);

    // Navigate to the multi-step form for this report type
    setTimeout(() => {
      navigate(`/reports/new/${reportType.id}`);
    }, 500);
  };

  const getDifficultyColor = (difficulty: ReportType['difficulty']) => {
    switch (difficulty) {
      case 'Beginner': return 'text-green-600 bg-green-100';
      case 'Intermediate': return 'text-yellow-600 bg-yellow-100';
      case 'Advanced': return 'text-red-600 bg-red-100';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to="/dashboard"
                className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to Dashboard
              </Link>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Welcome back,</p>
              <p className="font-semibold text-gray-900">{user?.full_name}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex p-4 bg-gradient-to-br from-violet-500 to-purple-600 rounded-3xl shadow-2xl shadow-violet-500/25 mb-6 animate-float">
            <FileText className="h-12 w-12 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black gradient-text-primary mb-6">
            Choose Your Report Type
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Select the type of report you'd like to create. Each report type is tailored
            with specific workflows and data collection optimized for your needs.
          </p>
        </div>

        {/* Report Type Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-8 mb-12">
          {reportTypes.map((reportType, index) => (
            <div
              key={reportType.id}
              className={`group relative bg-white/70 backdrop-blur-sm rounded-3xl border border-white/20 shadow-xl hover:shadow-2xl transition-all duration-500 overflow-hidden cursor-pointer animate-scaleIn ${
                !reportType.isAvailable ? 'opacity-60' : 'hover:scale-[1.02]'
              } ${selectedType === reportType.id ? 'ring-4 ring-violet-500 scale-[1.02]' : ''}`}
              style={{ animationDelay: `${index * 0.1}s` }}
              onMouseEnter={() => setHoveredType(reportType.id)}
              onMouseLeave={() => setHoveredType(null)}
              onClick={() => handleSelectReport(reportType)}
            >
              {/* Gradient Background */}
              <div className={`absolute inset-0 bg-gradient-to-br ${reportType.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

              {/* Content */}
              <div className="relative p-8">
                {/* Header */}
                <div className="flex items-start justify-between mb-6">
                  <div className={`p-4 rounded-2xl bg-gradient-to-br ${reportType.color} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    <reportType.icon className="h-8 w-8 text-white" />
                  </div>

                  {/* Badges */}
                  <div className="flex flex-col items-end space-y-2">
                    {reportType.popular && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-lg">
                        <Star className="h-3 w-3 mr-1" />
                        Popular
                      </span>
                    )}
                    {reportType.recommended && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg">
                        <Award className="h-3 w-3 mr-1" />
                        Recommended
                      </span>
                    )}
                    {reportType.comingSoon && (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-gray-400 to-gray-600 text-white">
                        <Clock className="h-3 w-3 mr-1" />
                        Coming Soon
                      </span>
                    )}
                  </div>
                </div>

                {/* Title & Description */}
                <div className="mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-violet-700 transition-colors duration-300">
                    {reportType.name}
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {reportType.description}
                  </p>
                </div>

                {/* Features */}
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-gray-800 mb-3">Key Features:</h4>
                  <div className="space-y-2">
                    {reportType.features.slice(0, 3).map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center text-sm text-gray-600">
                        <div className="w-1.5 h-1.5 bg-violet-500 rounded-full mr-3" />
                        {feature}
                      </div>
                    ))}
                    {reportType.features.length > 3 && (
                      <div className="text-sm text-gray-500 ml-5">
                        +{reportType.features.length - 3} more features
                      </div>
                    )}
                  </div>
                </div>

                {/* Metadata */}
                <div className="flex items-center justify-between text-xs text-gray-500 mb-6">
                  <div className="flex items-center space-x-4">
                    <span className="flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {reportType.estimatedTime}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(reportType.difficulty)}`}>
                      {reportType.difficulty}
                    </span>
                  </div>
                  <span className="text-gray-400">{reportType.category}</span>
                </div>

                {/* Action Button */}
                {reportType.isAvailable ? (
                  <button
                    className={`w-full flex items-center justify-center px-6 py-4 bg-gradient-to-r ${reportType.color} hover:shadow-xl text-white font-semibold rounded-2xl transition-all duration-300 transform ${
                      hoveredType === reportType.id ? 'scale-[1.02]' : ''
                    } ${selectedType === reportType.id ? 'animate-pulse' : ''}`}
                  >
                    {selectedType === reportType.id ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                        Loading...
                      </>
                    ) : (
                      <>
                        Start Report
                        <ChevronRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform duration-200" />
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    disabled
                    className="w-full flex items-center justify-center px-6 py-4 bg-gray-300 text-gray-500 font-semibold rounded-2xl cursor-not-allowed"
                  >
                    <Clock className="h-5 w-5 mr-2" />
                    Coming Soon
                  </button>
                )}

                {/* Sparkle Effects */}
                {hoveredType === reportType.id && reportType.isAvailable && (
                  <div className="absolute top-4 right-4 animate-bounce">
                    <Sparkles className="h-6 w-6 text-violet-500 opacity-70" />
                  </div>
                )}
              </div>

              {/* Selection Glow Effect */}
              {selectedType === reportType.id && (
                <div className="absolute inset-0 bg-violet-500/10 animate-pulse" />
              )}
            </div>
          ))}
        </div>

        {/* Help Section */}
        <div className="bg-gradient-to-r from-violet-500/10 via-purple-500/10 to-blue-500/10 rounded-3xl p-8 border border-violet-200/30 text-center">
          <h3 className="text-2xl font-bold gradient-text-primary mb-4">
            Need Help Choosing?
          </h3>
          <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
            Not sure which report type fits your needs? Our Residential Property Report
            is perfect for beginners and covers most common use cases.
          </p>
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              {
                icon: Users,
                title: 'Beginner Friendly',
                description: 'Step-by-step guidance through the entire process'
              },
              {
                icon: Calendar,
                title: 'Quick Setup',
                description: 'Get professional results in just 15-20 minutes'
              },
              {
                icon: MapPin,
                title: 'Comprehensive',
                description: 'Covers all essential property analysis aspects'
              }
            ].map((feature, index) => (
              <div key={index} className="flex flex-col items-center p-4">
                <div className="p-3 bg-white rounded-2xl shadow-lg mb-4">
                  <feature.icon className="h-6 w-6 text-violet-600" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">{feature.title}</h4>
                <p className="text-sm text-gray-600 text-center">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportTypeSelection;