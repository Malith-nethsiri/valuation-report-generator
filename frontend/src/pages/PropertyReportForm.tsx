import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Download, FileText } from 'lucide-react';
import MultiStepForm, { ResidentialPropertyFormData } from '../components/MultiStepForm';
import { useAuth } from '../contexts/AuthContext';
import { reportApi } from '../services/api';
import toast from 'react-hot-toast';
import { Report } from '../types';
import { authTokenStorage } from '../utils/secureStorage';

interface ReportTypeConfig {
  reportType: 'bare_land' | 'residential_property';
  label: string;
  reportLabel: string;
  draftKey: string;
  stepKey: string;
  color: {
    primary: string;
    gradient: string;
    gradientHover: string;
    bg: string;
    border: string;
    text: string;
    shadow: string;
    spinner: string;
    editBadgeBg: string;
    editBadgeText: string;
    loadingBg: string;
  };
  nullBuildings: boolean;
  cleanRoomDimensions: boolean;
}

const REPORT_CONFIGS: Record<string, ReportTypeConfig> = {
  bare_land: {
    reportType: 'bare_land',
    label: 'bare land report',
    reportLabel: 'Bare Land Valuation',
    draftKey: 'bareLandFormDraft',
    stepKey: 'bareLandFormStep',
    color: {
      primary: 'amber',
      gradient: 'from-amber-500 to-orange-600',
      gradientHover: 'from-amber-600 to-orange-700',
      bg: 'from-amber-50 via-white to-orange-50',
      border: 'from-amber-500/10 to-orange-500/10',
      text: 'text-amber-600 hover:text-amber-700',
      shadow: 'shadow-amber-500/25',
      spinner: 'border-amber-600',
      editBadgeBg: 'bg-amber-100',
      editBadgeText: 'text-amber-800',
      loadingBg: 'from-slate-50 via-white to-orange-50',
    },
    nullBuildings: true,
    cleanRoomDimensions: false,
  },
  residential_property: {
    reportType: 'residential_property',
    label: 'residential property report',
    reportLabel: 'Residential Property',
    draftKey: 'residentialFormDraft',
    stepKey: 'residentialFormStep',
    color: {
      primary: 'emerald',
      gradient: 'from-emerald-500 to-green-600',
      gradientHover: 'from-emerald-600 to-green-700',
      bg: 'from-emerald-50 via-white to-blue-50',
      border: 'from-emerald-500/10 to-green-500/10',
      text: 'text-emerald-600 hover:text-emerald-700',
      shadow: 'shadow-emerald-500/25',
      spinner: 'border-violet-600',
      editBadgeBg: 'bg-blue-100',
      editBadgeText: 'text-blue-800',
      loadingBg: 'from-slate-50 via-white to-indigo-50',
    },
    nullBuildings: false,
    cleanRoomDimensions: true,
  },
};

interface PropertyReportFormProps {
  reportType: 'bare_land' | 'residential_property';
}

