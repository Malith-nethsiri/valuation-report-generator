import React, { useState, useEffect } from 'react';
import { TrendingUp, Plus, Trash2 } from 'lucide-react';
import { Button } from './Button';
import { Label } from './Label';
import { Input } from './Input';
import { Textarea } from './Textarea';
import { ComparableProperty } from '../types';
import { formatCurrency, formatNumber } from '../utils/currency';

interface LandValuesData {
  comparable_properties?: ComparableProperty[];
  land_market_analysis?: string;
}

interface Props {
  data: LandValuesData;
  onChange: (data: Partial<LandValuesData>) => void;
}

const PROPERTY_TYPE_OPTIONS: Array<'Commercial' | 'Residential' | 'Agricultural'> = [
  'Residential',
  'Commercial',
  'Agricultural'
];

function generateId(): string {
  return `comp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export default function LandValuesSection({ data, onChange }: Props) {
  const [comparables, setComparables] = useState<ComparableProperty[]>(
    data.comparable_properties || []
  );

  // Sync local state with parent data
  useEffect(() => {
    if (data.comparable_properties) {
      setComparables(data.comparable_properties);
    }
  }, [data.comparable_properties]);

  const calculateTotalValue = (extent: number, rate: number): number => {
    return extent * rate;
  };

  const calculateAverageRate = (): number => {
    if (comparables.length === 0) return 0;
    const sum = comparables.reduce((acc, c) => acc + c.rate_per_perch, 0);
    return sum / comparables.length;
  };

  const handleAddComparable = () => {
    const newComparable: ComparableProperty = {
      id: generateId(),
      property_type: 'Residential',
      location_description: '',
      extent: 0,
      rate_per_perch: 0,
      total_value: 0
    };

    const updated = [...comparables, newComparable];
    setComparables(updated);
    onChange({ comparable_properties: updated });
  };

  const handleRemoveComparable = (id: string) => {
    const updated = comparables.filter(c => c.id !== id);
    setComparables(updated);
    onChange({ comparable_properties: updated });
  };

  const handleComparableChange = (
    id: string,
    field: keyof ComparableProperty,
    value: any
  ) => {
    const updated = comparables.map(c => {
      if (c.id === id) {
        const updatedComp = { ...c, [field]: value };

        // Auto-calculate total value when extent or rate changes
        if (field === 'extent' || field === 'rate_per_perch') {
          updatedComp.total_value = calculateTotalValue(
            field === 'extent' ? value : c.extent,
            field === 'rate_per_perch' ? value : c.rate_per_perch
          );
        }

        return updatedComp;
      }
      return c;
    });

    setComparables(updated);
    onChange({ comparable_properties: updated });
  };

  const generateLandValuesParagraph = (comparables: ComparableProperty[]): string => {
    // Filter valid comparables
    const valid = comparables.filter(c => c.extent > 0 && c.rate_per_perch > 0);

    if (valid.length === 0) {
      return "Add comparable properties to see the auto-generated paragraph...";
    }

    // Handle single comparable
    if (valid.length === 1) {
      const comp = valid[0];
      const descriptors = {
        Residential: 'Residential building blocks',
        Commercial: 'Commercial building blocks',
        Agricultural: 'Agricultural land parcels'
      };
      const descriptor = descriptors[comp.property_type] || 'Building blocks';
      const location = comp.location_description || 'this area';
      return `${descriptor} of about ${comp.extent.toFixed(0)} Perches in ${location} is valued at approximately Rs.${comp.rate_per_perch.toLocaleString('en-US')}/= Per Perch.`;
    }

    // Group by property type
    const grouped: Record<string, ComparableProperty[]> = {};
    valid.forEach(comp => {
      if (!grouped[comp.property_type]) {
        grouped[comp.property_type] = [];
      }
      grouped[comp.property_type].push(comp);
    });

    const typeOrder: Array<'Residential' | 'Commercial' | 'Agricultural'> =
      ['Residential', 'Commercial', 'Agricultural'];

    const paragraphs: string[] = [];

    typeOrder.forEach(propType => {
      if (!grouped[propType]) return;

      const group = grouped[propType];
      const extents = group.map(c => c.extent);
      const rates = group.map(c => c.rate_per_perch);

      const minExtent = Math.min(...extents);
      const maxExtent = Math.max(...extents);
      const minRate = Math.min(...rates);
      const maxRate = Math.max(...rates);

      // Format extent
      const extentStr = minExtent === maxExtent
        ? `about ${minExtent.toFixed(0)} Perches`
        : `about ${minExtent.toFixed(0)} – ${maxExtent.toFixed(0)} Perches`;

      // Format rate
      const formatRate = (rate: number) => `Rs.${rate.toLocaleString('en-US')}/=`;
      const rateStr = minRate === maxRate
        ? `${formatRate(minRate)} Per Perch`
        : `${formatRate(minRate)} to ${formatRate(maxRate)} Per Perch`;

      // Property descriptor
      const descriptors = {
        Residential: 'Residential building blocks',
        Commercial: 'Commercial building blocks',
        Agricultural: 'Agricultural land parcels'
      };

      // Location context (simplified for preview)
      const locations = group.map(c => c.location_description).filter(l => l);
      const locationStr = locations.length > 0 ? 'located in this area' : 'in this area';

      // Context phrase based on rate variance
      const rateVariance = minRate > 0 ? ((maxRate - minRate) / minRate * 100) : 0;
      let contextPhrase = '';
      if (rateVariance < 20) {
        contextPhrase = 'showing stable market conditions';
      } else if (rateVariance > 50) {
        contextPhrase = 'depending upon the location, topography and nature of the property and convenience etc.';
      } else {
        contextPhrase = 'to be influenced by factors affecting the property market';
      }

      const paragraph = `${descriptors[propType]} in extent ${extentStr} ${locationStr} are being sold at rates ranging from ${rateStr}, ${contextPhrase}.`;
      paragraphs.push(paragraph);
    });

    return paragraphs.join(' ');
  };

  const averageRate = calculateAverageRate();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 bg-green-100 rounded-lg">
          <TrendingUp className="h-6 w-6 text-green-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Land Values in the Area</h2>
          <p className="text-sm text-gray-600 mt-1">
            Record comparable property sales to establish market value
          </p>
        </div>
      </div>

      {/* Comparable Properties List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Comparable Properties</Label>
          <Button
            type="button"
            onClick={handleAddComparable}
            variant="outline"
            size="sm"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Comparable
          </Button>
        </div>

        {comparables.length === 0 ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-4">
              No comparable properties added yet
            </p>
            <Button
              type="button"
              onClick={handleAddComparable}
              variant="outline"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add First Comparable
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {comparables.map((comp, index) => (
              <div
                key={comp.id}
                className="border border-gray-300 rounded-lg p-4 bg-white shadow-sm"
              >
                <div className="flex items-start justify-between mb-4">
                  <h4 className="font-medium text-gray-900">
                    Comparable #{index + 1}
                  </h4>
                  <button
                    type="button"
                    onClick={() => handleRemoveComparable(comp.id)}
                    className="text-red-600 hover:text-red-800 transition-colors"
                    title="Remove comparable"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Property Type */}
                  <div>
                    <Label>Property Type</Label>
                    <select
                      value={comp.property_type}
                      onChange={(e) =>
                        handleComparableChange(
                          comp.id,
                          'property_type',
                          e.target.value as 'Commercial' | 'Residential' | 'Agricultural'
                        )
                      }
                      className="mt-1 w-full h-10 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      {PROPERTY_TYPE_OPTIONS.map(type => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Location Description */}
                  <div className="md:col-span-1">
                    <Label>Location / Description</Label>
                    <Input
                      type="text"
                      value={comp.location_description}
                      onChange={(e) =>
                        handleComparableChange(
                          comp.id,
                          'location_description',
                          e.target.value
                        )
                      }
                      placeholder="e.g., Rambukkana town center"
                      className="mt-1"
                    />
                  </div>

                  {/* Extent (Perches) */}
                  <div>
                    <Label>Extent (Perches)</Label>
                    <Input
                      type="number"
                      value={comp.extent || ''}
                      onChange={(e) =>
                        handleComparableChange(
                          comp.id,
                          'extent',
                          parseFloat(e.target.value) || 0
                        )
                      }
                      placeholder="0.00"
                      step="0.01"
                      min="0"
                      className="mt-1"
                    />
                  </div>

                  {/* Rate per Perch */}
                  <div>
                    <Label>Rate per Perch (LKR)</Label>
                    <Input
                      type="number"
                      value={comp.rate_per_perch || ''}
                      onChange={(e) =>
                        handleComparableChange(
                          comp.id,
                          'rate_per_perch',
                          parseFloat(e.target.value) || 0
                        )
                      }
                      placeholder="0.00"
                      step="0.01"
                      min="0"
                      className="mt-1"
                    />
                  </div>

                  {/* Total Value (Auto-calculated) */}
                  <div className="md:col-span-2">
                    <Label>Total Value (Auto-calculated)</Label>
                    <Input
                      type="text"
                      value={formatCurrency(comp.total_value, 2)}
                      readOnly
                      disabled
                      className="mt-1 bg-blue-50 border-blue-200 font-medium"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Summary Card */}
      {comparables.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 mb-3">Market Analysis Summary</h4>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-green-700">Total Comparables</p>
              <p className="text-2xl font-bold text-green-900">{comparables.length}</p>
            </div>
            <div>
              <p className="text-sm text-green-700">Average Rate per Perch</p>
              <p className="text-2xl font-bold text-green-900">
                {formatCurrency(averageRate, 2)}
              </p>
            </div>
          </div>
          <p className="text-xs text-green-700">
            This average rate will be used as the suggested value in the Valuation section
          </p>
        </div>
      )}

      {/* Generated Paragraph Preview */}
      {comparables.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-purple-900">Report Preview</h4>
            <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">
              Auto-generated
            </span>
          </div>
          <div className="bg-white rounded p-4 border border-purple-200">
            <p className="text-sm text-gray-800 leading-relaxed text-justify">
              {generateLandValuesParagraph(comparables)}
            </p>
          </div>
          <p className="text-xs text-purple-700 mt-3">
            This paragraph will appear in the "LAND VALUES IN THE AREA" section of your report
          </p>
        </div>
      )}

      {/* Market Analysis Text */}
      <div>
        <Label>Market Analysis</Label>
        <Textarea
          value={data.land_market_analysis || ''}
          onChange={(e) => onChange({ land_market_analysis: e.target.value })}
          placeholder="Provide additional market analysis, trends, and factors affecting property values in this area..."
          rows={5}
          className="mt-2"
        />
        <p className="text-xs text-gray-500 mt-1">
          Include observations about market trends, demand, development activity, and other factors
          influencing land values
        </p>
      </div>

      {/* Information Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Enter at least 3-5 comparable properties to establish a reliable
          market value. The total value is automatically calculated from extent × rate per perch.
          The average rate will be suggested in the Valuation section.
        </p>
      </div>
    </div>
  );
}
