import React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Home, MapPin, Ruler, DollarSign, Edit, CheckCircle2 } from 'lucide-react';
import { MultiPropertyFormData } from './MultiPropertyStepForm';

interface PropertyComparisonStepProps {
  formMethods: UseFormReturn<MultiPropertyFormData>;
  onEditProperty: (propertyIndex: number) => void;
}

const PropertyComparisonStep: React.FC<PropertyComparisonStepProps> = ({
  formMethods,
  onEditProperty,
}) => {
  const { watch } = formMethods;

  const properties = watch('properties') || [];
  const propertyCount = watch('property_count') || properties.length;

  const formatCurrency = (amount: number | undefined) => {
    if (!amount) return 'Not set';
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatExtent = (acres?: number, roods?: number, perches?: number) => {
    const parts = [];
    if (acres) parts.push(`${acres}A`);
    if (roods) parts.push(`${roods}R`);
    if (perches) parts.push(`${perches}P`);
    return parts.length > 0 ? parts.join(' ') : 'Not set';
  };

  // Calculate totals
  const totalMarketValue = properties.reduce((sum: number, prop: any) => {
    return sum + (prop.valuation_market_value || 0);
  }, 0);

  const totalExtentAcres = properties.reduce((sum: number, prop: any) => {
    const acres = prop.land_extent_acres || 0;
    const roods = (prop.land_extent_roods || 0) / 4;
    const perches = (prop.land_extent_perches || 0) / 160;
    return sum + acres + roods + perches;
  }, 0);

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-violet-500 to-purple-600 text-white rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-violet-100 text-sm mb-1">Total Properties</p>
              <p className="text-3xl font-black">{propertyCount}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Home className="h-8 w-8" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-emerald-500 to-green-600 text-white rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-emerald-100 text-sm mb-1">Total Land Extent</p>
              <p className="text-2xl font-black">{totalExtentAcres.toFixed(2)} Acres</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Ruler className="h-8 w-8" />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm mb-1">Total Market Value</p>
              <p className="text-2xl font-black">{formatCurrency(totalMarketValue)}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <DollarSign className="h-8 w-8" />
            </div>
          </div>
        </div>
      </div>

      {/* Properties Comparison Table */}
      <div className="bg-white rounded-2xl border-2 border-gray-200 overflow-hidden shadow-lg">
        <div className="bg-gradient-to-r from-indigo-500 to-blue-600 text-white px-6 py-4">
          <h4 className="font-bold text-lg">Property Comparison</h4>
          <p className="text-indigo-100 text-sm">Review all properties before finalizing</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-4 px-4 font-semibold text-gray-700 w-16">#</th>
                <th className="text-left py-4 px-4 font-semibold text-gray-700">Property</th>
                <th className="text-left py-4 px-4 font-semibold text-gray-700">Location</th>
                <th className="text-center py-4 px-4 font-semibold text-gray-700">Extent</th>
                <th className="text-right py-4 px-4 font-semibold text-gray-700">Market Value</th>
                <th className="text-center py-4 px-4 font-semibold text-gray-700 w-24">Actions</th>
              </tr>
            </thead>
            <tbody>
              {properties.map((property: any, index: number) => (
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 text-white flex items-center justify-center font-bold">
                      {index + 1}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div>
                      <div className="font-semibold text-gray-900">
                        {property.lot_number || property.property_lot_description || `Property ${index + 1}`}
                      </div>
                      {property.plan_number && (
                        <div className="text-sm text-gray-500">Plan: {property.plan_number}</div>
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div>
                      <div className="text-gray-900">
                        {property.property_village || 'Not set'}
                      </div>
                      <div className="text-sm text-gray-500">
                        {property.property_district || 'District not set'}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <div className="text-gray-900 font-medium">
                      {property.land_extent_formatted ||
                        formatExtent(
                          property.land_extent_acres,
                          property.land_extent_roods,
                          property.land_extent_perches
                        )}
                    </div>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="font-bold text-green-600">
                      {formatCurrency(property.valuation_market_value)}
                    </div>
                    {property.valuation_forced_sale_value && (
                      <div className="text-sm text-gray-500">
                        FSV: {formatCurrency(property.valuation_forced_sale_value)}
                      </div>
                    )}
                  </td>
                  <td className="py-4 px-4 text-center">
                    <button
                      type="button"
                      onClick={() => onEditProperty(index)}
                      className="inline-flex items-center px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg text-sm font-medium transition-colors"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gradient-to-r from-gray-50 to-gray-100 border-t-2 border-gray-300">
              <tr>
                <td colSpan={3} className="py-4 px-4">
                  <div className="font-bold text-gray-900 text-lg">Total</div>
                </td>
                <td className="py-4 px-4 text-center">
                  <div className="font-bold text-gray-900">
                    {totalExtentAcres.toFixed(2)} Acres
                  </div>
                </td>
                <td className="py-4 px-4 text-right">
                  <div className="font-bold text-green-600 text-lg">
                    {formatCurrency(totalMarketValue)}
                  </div>
                </td>
                <td className="py-4 px-4"></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Property Details Cards (Mobile View) */}
      <div className="md:hidden space-y-4">
        {properties.map((property: any, index: number) => (
          <div key={index} className="bg-white rounded-2xl border-2 border-gray-200 p-4 shadow-md">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 text-white flex items-center justify-center font-bold mr-3">
                  {index + 1}
                </div>
                <div>
                  <div className="font-semibold text-gray-900">
                    {property.property_lot_description || `Property ${index + 1}`}
                  </div>
                  {property.plan_number && (
                    <div className="text-sm text-gray-500">Plan: {property.plan_number}</div>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => onEditProperty(index)}
                className="p-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
              >
                <Edit className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center text-gray-700">
                <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                <span>{property.property_village || 'Not set'}, {property.property_district || 'Not set'}</span>
              </div>
              <div className="flex items-center text-gray-700">
                <Ruler className="h-4 w-4 mr-2 text-gray-400" />
                <span>
                  {property.land_extent_formatted ||
                    formatExtent(
                      property.land_extent_acres,
                      property.land_extent_roods,
                      property.land_extent_perches
                    )}
                </span>
              </div>
              <div className="flex items-center text-gray-700">
                <DollarSign className="h-4 w-4 mr-2 text-gray-400" />
                <span className="font-bold text-green-600">
                  {formatCurrency(property.valuation_market_value)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Confirmation Message */}
      <div className="bg-green-50 rounded-2xl p-6 border-2 border-green-200">
        <div className="flex items-start">
          <CheckCircle2 className="h-6 w-6 text-green-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h5 className="font-bold text-green-900 mb-2">Ready to Proceed</h5>
            <p className="text-green-800 text-sm">
              You've entered information for all {propertyCount} properties. Review the details above and use the "Edit" button
              to make any changes before proceeding to the invoice and certification steps.
            </p>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 rounded-xl p-4">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Note:</span> Drag-and-drop reordering will be available in a future update.
          Properties will appear in the report in the order shown above (Property 1, Property 2, etc.).
        </p>
      </div>
    </div>
  );
};

export default PropertyComparisonStep;