const PropertyReportForm: React.FC<PropertyReportFormProps> = ({ reportType }) => {
  const config = REPORT_CONFIGS[reportType];
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { reportId } = useParams<{ reportId: string }>();

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [existingReport, setExistingReport] = useState<Report | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [reportCreated, setReportCreated] = useState<any>(null);
  const [isGeneratingDocx, setIsGeneratingDocx] = useState(false);

  // Load report for editing
  useEffect(() => {
    const loadReportForEdit = async () => {
      if (!reportId) {
        setIsEditMode(false);
        return;
      }

      setIsLoadingReport(true);
      setIsEditMode(true);

      try {
        const report = await reportApi.getReport(parseInt(reportId));

        const cleanedReport = { ...report };

        // Strip room length/width from loaded data (residential only)
        if (config.cleanRoomDimensions && cleanedReport.buildings && Array.isArray(cleanedReport.buildings)) {
          cleanedReport.buildings = cleanedReport.buildings.map((building: any) => ({
            ...building,
            floors: building.floors?.map((floor: any) => ({
              ...floor,
              rooms: floor.rooms?.map((room: any) => {
                const { length, width, ...cleanRoom } = room;
                return cleanRoom;
              }) || []
            })) || []
          }));
        }

        // Ensure property_photos is always an array
        if (!cleanedReport.property_photos) {
          cleanedReport.property_photos = [];
        }

        setExistingReport(cleanedReport);
        console.log(`[PropertyReportForm:${reportType}] Loaded report for editing:`, cleanedReport);
      } catch (error: any) {
        console.error('Failed to load report:', error);
        toast.error('Failed to load report for editing');
        navigate('/dashboard');
      } finally {
        setIsLoadingReport(false);
      }
    };

    loadReportForEdit();
  }, [reportId, navigate, reportType, config.cleanRoomDimensions]);

  const handleFormSubmit = async (
    data: ResidentialPropertyFormData,
    submissionType: 'draft' | 'complete' = 'complete'
  ) => {
    if (!user) {
      console.error(`[PropertyReportForm:${reportType}] No user found, redirecting to login`);
      navigate('/login');
      return;
    }

    const token = authTokenStorage.getToken();
    if (!token) {
      console.error(`[PropertyReportForm:${reportType}] No auth token found`);
      toast.error('Your session has expired. Please log in again.');
      navigate('/login');
      return;
    }

    setIsSubmitting(true);
    try {
      const cleanedData = { ...data };

      // Residential: clean buildings data (migrate utilities, strip room dimensions)
      if (config.cleanRoomDimensions && cleanedData.buildings && Array.isArray(cleanedData.buildings)) {
        cleanedData.buildings = cleanedData.buildings.map((building: any) => {
          // Migrate utilities_services string values to arrays
          let utilities = building.utilities_services || {};
          if (utilities) {
            if (utilities.water_supply && typeof utilities.water_supply === 'string') {
              utilities.water_supply = [utilities.water_supply];
            }
            if (utilities.electricity_supply && typeof utilities.electricity_supply === 'string') {
              utilities.electricity_supply = [utilities.electricity_supply];
            }
            if (utilities.telephone_connection && typeof utilities.telephone_connection === 'string') {
              utilities.telephone_connection = [utilities.telephone_connection];
            }
            if (!Array.isArray(utilities.water_supply)) utilities.water_supply = [];
            if (!Array.isArray(utilities.electricity_supply)) utilities.electricity_supply = [];
            if (!Array.isArray(utilities.telephone_connection)) utilities.telephone_connection = [];
          }

          return {
            ...building,
            utilities_services: utilities,
            floors: building.floors?.map((floor: any) => ({
              ...floor,
              rooms: floor.rooms?.map((room: any) => {
                const { length, width, ...cleanRoom } = room;
                return cleanRoom;
              }) || []
            })) || []
          };
        });
      }

      // Fields to filter out - these should only exist in the `deeds` array, not at root level
      const fieldsToRemove = [
        'deed_type', 'deed_number', 'deed_date', 'notary_name', 'notary_location',
        'certificate_number', 'certificate_date', 'certificate_notary_name', 'certificate_notary_district',
      ];
      for (const field of fieldsToRemove) {
        delete (cleanedData as any)[field];
      }

      const reportData: any = {
        ...cleanedData,
        report_type: config.reportType,
        status: submissionType === 'complete' ? 'completed' : 'draft',
        property_photos: cleanedData.property_photos || [],
      };

      // Bare land: null out building-related fields
      if (config.nullBuildings) {
        reportData.buildings = null;
        reportData.occupier_name = null;
        reportData.occupier_relationship = null;
        reportData.valuation_buildings_data = null;
        reportData.valuation_total_buildings_value = null;
      }

      console.log(`[PropertyReportForm:${reportType}] About to send to API:`, reportData);

      let savedReport;
      if (isEditMode && reportId) {
        savedReport = await reportApi.updateReport(parseInt(reportId), reportData);

        if (submissionType === 'complete') {
          setReportCreated(savedReport);
          toast.success('Report updated successfully!');
        }
      } else {
        savedReport = await reportApi.createReport(reportData);

        if (submissionType === 'complete') {
          setReportCreated(savedReport);
        }
      }

      localStorage.removeItem(config.draftKey);
      localStorage.removeItem(config.stepKey);

    } catch (error: any) {
      console.error('Error saving report:', error);

      if (error.response?.status === 401) {
        toast.error('Your session has expired. Please log in again.');
        navigate('/login');
      } else {
        const errorMessage = error.response?.data?.detail || error.message || 'Failed to save report';
        toast.error(`Error: ${errorMessage}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!reportCreated) return;

    if (!user) {
      toast.error('Session expired. Please log in again.');
      navigate('/login');
      return;
    }

    const token = authTokenStorage.getToken();
    if (!token) {
      toast.error('Session expired. Please log in again.');
      navigate('/login');
      return;
    }

    setIsGeneratingDocx(true);
    try {
      const { generateReportDocx } = await import('../services/api');
      await generateReportDocx(reportCreated.id);
      console.log(`[PropertyReportForm:${reportType}] Report generated successfully`);
    } catch (error: any) {
      console.error('Error generating DOCX:', error);

      if (error.response?.status === 401) {
        toast.error('Your session has expired. Please log in again.');
        navigate('/login');
      } else {
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
        toast.error(`Failed to generate report: ${errorMessage}`);
      }
    } finally {
      setIsGeneratingDocx(false);
    }
  };

  if (isLoadingReport) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gradient-to-br ${config.color.loadingBg}`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-16 w-16 border-b-2 ${config.color.spinner} mx-auto mb-4`} />
          <p className="text-gray-600">Loading report...</p>
        </div>
      </div>
    );
  }

  if (reportCreated) {
    return (
      <div className={`min-h-screen bg-gradient-to-br ${config.color.bg}`}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          {/* Header */}
          <div className="text-center mb-12">
            <Link
              to="/dashboard"
              className={`inline-flex items-center ${config.color.text} mb-6 transition-colors duration-200`}
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Back to Dashboard
            </Link>
          </div>

          {/* Success Card */}
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8 lg:p-12 text-center">
            {/* Success Icon */}
            <div className={`inline-flex p-6 bg-gradient-to-br ${config.color.gradient} rounded-3xl shadow-2xl ${config.color.shadow} mb-8 animate-float`}>
              <CheckCircle2 className="h-16 w-16 text-white" />
            </div>

            {/* Success Message */}
            <h1 className="text-4xl font-black gradient-text-success mb-4">
              {isEditMode ? 'Report Updated Successfully!' : 'Report Created Successfully!'}
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Your {config.label} has been {isEditMode ? 'updated' : 'generated'} and is ready for download.
            </p>

            {/* Report Details */}
            <div className={`bg-gradient-to-r ${config.color.border} rounded-2xl p-6 mb-8 text-left`}>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Report Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-semibold text-gray-700">Report ID:</span>
                  <span className="ml-2 text-gray-600">#{reportCreated.id}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Report Type:</span>
                  <span className="ml-2 text-gray-600">{config.reportLabel}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Applicant:</span>
                  <span className="ml-2 text-gray-600">{reportCreated.applicant_full_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Property:</span>
                  <span className="ml-2 text-gray-600">{reportCreated.lot_number || reportCreated.property_lot_description || 'N/A'}</span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Created:</span>
                  <span className="ml-2 text-gray-600">
                    {new Date(reportCreated.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Valuer:</span>
                  <span className="ml-2 text-gray-600">{user?.full_name}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleDownloadReport}
                disabled={isGeneratingDocx}
                className={`group inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r ${config.color.gradient} hover:${config.color.gradientHover} text-white text-lg font-bold rounded-2xl shadow-2xl ${config.color.shadow} transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isGeneratingDocx ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Generating DOCX...
                  </>
                ) : (
                  <>
                    <Download className="h-5 w-5 mr-3 group-hover:animate-bounce" />
                    Download Report (DOCX)
                  </>
                )}
              </button>

              <Link
                to="/reports/new"
                className="group inline-flex items-center justify-center px-8 py-4 bg-white/80 backdrop-blur-sm hover:bg-white text-gray-800 text-lg font-semibold rounded-2xl shadow-xl border border-gray-200/50 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98]"
              >
                <FileText className="h-5 w-5 mr-3" />
                Create Another Report
              </Link>
            </div>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-gray-200/50">
              <p className="text-sm text-gray-500">
                Report saved to your dashboard •
                <Link to="/dashboard" className={`ml-1 ${config.color.text} font-medium`}>
                  View all reports
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to={isEditMode ? "/dashboard" : "/reports/new"}
                className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                {isEditMode ? 'Back to Dashboard' : 'Back to Report Selection'}
              </Link>

              {isEditMode && (
                <span className={`px-3 py-1 ${config.color.editBadgeBg} ${config.color.editBadgeText} text-sm font-medium rounded-full`}>
                  Editing Report #{reportId}
                </span>
              )}
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">
                {isEditMode ? `Editing ${config.label} as` : `Creating ${config.label} as`}
              </p>
              <p className="font-semibold text-gray-900">{user?.full_name}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Step Form */}
      <MultiStepForm
        onSubmit={handleFormSubmit}
        isSubmitting={isSubmitting}
        user={user}
        isEditMode={isEditMode}
        reportId={reportId ? parseInt(reportId) : undefined}
        initialData={existingReport || undefined}
        reportType={config.nullBuildings ? "bare_land" : undefined}
      />
    </div>
  );
};

export default PropertyReportForm;
