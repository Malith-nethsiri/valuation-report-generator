import React from 'react';
import { LandExtentInput } from '../LandExtentInput';
import { BoundaryInformationSection } from '../BoundaryInformationSection';
import type { StepComponentProps } from '../../types/multiStepForm';

const ExtentBoundariesStep: React.FC<StepComponentProps> = ({ setValue, watch }) => {
    const handleExtentChange = (extentData: any) => {
        if (setValue) {
            setValue('land_extent_acres', extentData.land_extent_acres);
            setValue('land_extent_roods', extentData.land_extent_roods);
            setValue('land_extent_perches', extentData.land_extent_perches);
            setValue('land_extent_hectares', extentData.land_extent_hectares);
            setValue('land_extent_square_meters', extentData.land_extent_square_meters);
            setValue('land_extent_formatted', extentData.land_extent_formatted);
        }
    };

    const handleBoundaryChange = (data: any) => {
        if (setValue) {
            setValue('boundaries', data.boundaries);
            setValue('physical_boundaries_types', data.physical_boundaries_types);
            setValue('physical_boundaries_description', data.physical_boundaries_description);
            setValue('land_traditional_name', data.land_traditional_name);
        }
    };

    return (
        <div className="space-y-8">
            {/* Land Extent Input */}
            <LandExtentInput
                acres={watch?.('land_extent_acres') || 0}
                roods={watch?.('land_extent_roods') || 0}
                perches={watch?.('land_extent_perches') || 0}
                onChange={handleExtentChange}
            />

            <div className="border-t border-gray-200 my-6"></div>

            {/* Boundary Information */}
            <BoundaryInformationSection
                boundaries={watch?.('boundaries')}
                physicalBoundariesTypes={watch?.('physical_boundaries_types') || []}
                physicalBoundariesDescription={watch?.('physical_boundaries_description') || ''}
                landTraditionalName={watch?.('land_traditional_name') || ''}
                onChange={handleBoundaryChange}
            />
        </div>
    );
};

export default ExtentBoundariesStep;
export { ExtentBoundariesStep };
