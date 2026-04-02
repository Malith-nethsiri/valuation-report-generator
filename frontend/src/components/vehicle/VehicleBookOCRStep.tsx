/**
 * VehicleBookOCRStep - Step 3 of Vehicle Report Form
 *
 * Upload vehicle book/registration document images for OCR extraction:
 * - Upload up to 5 book images
 * - "Extract Data" button triggers OCR
 * - Loading spinner during extraction
 * - Auto-populates description fields on success
 */

import React, { useState, useCallback } from 'react';
import { useFormContext } from 'react-hook-form';
import {
  BookOpen,
  Upload,
  X,
  Loader2,
  Sparkles,
  CheckCircle,
  AlertCircle,
  FileText,
  Image as ImageIcon,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { ocrApi, vehicleApi } from '../../services/api';
import type { VehiclePhoto } from '../../types';

const MAX_BOOK_IMAGES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface VehicleBookOCRStepProps {
  onEnrichmentStart?: () => void;
  onEnrichmentComplete?: () => void;
}

export const VehicleBookOCRStep: React.FC<VehicleBookOCRStepProps> = ({
  onEnrichmentStart,
  onEnrichmentComplete,
}) => {
  const { watch, setValue, getValues } = useFormContext();
  const [isUploading, setIsUploading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [extractionStatus, setExtractionStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [extractedFields, setExtractedFields] = useState<string[]>([]);

  const bookImages: VehiclePhoto[] = watch('book_images') || [];

  // Generate unique ID
  const generateId = () => `book-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Process file to base64
  const processFile = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  // Convert base64 to File object for OCR API
  const base64ToFile = (base64: string, filename: string): File => {
    const arr = base64.split(',');
    const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  };

  // Handle file selection
  const handleFileSelect = useCallback(async (files: FileList | File[]) => {
    if (bookImages.length >= MAX_BOOK_IMAGES) {
      toast.error(`Maximum ${MAX_BOOK_IMAGES} book images allowed`);
      return;
    }

    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
        toast.error(`${file.name} is not a valid file type`);
        return false;
      }
      if (file.size > MAX_FILE_SIZE) {
        toast.error(`${file.name} exceeds 10MB limit`);
        return false;
      }
      return true;
    });

    const slotsAvailable = MAX_BOOK_IMAGES - bookImages.length;
    const filesToProcess = validFiles.slice(0, slotsAvailable);

    if (filesToProcess.length === 0) return;

    setIsUploading(true);
    const toastId = toast.loading(`Uploading ${filesToProcess.length} image(s)...`);

    try {
      const newImages: VehiclePhoto[] = await Promise.all(
        filesToProcess.map(async (file, index) => {
          const imageData = await processFile(file);
          return {
            id: generateId(),
            image_data: imageData,
            caption: file.name,
            order: bookImages.length + index + 1,
          };
        })
      );

      setValue('book_images', [...bookImages, ...newImages]);
      setExtractionStatus('idle'); // Reset extraction status when new images added
      toast.success(`${newImages.length} image(s) uploaded`, { id: toastId });
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload images', { id: toastId });
    } finally {
      setIsUploading(false);
    }
  }, [bookImages, setValue]);

  // Handle drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('image/') || file.type === 'application/pdf'
    );

    if (files.length === 0) {
      toast.error('Please drop only image or PDF files');
      return;
    }

    handleFileSelect(files);
  }, [handleFileSelect]);

  // Handle file input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files);
    }
    e.target.value = '';
  };

  // Delete book image
  const handleDeleteImage = (imageId: string) => {
    const updated = bookImages.filter(img => img.id !== imageId);
    setValue('book_images', updated);
    setExtractionStatus('idle');
    toast.success('Image removed');
  };

  // Extract data using OCR
  const handleExtractData = async () => {
    if (bookImages.length === 0) {
      toast.error('Please upload at least one book image');
      return;
    }

    setIsExtracting(true);
    setExtractionStatus('idle');
    const toastId = toast.loading('Extracting vehicle data...');

    try {
      // Convert base64 images to File objects
      const files = bookImages.map((img, index) =>
        base64ToFile(img.image_data, `book_image_${index + 1}.jpg`)
      );

      // Call OCR API with vehicle_book type
      const result = await ocrApi.extractData(files, 'vehicle_book');

      if (result && result.data && result.data.extracted_data) {
        const data = result.data.extracted_data;
        const fieldsSet: string[] = [];

        // Map extracted fields to form fields
        const fieldMappings: Record<string, string> = {
          registration_number: 'registration_number',
          provincial_council: 'provincial_council',
          class_of_vehicle: 'class_of_vehicle',
          body_colour: 'body_colour',
          chassis_number: 'chassis_number',
          engine_number: 'engine_number',
          vehicle_status: 'vehicle_status',
          country_of_origin: 'country_of_origin',
          make: 'make',
          model: 'model',
          date_of_first_registration: 'date_of_first_registration',
          year_of_manufacture: 'year_of_manufacture',
          cylinder_capacity: 'cylinder_capacity',
          fuel_type: 'fuel_type',
          engine_type: 'engine_type',
          transmission: 'transmission',
        };

        // Set extracted values
        Object.entries(fieldMappings).forEach(([apiField, formField]) => {
          if (data[apiField] && data[apiField] !== null) {
            const currentValue = getValues(formField);
            // Only set if current value is empty
            if (!currentValue) {
              setValue(formField, data[apiField]);
              fieldsSet.push(apiField.replace(/_/g, ' '));
            }
          }
        });

        // Save full OCR output as book_data (preserves owner info, weights, dimensions, license dates)
        const bookDataFields = [
          'owner_name', 'owner_nic', 'owner_address',
          'revenue_license_valid_until', 'insurance_valid_until', 'last_transferred_date',
          'unladen_weight', 'gross_weight', 'wheelbase',
          'overall_length', 'overall_width', 'overall_height', 'number_of_axles',
        ];
        const bookData: Record<string, unknown> = {};
        bookDataFields.forEach(field => {
          if (data[field] != null) bookData[field] = data[field];
        });
        if (result.data.overall_confidence != null) {
          bookData.ocr_confidence = result.data.overall_confidence;
        }
        if (result.data.metadata?.parsing_notes) {
          bookData.extraction_notes = result.data.metadata.parsing_notes;
        }
        if (Object.keys(bookData).length > 0) {
          setValue('book_data', bookData);
        }

        // Auto-enrich manufacturer specs in background using OCR-extracted identity
        const vehicleId = getValues('id');
        const make = data['make'] || getValues('make');
        const model = data['model'] || getValues('model');
        const year = data['year_of_manufacture'] || getValues('year_of_manufacture');

        if (vehicleId && make && model && year) {
          onEnrichmentStart?.();
          vehicleApi.enrichSpecs(vehicleId)
            .then((enrichResult) => {
              const spec = enrichResult.spec_data;
              if (!spec || spec.confidence === 0.0) {
                toast.error('Could not auto-load manufacturer specs — please enter manually');
                return;
              }
              // Fill only empty fields — OCR values take priority
              if (!getValues('engine_type') && spec.engine_type) setValue('engine_type', spec.engine_type);
              if (!getValues('transmission') && spec.transmission) setValue('transmission', spec.transmission);
              if (!getValues('wheel_drive') && spec.wheel_drive) setValue('wheel_drive', spec.wheel_drive);
              if (!getValues('fuel_type') && spec.fuel_type) setValue('fuel_type', spec.fuel_type);
              if (!getValues('cylinder_capacity') && spec.displacement_cc) setValue('cylinder_capacity', spec.displacement_cc);
              if (!getValues('fuel_consumption') && spec.fuel_economy_kmpl) {
                setValue('fuel_consumption', spec.fuel_economy_kmpl);
                setValue('fuel_consumption_unit', 'km/L');
              }
              if (spec.standard_features) {
                const sf = spec.standard_features;
                const cf = getValues('features') || {};
                setValue('features', {
                  ...cf,
                  air_condition: cf.air_condition || sf.air_condition || false,
                  dual_air_condition: cf.dual_air_condition || sf.dual_air_condition || false,
                  power_window: cf.power_window || sf.power_window || false,
                  power_steering: cf.power_steering || sf.power_steering || false,
                  airbag: cf.airbag || (sf.airbag_count != null && sf.airbag_count > 0) || false,
                  num_airbags: cf.num_airbags || sf.airbag_count || 0,
                });
                if (!getValues('abs_available') && sf.abs_standard) setValue('abs_available', true);
                if (!getValues('features.seats') && spec.seating_capacity) setValue('features.seats', spec.seating_capacity);
                if (!getValues('features.doors') && spec.doors) setValue('features.doors', spec.doors);
              }
              setValue('spec_data', spec);
              setValue('spec_source', 'ai_claude');
              setValue('spec_confidence', spec.confidence);
            })
            .catch(() => {
              toast.error('Could not auto-load manufacturer specs — please enter manually');
            })
            .finally(() => {
              onEnrichmentComplete?.();
            });
        }

        setExtractedFields(fieldsSet);
        setExtractionStatus('success');

        if (fieldsSet.length > 0) {
          toast.success(`Extracted ${fieldsSet.length} fields from vehicle book`, { id: toastId });
        } else {
          toast.success('OCR completed - no new data to extract', { id: toastId });
        }
      } else {
        setExtractionStatus('error');
        toast.error('No data could be extracted', { id: toastId });
      }
    } catch (error: any) {
      console.error('OCR extraction error:', error);
      setExtractionStatus('error');
      toast.error(error.message || 'Failed to extract data', { id: toastId });
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
        <BookOpen className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-medium text-blue-900">Vehicle Book / Registration Document</h3>
          <p className="text-sm text-blue-700 mt-1">
            Upload images of the vehicle registration book (CR Book) to automatically extract vehicle details.
            The AI will attempt to read registration number, make, model, engine details, and more.
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300
          ${isDragOver
            ? 'border-emerald-500 bg-emerald-50'
            : 'border-gray-300 hover:border-emerald-400 bg-gray-50/50'
          }
          ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}
        `}
      >
        <input
          type="file"
          accept="image/*,application/pdf"
          multiple
          onChange={handleInputChange}
          disabled={isUploading || bookImages.length >= MAX_BOOK_IMAGES}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          id="book-image-upload"
        />

        <div className="space-y-4">
          <div className={`
            mx-auto w-16 h-16 rounded-2xl flex items-center justify-center transition-all
            ${isDragOver ? 'bg-emerald-500 text-white scale-110' : 'bg-gray-200 text-gray-500'}
          `}>
            {isUploading ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <FileText className="w-8 h-8" />
            )}
          </div>

          <div>
            {isUploading ? (
              <p className="text-gray-600 font-medium">Uploading images...</p>
            ) : bookImages.length >= MAX_BOOK_IMAGES ? (
              <p className="text-gray-600 font-medium">Maximum images reached</p>
            ) : (
              <>
                <p className="text-gray-700 font-medium">
                  Upload vehicle book images
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  PNG, JPG, or PDF up to 10MB • {MAX_BOOK_IMAGES - bookImages.length} slot{MAX_BOOK_IMAGES - bookImages.length !== 1 ? 's' : ''} remaining
                </p>
              </>
            )}
          </div>

          {!isUploading && bookImages.length < MAX_BOOK_IMAGES && (
            <label
              htmlFor="book-image-upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              Select Images
            </label>
          )}
        </div>
      </div>

      {/* Image Preview Grid */}
      {bookImages.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {bookImages.map((img, index) => (
            <div
              key={img.id}
              className="relative group aspect-[4/3] bg-gray-100 rounded-lg overflow-hidden border border-gray-200"
            >
              <img
                src={img.image_data}
                alt={`Book image ${index + 1}`}
                className="w-full h-full object-cover"
              />

              {/* Order Badge */}
              <div className="absolute top-1 left-1 w-6 h-6 bg-black/70 text-white rounded-full flex items-center justify-center text-xs font-medium">
                {index + 1}
              </div>

              {/* Delete Button */}
              <button
                type="button"
                onClick={() => handleDeleteImage(img.id)}
                className="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Extract Data Button */}
      {bookImages.length > 0 && (
        <div className="flex flex-col items-center gap-4 p-6 bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl border border-emerald-100">
          <button
            type="button"
            onClick={handleExtractData}
            disabled={isExtracting}
            className={`
              flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-white
              transition-all duration-300 shadow-lg
              ${isExtracting
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 hover:shadow-xl transform hover:scale-[1.02]'
              }
            `}
          >
            {isExtracting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Extracting Data...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Extract Data from Book
              </>
            )}
          </button>

          <p className="text-sm text-gray-600 text-center max-w-md">
            AI will analyze the uploaded images and automatically fill in vehicle details in the next step
          </p>
        </div>
      )}

      {/* Extraction Status */}
      {extractionStatus === 'success' && (
        <div className="flex items-start gap-3 p-4 bg-green-50 rounded-xl border border-green-200">
          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-green-800">Data extracted successfully!</p>
            {extractedFields.length > 0 && (
              <p className="text-sm text-green-700 mt-1">
                Fields extracted: {extractedFields.join(', ')}
              </p>
            )}
            <p className="text-sm text-green-600 mt-2">
              Proceed to the next step to review and edit the extracted data.
            </p>
          </div>
        </div>
      )}

      {extractionStatus === 'error' && (
        <div className="flex items-start gap-3 p-4 bg-red-50 rounded-xl border border-red-200">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Extraction failed</p>
            <p className="text-sm text-red-700 mt-1">
              Could not extract data from the uploaded images. Please ensure the images are clear and try again, or enter the details manually in the next step.
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {bookImages.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <ImageIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>No book images uploaded yet</p>
          <p className="text-sm mt-1">
            Upload vehicle book images to extract registration details automatically
          </p>
        </div>
      )}

      {/* Tips */}
      <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
        <p className="text-sm text-amber-800 font-medium mb-2">
          Tips for Better OCR Results
        </p>
        <ul className="text-sm text-amber-700 space-y-1">
          <li>• Ensure good lighting and no shadows</li>
          <li>• Capture the entire page in frame</li>
          <li>• Avoid blurry or skewed images</li>
          <li>• Include all pages with relevant information</li>
          <li>• Book images are not included in the final report</li>
        </ul>
      </div>
    </div>
  );
};

export default VehicleBookOCRStep;
