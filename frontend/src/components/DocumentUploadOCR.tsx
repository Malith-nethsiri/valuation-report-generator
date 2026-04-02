import React, { useState, useRef } from 'react';
import { Upload, FileImage, FileText, X, Loader2, CheckCircle2, AlertCircle, Eye } from 'lucide-react';
import { Button } from './Button';
import { Label } from './Label';
import { cleanOCRText, formatBoundaryDescription, smartTitleCase } from '../utils/textFormatter';
import { authTokenStorage } from '../utils/secureStorage';
import { getCSRFToken } from '../utils/csrf';

interface OCRResult {
  success: boolean;
  extracted_data?: any;
  overall_confidence?: number;
  metadata?: any;
  error?: string;
}

interface DocumentUploadOCRProps {
  onDataExtracted: (data: any, confidence: number) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  documentTypeHint?: 'survey_plan' | 'deed' | 'title_certificate';
}

export function DocumentUploadOCR({
  onDataExtracted,
  onError,
  disabled = false,
  documentTypeHint,
}: DocumentUploadOCRProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedResult, setProcessedResult] = useState<OCRResult | null>(null);
  const [showPreviews, setShowPreviews] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    // Validate each file — accept images and PDFs
    const allowedExtensions = ['.jpg', '.jpeg', '.jfif', '.png', '.webp', '.pdf'];
    for (const file of files) {
      const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
      const isImage = file.type.startsWith('image/');
      const isPdf = file.type === 'application/pdf' || ext === '.pdf';
      if (!isImage && !isPdf && !allowedExtensions.includes(ext)) {
        onError?.(`File "${file.name}" is not supported. Please select images (JPEG, PNG, WEBP) or PDF files.`);
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        onError?.(`File "${file.name}" is too large. Each file must be less than 10MB`);
        return;
      }
    }

    setSelectedFiles(files);
    setProcessedResult(null);

    // Create preview URLs — images get DataURL for preview, PDFs get a sentinel marker
    const urls: string[] = new Array(files.length).fill('');
    let loadedCount = 0;

    files.forEach((file, index) => {
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
      if (isPdf) {
        urls[index] = '[pdf]';
        loadedCount++;
        if (loadedCount === files.length) setPreviewUrls([...urls]);
      } else {
        const reader = new FileReader();
        reader.onloadend = () => {
          urls[index] = reader.result as string;
          loadedCount++;
          if (loadedCount === files.length) setPreviewUrls([...urls]);
        };
        reader.readAsDataURL(file);
      }
    });
  };

  const handleClearFile = () => {
    setSelectedFiles([]);
    setPreviewUrls([]);
    setProcessedResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatOCRData = (data: any): any => {
    const formatted = { ...data };

    // Apply smartTitleCase to all text fields from OCR
    // This converts ALL CAPS to proper Title Case while preserving:
    // - Initials (A.D.SILVA → A.D.Silva)
    // - Acronyms (LLC, PO, NE, SW, etc.)
    // - Hyphenated names (PERERA-SILVA → Perera-Silva)

    // Location fields
    if (formatted.property_village) {
      formatted.property_village = smartTitleCase(formatted.property_village);
    }
    if (formatted.village) {
      formatted.village = smartTitleCase(formatted.village);
    }
    if (formatted.gn_division_name) {
      formatted.gn_division_name = smartTitleCase(formatted.gn_division_name);
    }
    if (formatted.ds_division) {
      formatted.ds_division = smartTitleCase(formatted.ds_division);
    }
    if (formatted.district) {
      formatted.district = smartTitleCase(formatted.district);
    }
    if (formatted.province) {
      formatted.province = smartTitleCase(formatted.province);
    }
    if (formatted.korale) {
      formatted.korale = smartTitleCase(formatted.korale);
    }
    if (formatted.pradeshiya_sabha) {
      formatted.pradeshiya_sabha = smartTitleCase(formatted.pradeshiya_sabha);
    }

    // Plan-related fields
    if (formatted.licensed_surveyor_name) {
      formatted.licensed_surveyor_name = smartTitleCase(cleanOCRText(formatted.licensed_surveyor_name));
    }
    if (formatted.land_traditional_name) {
      // Force transformation by converting to uppercase first to ensure smartTitleCase always processes it
      const cleanedName = cleanOCRText(formatted.land_traditional_name);
      formatted.land_traditional_name = smartTitleCase(cleanedName.toUpperCase());
    }

    // Deed-related fields
    if (formatted.deeds && Array.isArray(formatted.deeds)) {
      formatted.deeds = formatted.deeds.map((deed: any) => ({
        ...deed,
        deed_type: deed.deed_type ? smartTitleCase(deed.deed_type) : deed.deed_type,
        notary_name: deed.notary_name ? smartTitleCase(deed.notary_name) : deed.notary_name,
        notary_location: deed.notary_location ? smartTitleCase(deed.notary_location) : deed.notary_location,
      }));
    }

    // Boundary descriptions
    if (formatted.boundaries) {
      Object.keys(formatted.boundaries).forEach(direction => {
        if (formatted.boundaries[direction]?.description) {
          formatted.boundaries[direction].description = smartTitleCase(
            formatBoundaryDescription(formatted.boundaries[direction].description)
          );
        }
        if (formatted.boundaries[direction]?.adjoins) {
          formatted.boundaries[direction].adjoins = smartTitleCase(
            formatted.boundaries[direction].adjoins
          );
        }
      });
    }

    return formatted;
  };

  const handleProcessDocument = async (retryCount = 0) => {
    if (selectedFiles.length === 0) return;

    const MAX_RETRIES = 2;
    const RETRY_DELAY = 2000; // 2 seconds

    setIsProcessing(true);
    setProcessedResult(null);

    try {
      // Get auth token from secure storage
      const token = authTokenStorage.getToken();
      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Create FormData with all files
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });
      if (documentTypeHint) {
        formData.append('document_type', documentTypeHint);
      }

      // Call OCR API (use relative path to go through Vite proxy)
      const csrfToken = getCSRFToken();
      const response = await fetch('/api/ocr/extract', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          ...(csrfToken && { 'X-CSRF-Token': csrfToken }),
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorDetail = errorData.detail || 'OCR processing failed';

        // Check if error suggests server is reloading (transient error)
        const isTransientError =
          errorDetail.includes('server may be reloading') ||
          errorDetail.includes('returned None') ||
          (response.status === 500 && retryCount < MAX_RETRIES);

        if (isTransientError) {
          console.log(`Transient error detected, retrying in ${RETRY_DELAY}ms (attempt ${retryCount + 1}/${MAX_RETRIES})...`);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
          return handleProcessDocument(retryCount + 1);
        }

        throw new Error(errorDetail);
      }

      const result = await response.json();

      if (result.status === 'success') {
        const ocrResult: OCRResult = result.data;
        setProcessedResult(ocrResult);

        if (ocrResult.success && ocrResult.extracted_data) {
          const formattedData = formatOCRData(ocrResult.extracted_data);

          onDataExtracted(
            formattedData,
            ocrResult.overall_confidence || 0.5
          );
        }
      } else {
        throw new Error('OCR processing failed');
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error occurred';

      // Only show error if we've exhausted retries
      if (retryCount >= MAX_RETRIES) {
        setProcessedResult({
          success: false,
          error: errorMessage,
        });
        onError?.(errorMessage);
      } else {
        // This shouldn't happen as we handle retries above, but just in case
        console.error('Unexpected error during OCR processing:', error);
        setProcessedResult({
          success: false,
          error: errorMessage,
        });
        onError?.(errorMessage);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-orange-600 bg-orange-50 border-orange-200';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'High Confidence';
    if (confidence >= 0.7) return 'Medium Confidence';
    return 'Low Confidence - Please Verify';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <Label className="text-lg font-semibold">Document Upload & Auto-Fill</Label>
        <p className="text-sm text-gray-600 mt-1">
          Upload a survey plan or deed (images or PDF) to automatically extract property data
        </p>
      </div>

      {/* File Input */}
      {selectedFiles.length === 0 ? (
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-sm font-medium text-gray-700 mb-1">
            Click to upload documents
          </p>
          <p className="text-xs text-gray-500 mb-2">
            Images: deed pages (3-5) + plan pages (1-2) — or upload a PDF
          </p>
          <p className="text-xs text-gray-500">
            JPEG, PNG, WEBP, or PDF (max 10MB each)
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp,.jfif,application/pdf,.pdf"
            onChange={handleFileSelect}
            disabled={disabled}
            multiple
            className="hidden"
          />
        </div>
      ) : (
        <div className="border border-gray-300 rounded-lg p-4">
          {/* Files Info */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3">
              <FileImage className="h-8 w-8 text-blue-600 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected
                </p>
                <div className="mt-1 space-y-1">
                  {selectedFiles.map((file, index) => (
                    <p key={`${file.name}-${index}`} className="text-xs text-gray-500">
                      {index + 1}. {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </p>
                  ))}
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={handleClearFile}
              disabled={isProcessing}
              className="text-gray-400 hover:text-red-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Preview Toggle */}
          {previewUrls.length > 0 && (
            <div className="mb-4">
              <button
                type="button"
                onClick={() => setShowPreviews(!showPreviews)}
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"
              >
                <Eye className="h-4 w-4" />
                {showPreviews ? 'Hide Previews' : 'Show Previews'}
              </button>
              {showPreviews && (
                <div className="mt-3 grid grid-cols-2 md:grid-cols-3 gap-3">
                  {previewUrls.map((url, index) => (
                    <div key={`preview-${index}-${url.substring(0, 20)}`} className="border border-gray-300 rounded-lg p-2 bg-gray-50">
                      <p className="text-xs text-gray-600 mb-1">
                        {url === '[pdf]' ? 'PDF' : `Page ${index + 1}`}
                      </p>
                      {url === '[pdf]' ? (
                        <div className="w-full h-32 flex flex-col items-center justify-center gap-2 bg-red-50 rounded border border-red-100">
                          <FileText className="h-10 w-10 text-red-400" />
                          <p className="text-xs text-gray-600 text-center truncate w-full px-1">
                            {selectedFiles[index]?.name}
                          </p>
                        </div>
                      ) : (
                        <img
                          src={url}
                          alt={`Document page ${index + 1}`}
                          className="w-full h-32 object-cover rounded"
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Process Button */}
          {!processedResult && (
            <Button
              type="button"
              onClick={handleProcessDocument}
              disabled={isProcessing || disabled}
              className="w-full"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing Document...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Extract Data from Document
                </>
              )}
            </Button>
          )}

          {/* Processing Result */}
          {processedResult && (
            <div className="mt-4">
              {processedResult.success ? (
                <div
                  className={`flex items-start gap-3 p-4 border rounded-lg ${getConfidenceColor(
                    processedResult.overall_confidence || 0.5
                  )}`}
                >
                  <CheckCircle2 className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      Data Extracted Successfully
                    </p>
                    <p className="text-xs mt-1">
                      {getConfidenceLabel(
                        processedResult.overall_confidence || 0.5
                      )}{' '}
                      ({((processedResult.overall_confidence || 0.5) * 100).toFixed(
                        0
                      )}
                      %)
                    </p>
                    <p className="text-xs mt-2">
                      Form fields have been pre-filled. Please review and edit as
                      needed.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-800">
                      Processing Failed
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      {processedResult.error || 'Unknown error occurred'}
                    </p>
                  </div>
                </div>
              )}

              {/* Retry Button */}
              <Button
                type="button"
                onClick={handleProcessDocument}
                disabled={isProcessing || disabled}
                variant="outline"
                className="w-full mt-3"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Process Again'
                )}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          <strong>Tip:</strong> Upload a PDF (scanned or digital) or individual image pages of your deed (3-5 pages) and survey plan (1-2 pages).
          Digital PDFs are processed directly; scanned PDFs and images go through Google Vision OCR.
          The system automatically detects and extracts plan numbers, dates, land extent, boundaries, and other property details.
        </p>
      </div>
    </div>
  );
}
