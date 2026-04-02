import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { reportApi } from '../services/api';
import { Report } from '../types';
import toast from 'react-hot-toast';
import PropertyReportForm from '../pages/PropertyReportForm';
import { AlertCircle } from 'lucide-react';

const ReportEditRouter: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [reportData, setReportData] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!reportId) {
        toast.error('Invalid report ID');
        navigate('/dashboard');
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const report = await reportApi.getReport(parseInt(reportId));
        setReportData(report);
      } catch (err: any) {
        console.error('Failed to load report:', err);
        const errorMessage = err.response?.data?.detail || 'Failed to load report';
        toast.error(errorMessage);
        setError(errorMessage);

        // Navigate to dashboard after showing error
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [reportId, navigate]);

  // Handle multi-property and vehicle report navigation
  useEffect(() => {
    if (!reportData) return;
    if (reportData.report_type === 'multi_property') {
      navigate(`/reports/multi-property/${reportId}`);
    }
    if (reportData.report_type === 'vehicle') {
      navigate(`/reports/vehicle/${reportId}`);
    }
  }, [reportData, reportId, navigate]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading report...</p>
        </div>
      </div>
    );
  }

  // Error state (with redirect happening in useEffect)
  if (error || !reportData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  // Route to the appropriate form based on report type
  switch (reportData.report_type) {
    case 'residential_property':
      return <PropertyReportForm reportType="residential_property" />;

    case 'bare_land':
      return <PropertyReportForm reportType="bare_land" />;

    case 'multi_property':
      // Navigation handled in useEffect above to avoid setState during render
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-violet-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading multi-property report...</p>
          </div>
        </div>
      );

    case 'vehicle':
      // Navigation to /reports/vehicle/:id handled in useEffect above
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-cyan-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-cyan-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading vehicle report...</p>
          </div>
        </div>
      );

    default:
      // Unknown report type
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-blue-50">
          <div className="text-center max-w-md p-8">
            <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Unknown Report Type
            </h2>
            <p className="text-gray-600 mb-4">
              This report has an unknown type: <strong>{reportData.report_type}</strong>
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      );
  }
};

export default ReportEditRouter;
