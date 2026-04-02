/**
 * VehicleStepForm - Main 5-step form for vehicle valuation reports
 *
 * Steps:
 * 1. Basic Info (Purpose, Requested By, Dates, Folio, Inspection Place)
 * 2. Vehicle Photos (Max 5, drag-drop + click upload)
 * 3. Book Images + OCR (Max 5, "Extract Data" button — auto-triggers spec enrichment)
 * 4. Book Data Review (OCR auto-fills here; AI specs auto-fill gaps; variant field)
 * 5. Features/Assessment + Valuation (Office/Private question before valuation)
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  Save,
  FileText,
  Car,
  Camera,
  BookOpen,
  ClipboardList,
  DollarSign,
  Loader2,
  Library,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { VehicleBasicInfoStep } from './vehicle/VehicleBasicInfoStep';
import { VehiclePhotosStep } from './vehicle/VehiclePhotosStep';
import { VehicleBookOCRStep } from './vehicle/VehicleBookOCRStep';
import { VehicleDescriptionStep } from './vehicle/VehicleDescriptionStep';
import { VehicleFeaturesValuationStep } from './vehicle/VehicleFeaturesValuationStep';
import { vehicleApi, reportApi } from '../services/api';
import type { Vehicle, VehicleCreate, Report, ReportCreate } from '../types';

interface VehicleStepFormProps {
  mode: 'create' | 'edit';
  reportId?: number;
  vehicleId?: number;
  isMultiPropertyContext?: boolean;
  initialData?: any;
  onSaveComplete?: (vehicle: Vehicle) => void;
  onSaveProperty?: (data: any) => void;
  onFinishProperty?: (data: any) => void;
  onCancel?: () => void;
}

const STEPS = [
  { id: 1, title: 'Basic Info', icon: FileText },
  { id: 2, title: 'Vehicle Photos', icon: Camera },
  { id: 3, title: 'Book Images & OCR', icon: BookOpen },
  { id: 4, title: 'Book Data Review', icon: ClipboardList },
  { id: 5, title: 'Features & Valuation', icon: DollarSign },
];

const TOTAL_STEPS = 5;

export const VehicleStepForm: React.FC<VehicleStepFormProps> = ({
  mode,
  reportId,
  vehicleId,
  isMultiPropertyContext = false,
  initialData,
  onSaveComplete,
  onSaveProperty,
  onFinishProperty,
  onCancel,
}) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(isMultiPropertyContext ? 2 : 1);
  const [isSaving, setIsSaving] = useState(false);
  const [isSpecEnriching, setIsSpecEnriching] = useState(false);
  const [isLoading, setIsLoading] = useState(mode === 'edit');
  const [existingReport, setExistingReport] = useState<Report | null>(null);
  const [existingVehicle, setExistingVehicle] = useState<Vehicle | null>(null);
  const [saveToLibrary, setSaveToLibrary] = useState(false);

  const methods = useForm({
    defaultValues: {
      // Report-level fields (Step 1)
      valuation_purpose: '',
      applicant_title: '',
      applicant_full_name: '',
      report_date: '',
      inspection_date: '',
      folio_number: '',
      inspection_place: '',
      is_office_use: false,

      // Vehicle fields
      status: 'draft',
      vehicle_type: 'car',
      registration_number: '',
      provincial_council: '',
      class_of_vehicle: '',
      body_colour: '',
      chassis_number: '',
      engine_number: '',
      vehicle_status: '',
      country_of_origin: '',
      make: '',
      model: '',
      date_of_first_registration: '',
      year_of_manufacture: undefined as number | undefined,
      cylinder_capacity: undefined as number | undefined,
      fuel_type: '',
      mileage: undefined as number | undefined,
      mileage_unit: 'km',

      // Engine & Transmission
      engine_type: '',
      transmission: '',
      wheel_drive: '',

      // Conditions
      running_condition: '',
      clutch_status: '',
      engine_condition: '',
      gear_box_condition: '',
      differential_status: '',
      gear_selection: '',
      body_condition: '',
      chassis_condition: '',
      upholstery_condition: '',
      underside_condition: '',

      // Parts
      body_parts_status: '',
      engine_parts_status: '',
      accessories_status: '',

      // Fuel
      fuel_consumption: undefined as number | undefined,
      fuel_consumption_unit: 'km/L',

      // Brakes
      foot_brake_condition: '',
      disc_brake_available: false,
      parking_brake_condition: '',
      abs_available: false,

      // Features
      features: {
        air_condition: false,
        dual_air_condition: false,
        power_mirror: false,
        power_window: false,
        power_steering: false,
        airbag: false,
        num_airbags: 0,
        seats: undefined as number | undefined,
        doors: undefined as number | undefined,
      },

      // Suspension
      suspension: {
        front: '',
        rear: '',
      },

      // Tyres
      tyres: {
        front: { brand: '', size: '', tread_percent: undefined as number | undefined, condition: '' },
        rear: { brand: '', size: '', tread_percent: undefined as number | undefined, condition: '' },
        spare_available: false,
        need_replacement: false,
        rear_type: 'single' as 'single' | 'dual',
      },

      // Electrical
      electrical: {
        starter: false,
        horn: false,
        wiper: false,
        battery_condition: '',
      },

      // Lights
      lights: {
        head: false,
        dim: false,
        signal: false,
        parking: false,
        reverse: false,
        meter: false,
      },

      // History
      has_accidents: false,
      has_repairs: false,
      needs_repairs_within_year: false,
      body_parts_replaced: false,

      // Valuation
      purchase_price: undefined as number | undefined,
      brand_new_price: undefined as number | undefined,
      market_value: undefined as number | undefined,
      forced_sale_value: undefined as number | undefined,
      valuation_summary: '',

      // Office data
      office_data: {
        civil_no: '',
        military_no: '',
        approval_position: '',
      },

      // Past valuations
      past_valuations: [] as any[],

      // Photos
      vehicle_photos: [] as any[],
      book_images: [] as any[],

      // Variant & enrichment data
      variant: '',
      book_data: undefined as any,
      spec_data: undefined as any,
      spec_source: undefined as any,
      spec_confidence: undefined as any,
    },
  });

  const { handleSubmit, setValue, watch, reset } = methods;

  // Load existing data for edit mode
  useEffect(() => {
    const loadData = async () => {
      // Handle multi-property context with initialData
      if (isMultiPropertyContext && initialData && Object.keys(initialData).length > 0) {
        setIsLoading(true);
        try {
          // Merge initialData into form
          Object.keys(initialData).forEach((key) => {
            if (initialData[key] !== undefined && initialData[key] !== null) {
              setValue(key as any, initialData[key]);
            }
          });
        } finally {
          setIsLoading(false);
        }
        return;
      }

      // Handle standalone edit mode
      if (mode === 'edit' && reportId) {
        try {
          setIsLoading(true);
          const report = await reportApi.getReport(reportId);
          setExistingReport(report);

          // Set report-level fields
          reset({
            ...methods.getValues(),
            valuation_purpose: report.valuation_purpose || '',
            applicant_title: report.applicant_title || '',
            applicant_full_name: report.applicant_full_name || '',
            report_date: report.report_date || '',
            inspection_date: report.inspection_date || '',
            folio_number: report.folio_number || '',
            inspection_place: report.inspection_place || '',
            is_office_use: report.is_office_use || false,
          });

          // Load vehicle data if available — fall back to primary_vehicle_id from report
          const resolvedVehicleId = vehicleId ?? report.primary_vehicle_id;
          if (resolvedVehicleId) {
            const vehicle = await vehicleApi.getVehicle(resolvedVehicleId);
            setExistingVehicle(vehicle);

            // Merge vehicle data into form
            Object.keys(vehicle).forEach((key) => {
              if ((vehicle as any)[key] !== undefined && (vehicle as any)[key] !== null) {
                setValue(key as any, (vehicle as any)[key]);
              }
            });
          }
        } catch (error) {
          console.error('Error loading data:', error);
          toast.error('Failed to load existing data');
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadData();
  }, [mode, reportId, vehicleId, reset, setValue, isMultiPropertyContext, initialData]);

  // Handle step navigation
  const goToStep = (step: number) => {
    const minStep = isMultiPropertyContext ? 2 : 1;
    if (step >= minStep && step <= TOTAL_STEPS) {
      setCurrentStep(step);
    }
  };

  const nextStep = () => goToStep(currentStep + 1);
  const prevStep = () => goToStep(currentStep - 1);

  // Handle form submission (save draft or complete)
  const onSubmit = async (data: any, status: 'draft' | 'completed' = 'draft') => {
    setIsSaving(true);
    try {
      // Prepare vehicle data
      const vehicleData: VehicleCreate = {
        status,
        is_template: saveToLibrary && !isMultiPropertyContext, // Only save to library for standalone vehicles
        vehicle_type: data.vehicle_type,
        registration_number: data.registration_number,
        provincial_council: data.provincial_council,
        class_of_vehicle: data.class_of_vehicle,
        body_colour: data.body_colour,
        chassis_number: data.chassis_number,
        engine_number: data.engine_number,
        vehicle_status: data.vehicle_status,
        country_of_origin: data.country_of_origin,
        make: data.make,
        model: data.model,
        date_of_first_registration: data.date_of_first_registration,
        year_of_manufacture: data.year_of_manufacture,
        cylinder_capacity: data.cylinder_capacity,
        fuel_type: data.fuel_type,
        mileage: data.mileage,
        mileage_unit: data.mileage_unit,
        engine_type: data.engine_type,
        transmission: data.transmission,
        wheel_drive: data.wheel_drive,
        running_condition: data.running_condition,
        clutch_status: data.clutch_status,
        engine_condition: data.engine_condition,
        gear_box_condition: data.gear_box_condition,
        differential_status: data.differential_status,
        gear_selection: data.gear_selection,
        body_condition: data.body_condition,
        chassis_condition: data.chassis_condition,
        upholstery_condition: data.upholstery_condition,
        underside_condition: data.underside_condition,
        body_parts_status: data.body_parts_status,
        engine_parts_status: data.engine_parts_status,
        accessories_status: data.accessories_status,
        fuel_consumption: data.fuel_consumption,
        fuel_consumption_unit: data.fuel_consumption_unit,
        foot_brake_condition: data.foot_brake_condition,
        disc_brake_available: data.disc_brake_available,
        parking_brake_condition: data.parking_brake_condition,
        abs_available: data.abs_available,
        features: data.features,
        suspension: data.suspension,
        tyres: data.tyres,
        electrical: data.electrical,
        lights: data.lights,
        has_accidents: data.has_accidents,
        has_repairs: data.has_repairs,
        needs_repairs_within_year: data.needs_repairs_within_year,
        body_parts_replaced: data.body_parts_replaced,
        purchase_price: data.purchase_price,
        brand_new_price: data.brand_new_price,
        market_value: data.market_value,
        forced_sale_value: data.forced_sale_value,
        valuation_summary: data.valuation_summary,
        office_data: data.is_office_use ? data.office_data : undefined,
        past_valuations: data.is_office_use ? data.past_valuations : undefined,
        vehicle_photos: data.vehicle_photos,
        book_images: [], // Clear book images after OCR
        variant: data.variant || undefined,
        book_data: data.book_data || undefined,
        spec_data: data.spec_data || undefined,
        spec_source: data.spec_source || undefined,
        spec_confidence: data.spec_confidence || undefined,
      };

      // In multi-property context, call the parent callbacks instead of API
      if (isMultiPropertyContext) {
        if (status === 'completed' && onFinishProperty) {
          onFinishProperty(vehicleData);
        } else if (onSaveProperty) {
          onSaveProperty(vehicleData);
        }
        setIsSaving(false);
        return;
      }

      let vehicle: Vehicle;
      let report: Report;

      if (mode === 'edit' && existingVehicle) {
        // Update existing vehicle
        vehicle = await vehicleApi.updateVehicle(existingVehicle.id, vehicleData);
        toast.success('Vehicle updated successfully');
      } else {
        // Create new vehicle
        vehicle = await vehicleApi.createVehicle(vehicleData);
        toast.success('Vehicle created successfully');
      }

      // Handle report creation/update if not in multi-property context
      if (mode === 'edit' && existingReport) {
        // Update existing report
        const reportData: Partial<ReportCreate> = {
          report_type: 'vehicle',
          status,
          valuation_purpose: data.valuation_purpose,
          applicant_title: data.applicant_title,
          applicant_full_name: data.applicant_full_name,
          report_date: data.report_date,
          inspection_date: data.inspection_date,
          folio_number: data.folio_number,
          inspection_place: data.inspection_place,
          is_office_use: data.is_office_use,
          primary_vehicle_id: vehicle.id,
          vehicle_count: 1,
        };
        report = await reportApi.updateReport(existingReport.id, reportData);
      } else {
        // Create new report
        const reportData: ReportCreate = {
          report_type: 'vehicle',
          status,
          valuation_purpose: data.valuation_purpose,
          applicant_title: data.applicant_title,
          applicant_full_name: data.applicant_full_name,
          report_date: data.report_date,
          inspection_date: data.inspection_date,
          folio_number: data.folio_number,
          inspection_place: data.inspection_place,
          is_office_use: data.is_office_use,
          primary_vehicle_id: vehicle.id,
          vehicle_count: 1,
        };
        report = await reportApi.createReport(reportData);

        // Add vehicle to report
        await vehicleApi.addToReport(report.id, vehicle.id);
      }

      // If completing, start async DOCX generation and pass job ID to dashboard
      let pendingJobId: string | undefined;
      if (status === 'completed') {
        try {
          const job = await reportApi.generateReportAsync(report.id);
          pendingJobId = job.id;
        } catch {
          // Generation start failed — still navigate, user can download manually
        }
      }

      navigate('/dashboard', pendingJobId ? { state: { pendingJobId } } : undefined);

      // Legacy callback support
      if (onSaveComplete) {
        onSaveComplete(vehicle);
      }
    } catch (error: any) {
      console.error('Error saving vehicle:', error);
      toast.error(error.message || 'Failed to save vehicle');
    } finally {
      setIsSaving(false);
    }
  };

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <VehicleBasicInfoStep />;
      case 2:
        return <VehiclePhotosStep />;
      case 3:
        return (
          <VehicleBookOCRStep
            onEnrichmentStart={() => setIsSpecEnriching(true)}
            onEnrichmentComplete={() => setIsSpecEnriching(false)}
          />
        );
      case 4:
        return <VehicleDescriptionStep />;
      case 5:
        return <VehicleFeaturesValuationStep />;
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        <span className="ml-2 text-gray-600">Loading...</span>
      </div>
    );
  }

  return (
    <FormProvider {...methods}>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30">
        {/* Step Progress Indicator */}
        <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-sm border-b border-gray-200/50 px-4 py-3">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between">
              {STEPS.filter((step) => !isMultiPropertyContext || step.id !== 1).map((step, index) => {
                const StepIcon = step.icon;
                const isActive = step.id === currentStep;
                const isCompleted = step.id < currentStep;

                return (
                  <React.Fragment key={step.id}>
                    <button
                      type="button"
                      onClick={() => goToStep(step.id)}
                      className={`flex flex-col items-center gap-1 transition-all ${
                        isActive
                          ? 'text-emerald-600'
                          : isCompleted
                          ? 'text-emerald-500'
                          : 'text-gray-400'
                      }`}
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                          isActive
                            ? 'border-emerald-500 bg-emerald-50'
                            : isCompleted
                            ? 'border-emerald-500 bg-emerald-500 text-white'
                            : 'border-gray-300 bg-white'
                        }`}
                      >
                        {isSpecEnriching && step.id === 4 ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <StepIcon className="w-5 h-5" />
                        )}
                      </div>
                      <span className="text-xs font-medium hidden sm:block">{step.title}</span>
                    </button>
                    {index < STEPS.filter((s) => !isMultiPropertyContext || s.id !== 1).length - 1 && (
                      <div
                        className={`flex-1 h-0.5 mx-2 ${
                          step.id < currentStep ? 'bg-emerald-500' : 'bg-gray-200'
                        }`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        </div>

        {/* Form Content */}
        <div className="max-w-4xl mx-auto px-4 md:px-6 py-4 md:py-6">
          <form onSubmit={handleSubmit((data) => onSubmit(data, 'draft'))}>
            {/* Step Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                <Car className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-800">
                  Step {currentStep}: {STEPS.find((s) => s.id === currentStep)?.title}
                </h2>
                <p className="text-sm text-gray-500">
                  {currentStep === 1 && 'Enter basic information about the valuation request'}
                  {currentStep === 2 && 'Upload up to 5 photos of the vehicle'}
                  {currentStep === 3 && 'Upload vehicle book images for OCR extraction'}
                  {currentStep === 4 && 'Review and edit vehicle identification and registration details'}
                  {currentStep === 5 && 'Complete features assessment and valuation'}
                </p>
              </div>
            </div>

            {/* Step Content */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200/50 p-4 md:p-6 mb-4 md:mb-6">
              {renderStepContent()}
            </div>

            {/* Save to Library Option (Step 6 only, not in multi-property context) */}
            {currentStep === 5 && !isMultiPropertyContext && (
              <div className="bg-cyan-50 border border-cyan-200 rounded-xl p-4 mb-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={saveToLibrary}
                    onChange={(e) => setSaveToLibrary(e.target.checked)}
                    className="w-5 h-5 rounded border-cyan-300 text-cyan-600 focus:ring-cyan-500"
                  />
                  <div className="flex items-center gap-2">
                    <Library className="w-5 h-5 text-cyan-600" />
                    <div>
                      <span className="font-medium text-gray-900">Save to Vehicle Library</span>
                      <p className="text-sm text-gray-500">
                        Reuse this vehicle's data for future reports
                      </p>
                    </div>
                  </div>
                </label>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between">
              <div>
                {currentStep > (isMultiPropertyContext ? 2 : 1) && (
                  <button
                    type="button"
                    onClick={prevStep}
                    className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5" />
                    Previous
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {/* Save Draft Button */}
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  {isSaving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Save Draft
                </button>

                {/* Next/Complete Button */}
                {currentStep < TOTAL_STEPS ? (
                  <button
                    type="button"
                    onClick={nextStep}
                    className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-xl hover:from-emerald-600 hover:to-emerald-700 transition-all shadow-sm"
                  >
                    Next
                    <ChevronRight className="w-5 h-5" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSubmit((data) => onSubmit(data, 'completed'))}
                    disabled={isSaving}
                    className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-xl hover:from-emerald-600 hover:to-emerald-700 transition-all shadow-sm disabled:opacity-50"
                  >
                    {isSaving ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <FileText className="w-4 h-4" />
                    )}
                    Complete Report
                  </button>
                )}
              </div>
            </div>

            {/* Cancel Button (for multi-property context) */}
            {isMultiPropertyContext && onCancel && (
              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={onCancel}
                  className="text-gray-500 hover:text-gray-700 text-sm"
                >
                  Cancel
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </FormProvider>
  );
};

export default VehicleStepForm;
