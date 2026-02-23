import React, { useState } from 'react';
import { MapPin } from 'lucide-react';
import { InteractivePropertyMap } from '../InteractivePropertyMap';
import type { Report } from '../../types';
import type { StepComponentProps } from '../../types/multiStepForm';

// Extra props passed at runtime but not yet declared in InteractivePropertyMap Props type
type MapExtraProps = {
    initialEntryMode?: string;
    initialRoadSegments?: any;
};
const AnyInteractivePropertyMap = InteractivePropertyMap as React.FC<React.ComponentProps<typeof InteractivePropertyMap> & MapExtraProps>;

const PropertySearchStep: React.FC<StepComponentProps & { getValues: any }> = ({ setValue, getValues }) => {
    const [formData, setFormData] = useState<Partial<Report>>({});

    // Sync with react-hook-form
    React.useEffect(() => {
        const currentValues = getValues();
        setFormData(currentValues);
    }, [getValues]);

    const updateFormData = (updates: Record<string, any>) => {
        setFormData(prev => ({ ...prev, ...updates }));
        // Sync back to react-hook-form
        Object.keys(updates).forEach(key => {
            setValue(key, updates[key]);
        });
    };

    return (
        <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-2 border-blue-300 rounded-2xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                    <MapPin className="h-6 w-6 text-blue-600" />
                    Find Property & Generate Directions
                </h3>
                <p className="text-gray-600">
                    Use the interactive map to find the property location and generate access directions - just like Google Maps!
                </p>
            </div>

            {/* Interactive Google Maps */}
            <AnyInteractivePropertyMap
                onPropertySelected={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Property selected:', data);
                    }
                    updateFormData({
                        property_latitude: data.latitude,
                        property_longitude: data.longitude,
                        // Save geocoding data for auto-fill in next step
                        property_district: data.district,
                        property_province: data.province,
                        property_village: data.village,
                    });
                }}
                onStartingPointSelected={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Starting point selected:', data);
                    }
                    updateFormData({
                        access_starting_point_name: data.address,
                        access_starting_point_latitude: data.latitude,
                        access_starting_point_longitude: data.longitude,
                    });
                }}
                onRouteGenerated={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Route generated:', data);
                    }
                    updateFormData({
                        access_directions_text: data.accessText,
                        access_distance_km: parseFloat(data.distance.replace(/[^\d.]/g, '')) || 0,
                        access_duration_minutes: parseFloat(data.duration.replace(/[^\d.]/g, '')) || 0,
                        access_route_data: { steps: data.steps, distance: data.distance, duration: data.duration },
                        // Save map image URL
                        location_map_image_data: data.mapImageUrl,
                        // NEW: Save dual-mode data
                        access_road_conditions: (data as any).road_conditions,
                        access_road_segments: (data as any).road_segments,
                        access_entry_mode: data.entry_mode,
                    });
                }}
                onFacilitiesFetched={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Facilities prefetched:', data);
                    }
                    updateFormData({
                        nearby_facilities: data.facilities,
                        major_town_name: data.majorTown?.name,
                        distance_to_major_town_km: data.majorTown?.distance_km,
                        nearest_bus_stop_name: data.transport?.bus_stop?.name,
                        nearest_bus_stop_distance_km: data.transport?.bus_stop?.distance_km,
                        nearest_railway_station: data.transport?.railway_station?.name,
                        nearest_railway_distance_km: data.transport?.railway_station?.distance_km,
                    });
                }}
                initialStartingPoint={formData.access_starting_point_name}
                // Pass saved data to restore state when navigating back
                initialRouteData={formData.access_route_data}
                initialAccessText={formData.access_directions_text}
                initialMapImageUrl={formData.location_map_image_data}
                // NEW: Pass dual-mode data to restore state
                initialEntryMode={(formData as any).access_entry_mode}
                initialRoadConditions={formData.access_road_conditions}
                initialRoadSegments={(formData as any).access_road_segments}
            />
        </div>
    );
};

export default PropertySearchStep;
export { PropertySearchStep };
