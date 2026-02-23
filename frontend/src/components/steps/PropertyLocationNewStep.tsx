import React, { useState } from 'react';
import { PropertyLocationSection } from '../PropertyLocationSection';
import type { Report } from '../../types';
import type { StepComponentProps } from '../../types/multiStepForm';

const PropertyLocationNewStep: React.FC<StepComponentProps & { getValues: any }> = ({ setValue, getValues }) => {
    const [formData, setFormData] = useState<Partial<Report>>({});

    // Sync with react-hook-form
    React.useEffect(() => {
        const currentValues = getValues();
        setFormData(currentValues);
    }, [getValues]);

    const updateFormData = (updates: Partial<Report>) => {
        setFormData(prev => ({ ...prev, ...updates }));
        // Sync back to react-hook-form
        Object.keys(updates).forEach(key => {
            setValue(key, updates[key as keyof typeof updates]);
        });
    };

    return (
        <div className="space-y-6">
            <PropertyLocationSection
                formData={formData}
                updateFormData={updateFormData}
            />

            {/* Show map if available */}
            {formData.location_map_image_data && (
                <div className="mt-6 border-2 border-blue-200 rounded-2xl overflow-hidden">
                    <img
                        src={formData.location_map_image_data}
                        alt="Property Location Map"
                        className="w-full h-80 object-cover"
                    />
                </div>
            )}
        </div>
    );
};

export default PropertyLocationNewStep;
export { PropertyLocationNewStep };
