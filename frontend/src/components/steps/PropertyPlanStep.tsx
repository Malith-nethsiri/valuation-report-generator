import React from 'react';
import toast from 'react-hot-toast';
import { DocumentUploadOCR } from '../DocumentUploadOCR';
import { PropertyPlanFields } from './PropertyPlanFields';
import type { StepComponentProps } from '../../types/multiStepForm';

const PropertyPlanStep: React.FC<StepComponentProps> = ({
    register,
    errors,
    setValue,
    watch,
    getValues,
    ocrFilledFields,
    onMarkOCRFilled,
    isBareLand,
}) => {
    const handleOCRDataExtracted = (extractedData: any, confidence: number) => {
        if (!setValue || !getValues) return;

        let detectedType: string | null = null;
        const confidenceScores = extractedData._confidence_scores || {};

        // Helper: only fill if confidence > 0.6 AND field is currently empty
        const fill = (field: string, value: any) => {
            const fieldConfidence = confidenceScores[field] ?? confidence;
            if (fieldConfidence > 0.6 && !getValues(field) && value != null) {
                setValue(field, value);
                onMarkOCRFilled?.(field);
            }
        };

        // Detection type is always set (selector, not user-typed text)
        const hasPlan = !!extractedData.plan_number;
        const hasDeed =
            extractedData.deeds &&
            Array.isArray(extractedData.deeds) &&
            extractedData.deeds.length > 0;

        if (hasPlan && hasDeed) {
            detectedType = 'plan_and_deed';
            setValue('property_identification_type', 'plan_and_deed');
            fill('plan_number', extractedData.plan_number);
            fill('plan_date', extractedData.plan_date);
            fill('licensed_surveyor_name', extractedData.licensed_surveyor_name);
            fill('lot_number', extractedData.lot_number);
            const firstDeed = extractedData.deeds[0];
            fill('deed_type', firstDeed.deed_type);
            fill('deed_number', firstDeed.deed_number);
            fill('deed_date', firstDeed.deed_date);
            fill('notary_name', firstDeed.notary_name);
            fill('notary_location', firstDeed.notary_location);
        } else if (hasPlan) {
            detectedType = 'plan';
            setValue('property_identification_type', 'plan');
            fill('plan_number', extractedData.plan_number);
            fill('plan_date', extractedData.plan_date);
            fill('licensed_surveyor_name', extractedData.licensed_surveyor_name);
            fill('lot_number', extractedData.lot_number);
        } else if (hasDeed) {
            const firstDeed = extractedData.deeds[0];
            if (firstDeed.deed_type?.toLowerCase().includes('certificate of sale')) {
                detectedType = 'certificate_of_sale';
                setValue('property_identification_type', 'certificate_of_sale');
                fill('certificate_number', firstDeed.deed_number);
                fill('certificate_date', firstDeed.deed_date);
                fill('certificate_notary_name', firstDeed.notary_name);
                fill('certificate_notary_district', firstDeed.notary_location);
            } else {
                detectedType = 'deed';
                setValue('property_identification_type', 'deed');
                fill('deed_type', firstDeed.deed_type);
                fill('deed_number', firstDeed.deed_number);
                fill('deed_date', firstDeed.deed_date);
                fill('notary_name', firstDeed.notary_name);
                fill('notary_location', firstDeed.notary_location);
            }
        }

        // Extent
        fill('land_extent_acres', extractedData.land_extent_acres);
        fill('land_extent_roods', extractedData.land_extent_roods);
        fill('land_extent_perches', extractedData.land_extent_perches);
        fill('land_extent_hectares', extractedData.land_extent_hectares);
        fill('land_extent_square_meters', extractedData.land_extent_square_meters);
        fill('land_extent_formatted', extractedData.land_extent_formatted);
        fill('land_traditional_name', extractedData.land_traditional_name);

        // Boundaries (non-scalar — fill if missing)
        fill('boundaries', extractedData.boundaries);
        fill('physical_boundaries_types', extractedData.physical_boundaries_types);
        fill('physical_boundaries_description', extractedData.physical_boundaries_description);

        // Location / administrative divisions
        fill('property_village', extractedData.village);
        fill('grama_niladari_division', extractedData.gn_division_name);
        fill('property_divisional_secretariat', extractedData.ds_division);
        fill('property_district', extractedData.district);
        fill('property_province', extractedData.province);
        fill('korale', extractedData.korale);
        fill('pradeshiya_sabha', extractedData.pradeshiya_sabha);

        // Building plan data — residential only, stored in staging field
        if (extractedData.building_plan && !isBareLand) {
            setValue('ocr_building_plan_data', extractedData.building_plan);
            onMarkOCRFilled?.('ocr_building_plan_data');
        }

        // Toast
        const pct = (confidence * 100).toFixed(0);
        const label = detectedType ? detectedType.replace(/_/g, ' ') : 'document';
        if (confidence >= 0.7) {
            toast.success(
                `Detected ${label} information with ${pct}% confidence. Please review and edit as needed.`,
                { duration: 5000, position: 'top-right' }
            );
        } else {
            toast(`Detected ${label} information with ${pct}% confidence. Please review and verify carefully.`, {
                icon: '⚠️',
                duration: 6000,
                position: 'top-right',
            });
        }
    };

    return (
        <div className="space-y-6">
            <DocumentUploadOCR
                onDataExtracted={handleOCRDataExtracted}
                onError={(error) =>
                    toast.error(`OCR Error: ${error}`, { duration: 6000, position: 'top-right' })
                }
                documentTypeHint="survey_plan"
            />

            <div className="border-t border-gray-200 my-6"></div>

            <PropertyPlanFields
                register={register}
                errors={errors}
                watch={watch}
                setValue={setValue!}
                ocrFilledFields={ocrFilledFields}
            />
        </div>
    );
};

export default PropertyPlanStep;
export { PropertyPlanStep };
