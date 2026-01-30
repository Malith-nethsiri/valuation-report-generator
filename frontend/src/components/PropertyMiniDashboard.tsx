/**
 * PropertyMiniDashboard - Mini dashboard for managing properties in multi-property reports
 *
 * Features:
 * - Property type selector cards (clickable to add properties)
 * - Displays property cards in horizontal list layout
 * - Shows property type badge, number, address, and status
 * - CRUD actions: Edit, Delete, Move Up, Move Down, Duplicate
 * - AddPropertyDialog for batch adding properties
 * - 20 property maximum limit enforced
 * - 1 property minimum enforced
 *
 * Card Information:
 * - Property type label ("Residential Property 1" or "Bare Land Property 1")
 * - Full address (or placeholder if not entered)
 * - Status badge (Draft = orange, Completed = green)
 * - Action buttons
 */

import React, { useState } from 'react';
import {
    Edit,
    Trash2,
    ChevronUp,
    ChevronDown,
    Copy,
    Building,
    Sprout,
    MapPin,
    Plus,
    Car
} from 'lucide-react';
import { AddPropertyDialog } from './AddPropertyDialog';
import toast from 'react-hot-toast';
import type { PropertyInReport } from '../types';

// Re-export for backward compatibility
export type { PropertyInReport };

interface PropertyMiniDashboardProps {
    properties: PropertyInReport[];
    onEdit: (propertyId: string | number) => void;
    onDelete: (propertyId: string | number) => void;
    onMoveUp: (propertyId: string | number) => void;
    onMoveDown: (propertyId: string | number) => void;
    onDuplicate: (propertyId: string | number) => void;
    onAddBatch: (type: 'residential' | 'bare_land' | 'vehicle', count: number) => void;
}

