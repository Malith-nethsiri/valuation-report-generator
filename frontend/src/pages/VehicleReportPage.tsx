/**
 * VehicleReportPage - Wrapper page for vehicle valuation reports
 *
 * Handles both creating new vehicle reports and editing existing ones.
 */

import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Car } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { VehicleStepForm } from '../components/VehicleStepForm';

const VehicleReportPage: React.FC = () => {
  const { reportId } = useParams<{ reportId?: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const isEditMode = !!reportId;
  const parsedReportId = reportId ? parseInt(reportId, 10) : undefined;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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

            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl shadow-lg">
                <Car className="h-5 w-5 text-white" />
              </div>
              <div className="text-right">
                <h1 className="font-semibold text-gray-900">
                  {isEditMode ? 'Edit Vehicle Report' : 'New Vehicle Report'}
                </h1>
                <p className="text-sm text-gray-500">
                  {user?.full_name}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Form Container */}
      <div className="max-w-5xl mx-auto">
        <VehicleStepForm
          mode={isEditMode ? 'edit' : 'create'}
          reportId={parsedReportId}
          onSaveComplete={(vehicle) => {
            // Navigate to dashboard or report detail after save
            navigate('/dashboard');
          }}
          onCancel={() => {
            navigate('/dashboard');
          }}
        />
      </div>
    </div>
  );
};

export default VehicleReportPage;