export const PropertyMiniDashboard: React.FC<PropertyMiniDashboardProps> = ({
    properties,
    onEdit,
    onDelete,
    onMoveUp,
    onMoveDown,
    onDuplicate,
    onAddBatch
}) => {
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
    const [selectedPropertyType, setSelectedPropertyType] = useState<'residential' | 'bare_land' | 'vehicle' | null>(null);

    // Sort properties by order
    const sortedProperties = [...properties].sort((a, b) => a.order - b.order);

    // Count residential, bare land, and vehicle properties
    const residentialCount = properties.filter(p => p.type === 'residential').length;
    const bareLandCount = properties.filter(p => p.type === 'bare_land').length;
    const vehicleCount = properties.filter(p => p.type === 'vehicle').length;

    // Handle type card click
    const handleTypeCardClick = (type: 'residential' | 'bare_land' | 'vehicle') => {
        const totalCount = properties.length;
        if (totalCount >= 20) {
            toast.error('Maximum 20 properties reached');
            return;
        }

        setSelectedPropertyType(type);
        setIsAddDialogOpen(true);
    };

    const handleAddConfirm = (count: number) => {
        onAddBatch(selectedPropertyType!, count);
        setIsAddDialogOpen(false);
        setSelectedPropertyType(null);
    };

    const handleAddCancel = () => {
        setIsAddDialogOpen(false);
        setSelectedPropertyType(null);
    };

    // Get property number within its type (e.g., "Residential Property 2")
    const getPropertyNumber = (property: PropertyInReport) => {
        const propertiesOfSameType = sortedProperties.filter(p => p.type === property.type);
        return propertiesOfSameType.findIndex(p => p.id === property.id) + 1;
    };

    // Get property display address (or vehicle info)
    const getPropertyAddress = (property: PropertyInReport) => {
        // Handle vehicle type differently
        if (property.type === 'vehicle') {
            const { registration_number, make, model } = property.data;
            if (make || model) {
                return `${make || ''} ${model || ''}${registration_number ? ' (' + registration_number + ')' : ''}`.trim();
            }
            if (registration_number) {
                return registration_number;
            }
            return 'No vehicle details entered yet';
        }

        // Handle property types
        const { property_village, property_district, lot_number, property_lot_description, plan_number } = property.data;

        if (property_village || property_district) {
            return `${property_village || 'Unknown'}${property_district ? ', ' + property_district : ''}`;
        }

        const lotNum = lot_number || property_lot_description;
        if (lotNum || plan_number) {
            return `${lotNum ? 'Lot ' + lotNum : ''}${
                plan_number ? (lotNum ? ', ' : '') + 'Plan ' + plan_number : ''
            }`;
        }

        return 'No address entered yet';
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Property Dashboard</h2>
                <p className="text-gray-600">
                    Manage your properties: Edit, delete, reorder, or duplicate
                </p>
            </div>

            {/* Property Type Selector Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Residential/Commercial Card */}
                <button
                    onClick={() => handleTypeCardClick('residential')}
                    disabled={properties.length >= 20}
                    className={`bg-white/60 backdrop-blur-sm rounded-3xl p-6 border-2 transition-all duration-300 text-left group ${
                        properties.length >= 20
                            ? 'border-gray-200 opacity-50 cursor-not-allowed'
                            : 'border-blue-200 hover:border-blue-400 hover:shadow-xl cursor-pointer transform hover:scale-[1.02]'
                    }`}
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg">
                                <Building className="h-8 w-8 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Residential/Commercial</h3>
                                <p className="text-sm text-gray-600">Properties with buildings</p>
                            </div>
                        </div>
                        <div className={`p-3 rounded-full ${properties.length >= 20 ? 'bg-gray-100' : 'bg-blue-100 group-hover:bg-blue-200'} transition-colors duration-200`}>
                            <Plus className={`h-6 w-6 ${properties.length >= 20 ? 'text-gray-400' : 'text-blue-600'}`} />
                        </div>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-blue-600">{residentialCount}</span>
                        <span className="text-sm text-gray-600">{residentialCount === 1 ? 'property' : 'properties'}</span>
                    </div>
                    {properties.length >= 20 && (
                        <p className="text-xs text-red-600 mt-2">Maximum limit reached</p>
                    )}
                </button>

                {/* Bare Land Card */}
                <button
                    onClick={() => handleTypeCardClick('bare_land')}
                    disabled={properties.length >= 20}
                    className={`bg-white/60 backdrop-blur-sm rounded-3xl p-6 border-2 transition-all duration-300 text-left group ${
                        properties.length >= 20
                            ? 'border-gray-200 opacity-50 cursor-not-allowed'
                            : 'border-green-200 hover:border-green-400 hover:shadow-xl cursor-pointer transform hover:scale-[1.02]'
                    }`}
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-lg">
                                <Sprout className="h-8 w-8 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Bare Land</h3>
                                <p className="text-sm text-gray-600">Land without buildings</p>
                            </div>
                        </div>
                        <div className={`p-3 rounded-full ${properties.length >= 20 ? 'bg-gray-100' : 'bg-green-100 group-hover:bg-green-200'} transition-colors duration-200`}>
                            <Plus className={`h-6 w-6 ${properties.length >= 20 ? 'text-gray-400' : 'text-green-600'}`} />
                        </div>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-green-600">{bareLandCount}</span>
                        <span className="text-sm text-gray-600">{bareLandCount === 1 ? 'property' : 'properties'}</span>
                    </div>
                    {properties.length >= 20 && (
                        <p className="text-xs text-red-600 mt-2">Maximum limit reached</p>
                    )}
                </button>

                {/* Vehicle Card */}
                <button
                    onClick={() => handleTypeCardClick('vehicle')}
                    disabled={properties.length >= 20}
                    className={`bg-white/60 backdrop-blur-sm rounded-3xl p-6 border-2 transition-all duration-300 text-left group ${
                        properties.length >= 20
                            ? 'border-gray-200 opacity-50 cursor-not-allowed'
                            : 'border-cyan-200 hover:border-cyan-400 hover:shadow-xl cursor-pointer transform hover:scale-[1.02]'
                    }`}
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-3 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl shadow-lg">
                                <Car className="h-8 w-8 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Vehicle</h3>
                                <p className="text-sm text-gray-600">Cars, motorcycles, trucks</p>
                            </div>
                        </div>
                        <div className={`p-3 rounded-full ${properties.length >= 20 ? 'bg-gray-100' : 'bg-cyan-100 group-hover:bg-cyan-200'} transition-colors duration-200`}>
                            <Plus className={`h-6 w-6 ${properties.length >= 20 ? 'text-gray-400' : 'text-cyan-600'}`} />
                        </div>
                    </div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-cyan-600">{vehicleCount}</span>
                        <span className="text-sm text-gray-600">{vehicleCount === 1 ? 'vehicle' : 'vehicles'}</span>
                    </div>
                    {properties.length >= 20 && (
                        <p className="text-xs text-red-600 mt-2">Maximum limit reached</p>
                    )}
                </button>
            </div>

            {/* Total Summary */}
            <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-2xl p-4 border border-violet-200">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-gray-600">Total Assets</p>
                        <p className="text-2xl font-bold text-gray-900">{properties.length} / 20</p>
                    </div>
                    <div className="flex gap-6">
                        <div className="text-center">
                            <p className="text-xs text-gray-500">Properties</p>
                            <p className="text-lg font-bold text-blue-600">{residentialCount + bareLandCount}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-xs text-gray-500">Vehicles</p>
                            <p className="text-lg font-bold text-cyan-600">{vehicleCount}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-xs text-gray-500">Completed</p>
                            <p className="text-lg font-bold text-green-600">
                                {properties.filter(p => p.status === 'completed').length}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Property Cards - Horizontal List Layout */}
            <div className="space-y-3">
                {sortedProperties.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50/50 rounded-2xl border-2 border-dashed border-gray-300">
                        <Building className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-gray-700 mb-2">No properties yet</h3>
                        <p className="text-sm text-gray-500 mb-4">Click a property type card above to add properties</p>
                    </div>
                ) : (
                    sortedProperties.map((property, index) => {
                        const isFirst = index === 0;
                        const isLast = index === sortedProperties.length - 1;
                        const propertyNumber = getPropertyNumber(property);
                        const isResidential = property.type === 'residential';
                        const isVehicle = property.type === 'vehicle';

                        // Determine colors and icons based on type
                        const getTypeConfig = () => {
                            if (isVehicle) {
                                return {
                                    hoverBorder: 'hover:border-cyan-300',
                                    bgGradient: 'bg-gradient-to-br from-cyan-500 to-blue-600',
                                    icon: <Car className="h-6 w-6 text-white" />,
                                    label: 'Vehicle',
                                    editColor: 'text-cyan-600 hover:bg-cyan-50'
                                };
                            } else if (isResidential) {
                                return {
                                    hoverBorder: 'hover:border-blue-300',
                                    bgGradient: 'bg-gradient-to-br from-blue-500 to-indigo-600',
                                    icon: <Building className="h-6 w-6 text-white" />,
                                    label: 'Residential',
                                    editColor: 'text-blue-600 hover:bg-blue-50'
                                };
                            } else {
                                return {
                                    hoverBorder: 'hover:border-green-300',
                                    bgGradient: 'bg-gradient-to-br from-green-500 to-emerald-600',
                                    icon: <Sprout className="h-6 w-6 text-white" />,
                                    label: 'Bare Land',
                                    editColor: 'text-green-600 hover:bg-green-50'
                                };
                            }
                        };

                        const typeConfig = getTypeConfig();

                        return (
                            <div
                                key={property.id}
                                className={`flex items-center gap-4 p-4 bg-gray-50/50 rounded-2xl border border-gray-100 hover:bg-gray-100/50 hover:border-gray-200 transition-all duration-200 ${typeConfig.hoverBorder}`}
                            >
                                {/* Property Icon Badge */}
                                <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${typeConfig.bgGradient}`}>
                                    {typeConfig.icon}
                                </div>

                                {/* Property Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="font-semibold text-gray-900">
                                            {typeConfig.label} {isVehicle ? '' : 'Property '}{propertyNumber}
                                        </h3>
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                            property.status === 'completed'
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-orange-100 text-orange-800'
                                        }`}>
                                            {property.status === 'completed' ? '✓ Completed' : '○ Draft'}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-1.5 text-sm text-gray-600">
                                        <MapPin className="h-3.5 w-3.5 text-gray-400 flex-shrink-0" />
                                        <p className="truncate">{getPropertyAddress(property)}</p>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">Position {index + 1} of {sortedProperties.length}</p>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex items-center gap-2">
                                    {/* Edit Button */}
                                    <button
                                        onClick={() => onEdit(property.id)}
                                        className={`p-2 rounded-xl transition-all duration-200 ${typeConfig.editColor}`}
                                        title={isVehicle ? "Edit Vehicle" : "Edit Property"}
                                    >
                                        <Edit className="h-5 w-5" />
                                    </button>

                                    {/* Move Up Button */}
                                    <button
                                        onClick={() => onMoveUp(property.id)}
                                        disabled={isFirst}
                                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                                        title="Move Up"
                                    >
                                        <ChevronUp className="h-5 w-5" />
                                    </button>

                                    {/* Move Down Button */}
                                    <button
                                        onClick={() => onMoveDown(property.id)}
                                        disabled={isLast}
                                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                                        title="Move Down"
                                    >
                                        <ChevronDown className="h-5 w-5" />
                                    </button>

                                    {/* Duplicate Button */}
                                    <button
                                        onClick={() => onDuplicate(property.id)}
                                        disabled={properties.length >= 20}
                                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                                        title={properties.length >= 20 ? 'Maximum 20 properties reached' : 'Duplicate Property'}
                                    >
                                        <Copy className="h-5 w-5" />
                                    </button>

                                    {/* Delete Button */}
                                    <button
                                        onClick={() => onDelete(property.id)}
                                        className="p-2 text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200"
                                        title="Delete Property"
                                    >
                                        <Trash2 className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Quick Tips</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Click a card above to add properties or vehicles</li>
                    <li>• Click "Edit" to fill in details and mark as completed</li>
                    <li>• Use "Move Up/Down" to reorder items (affects final report order)</li>
                    <li>• Click "Copy" to duplicate with all data (max 20 total)</li>
                    <li>• At least 1 completed item is required to generate the report</li>
                    <li>• Vehicles and properties can be mixed in the same report</li>
                </ul>
            </div>

            {/* Add Property Dialog */}
            <AddPropertyDialog
                isOpen={isAddDialogOpen}
                propertyType={selectedPropertyType || 'residential'}
                maxAllowed={20 - properties.length}
                onConfirm={handleAddConfirm}
                onCancel={handleAddCancel}
            />
        </div>
    );
};
