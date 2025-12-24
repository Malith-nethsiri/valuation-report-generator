import React, { useState, useEffect, useRef } from 'react';
import { Scale, Plus, Trash2, Calculator } from 'lucide-react';
import { Button } from './Button';
import { Label } from './Label';
import { Input } from './Input';
import { CalculatedField } from './CalculatedField';
import { Building, BuildingValuation, ValuationComponent, ValuationAddon, ComparableProperty } from '../types';
import { formatCurrency, formatNumber } from '../utils/currency';
import { calculateTotalPerches } from '../utils/extentCalculator';

interface ValuationData {
  // Land valuation
  valuation_land_extent?: number;
  valuation_rate_per_perch?: number;
  valuation_total_land_value?: number;

  // Buildings valuation
  valuation_buildings_data?: BuildingValuation[];
  valuation_total_buildings_value?: number;

  // Add-ons
  valuation_addons?: ValuationAddon[];
  valuation_total_addons_value?: number;

  // Fair value summary
  valuation_market_value?: number;
  valuation_forced_sale_percentage?: number;
  valuation_forced_sale_value?: number;
  valuation_insurance_value?: number;

  // Manual overrides tracking
  valuation_manual_overrides?: Record<string, boolean>;

  // For reference (from previous steps)
  land_extent_perches?: number;
  comparable_properties?: ComparableProperty[];
  buildings?: Building[];
}

interface Props {
  data: ValuationData;
  onChange: (data: Partial<ValuationData>) => void;
  buildings?: Building[];
}

function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Helper function to get default economic life based on building type
function getDefaultEconomicLife(buildingType?: string): number {
  if (!buildingType) return 50; // Default for unspecified buildings

  const type = buildingType.toLowerCase();

  // Residential buildings
  if (type.includes('house') || type.includes('bungalow') || type.includes('villa') ||
      type.includes('apartment') || type.includes('flat') || type.includes('residential')) {
    return 60;
  }

  // Commercial buildings
  if (type.includes('shop') || type.includes('office') || type.includes('commercial') ||
      type.includes('store') || type.includes('showroom')) {
    return 50;
  }

  // Industrial buildings
  if (type.includes('factory') || type.includes('warehouse') || type.includes('industrial') ||
      type.includes('shed') || type.includes('workshop')) {
    return 40;
  }

  // Temporary or light structures
  if (type.includes('temporary') || type.includes('shed') || type.includes('hut') ||
      type.includes('cabin') || type.includes('kiosk')) {
    return 20;
  }

  // Default for any other building type
  return 50;
}

// Depreciation Calculation Functions
function calculateAge(constructionYear: number | null | undefined): number {
  if (!constructionYear || constructionYear <= 0) return 0;
  const currentYear = new Date().getFullYear();
  return Math.max(0, currentYear - constructionYear);
}

function calculateDepreciationRate(age: number, economicLife: number): number {
  if (economicLife <= 0) return 0;
  return Math.min((age / economicLife) * 100, 100);
}

function calculateDepreciationAmount(replacementCost: number, depreciationRate: number): number {
  return replacementCost * (depreciationRate / 100);
}

function calculateDepreciatedValue(replacementCost: number, depreciationAmount: number): number {
  return Math.max(0, replacementCost - depreciationAmount);
}

export default function ValuationSection({ data, onChange, buildings = [] }: Props) {
  // Land valuation state
  const [ratePerPerch, setRatePerPerch] = useState<number>(
    data.valuation_rate_per_perch || 0
  );

  // Buildings valuation state
  const [buildingValuations, setBuildingValuations] = useState<Record<string, BuildingValuation>>(
    {}
  );

  // Add-ons state
  const [addons, setAddons] = useState<ValuationAddon[]>(data.valuation_addons || []);

  // Forced sale percentage
  const [forcedSalePercentage, setForcedSalePercentage] = useState<number>(
    data.valuation_forced_sale_percentage || 90
  );

  // Manual overrides
  const [manualOverrides, setManualOverrides] = useState<Record<string, boolean>>(
    data.valuation_manual_overrides || {}
  );

  // Initialize rate from comparables
  useEffect(() => {
    // Calculate suggested rate from comparables
    if (data.comparable_properties && data.comparable_properties.length > 0 && !data.valuation_rate_per_perch) {
      const avgRate = data.comparable_properties.reduce((sum, c) => sum + c.rate_per_perch, 0) / data.comparable_properties.length;
      setRatePerPerch(avgRate);
    }
  }, [data.comparable_properties]);

  // Initialize building valuations from buildings array with auto-populated components
  useEffect(() => {
    const savedData = data.valuation_buildings_data;

    if (buildings.length > 0 && Object.keys(buildingValuations).length === 0) {
      const initialValuations: Record<string, BuildingValuation> = {};

      buildings.forEach(building => {
        const savedValuation = savedData?.find(v => v.building_id === building.id);

        let component: ValuationComponent;

        if (savedValuation && savedValuation.components.length > 0) {
          // Restore from saved data, update floor_area from current building
          component = {
            ...savedValuation.components[0],
            floor_area: building.total_floor_area || 0,
            value: savedValuation.components[0].units *
                   (building.total_floor_area || 0) *
                   savedValuation.components[0].rate
          };
        } else {
          // Create new auto-populated component
          component = {
            id: generateId(),
            description: building.building_name || building.building_type || 'Building',
            units: 1,
            floor_area: building.total_floor_area || 0,
            rate: 0,
            value: 0
          };
        }

        initialValuations[building.id] = {
          building_id: building.id,
          building_name: building.building_type || building.building_name,
          components: [component],
          subtotal: component.value,
          // Set default economic life based on building type (if saved data has it, use that)
          economic_life_years: savedValuation?.economic_life_years || getDefaultEconomicLife(building.building_type),
          // Restore other depreciation fields from saved data if available
          construction_year: savedValuation?.construction_year,
          age_years: savedValuation?.age_years,
          depreciation_rate_percent: savedValuation?.depreciation_rate_percent,
          depreciation_amount: savedValuation?.depreciation_amount,
          depreciated_value: savedValuation?.depreciated_value
        };
      });

      setBuildingValuations(initialValuations);
    }
  }, [buildings, data.valuation_buildings_data]);

  // Sync buildings changes (additions, removals, floor_area updates)
  const prevBuildingsRef = useRef<Building[]>([]);

  useEffect(() => {
    // Skip if no change or not initialized
    if (JSON.stringify(buildings) === JSON.stringify(prevBuildingsRef.current)) return;
    if (Object.keys(buildingValuations).length === 0) {
      prevBuildingsRef.current = buildings;
      return;
    }

    prevBuildingsRef.current = buildings;
    const updatedValuations = { ...buildingValuations };
    let hasChanges = false;

    // Add new buildings
    buildings.forEach(building => {
      if (!updatedValuations[building.id]) {
        updatedValuations[building.id] = {
          building_id: building.id,
          building_name: building.building_type || building.building_name,
          components: [{
            id: generateId(),
            description: building.building_name || building.building_type || 'Building',
            units: 1,
            floor_area: building.total_floor_area || 0,
            rate: 0,
            value: 0
          }],
          subtotal: 0,
          // Set default economic life for new buildings
          economic_life_years: getDefaultEconomicLife(building.building_type)
        };
        hasChanges = true;
      } else {
        // Update floor_area if changed
        const component = updatedValuations[building.id].components[0];
        if (component && component.floor_area !== building.total_floor_area) {
          component.floor_area = building.total_floor_area || 0;
          component.value = component.units * component.floor_area * component.rate;
          updatedValuations[building.id].subtotal = component.value;
          hasChanges = true;
        }
      }
    });

    // Remove deleted buildings
    const buildingIds = new Set(buildings.map(b => b.id));
    Object.keys(updatedValuations).forEach(buildingId => {
      if (!buildingIds.has(buildingId)) {
        delete updatedValuations[buildingId];
        hasChanges = true;
      }
    });

    if (hasChanges) setBuildingValuations(updatedValuations);
  }, [buildings]);

  // CALCULATIONS
  const calculateLandValue = (): number => {
    const totalPerches = calculateTotalPerches(
      data.land_extent_acres || 0,
      data.land_extent_roods || 0,
      data.land_extent_perches || 0
    );
    return totalPerches * ratePerPerch;
  };

  const calculateComponentValue = (comp: ValuationComponent): number => {
    return comp.units * comp.floor_area * comp.rate;
  };

  const calculateBuildingSubtotal = (buildingId: string): number => {
    const valuation = buildingValuations[buildingId];
    if (!valuation) return 0;
    return valuation.components.reduce((sum, comp) => sum + comp.value, 0);
  };

  const calculateTotalBuildings = (): number => {
    return Object.keys(buildingValuations).reduce(
      (sum, buildingId) => {
        const valuation = buildingValuations[buildingId];
        if (!valuation) return sum;
        // Use depreciated value if available, otherwise use subtotal
        return sum + (valuation.depreciated_value || valuation.subtotal || 0);
      },
      0
    );
  };

  const calculateTotalAddons = (): number => {
    return addons.reduce((sum, addon) => sum + addon.value, 0);
  };

  const calculateTotalBuildingsReplacementCost = (): number => {
    // For insurance value - use replacement cost (undepreciated)
    return Object.keys(buildingValuations).reduce(
      (sum, buildingId) => {
        const valuation = buildingValuations[buildingId];
        if (!valuation) return sum;
        return sum + (valuation.subtotal || 0);
      },
      0
    );
  };

  const calculateMarketValue = (): number => {
    const landValue = manualOverrides.land_value
      ? data.valuation_total_land_value || 0
      : calculateLandValue();

    const buildingsValue = manualOverrides.buildings_value
      ? data.valuation_total_buildings_value || 0
      : calculateTotalBuildings();

    const addonsValue = manualOverrides.addons_value
      ? data.valuation_total_addons_value || 0
      : calculateTotalAddons();

    return landValue + buildingsValue + addonsValue;
  };

  const calculateForcedSaleValue = (): number => {
    const marketValue = manualOverrides.market_value
      ? data.valuation_market_value || 0
      : calculateMarketValue();

    return marketValue * (forcedSalePercentage / 100);
  };

  const calculateInsuranceValue = (): number => {
    // Insurance uses REPLACEMENT COST (not depreciated)
    const buildingsValue = calculateTotalBuildingsReplacementCost();

    const addonsValue = manualOverrides.addons_value
      ? data.valuation_total_addons_value || 0
      : calculateTotalAddons();

    return buildingsValue + addonsValue; // Excludes land
  };


  // HANDLERS
  const handleToggleManualOverride = (field: string) => {
    const newOverrides = { ...manualOverrides, [field]: !manualOverrides[field] };
    setManualOverrides(newOverrides);
    updateParentData({ valuation_manual_overrides: newOverrides });
  };

  const handleRemoveBuilding = (buildingId: string) => {
    setBuildingValuations(prev => {
      const updated = { ...prev };
      delete updated[buildingId];
      return updated;
    });
  };

  const handleComponentChange = (
    buildingId: string,
    componentId: string,
    field: keyof ValuationComponent,
    value: any
  ) => {
    // Prevent editing read-only floor_area
    if (field === 'floor_area') {
      console.warn('Floor area is read-only and sourced from building data');
      return;
    }

    setBuildingValuations(prev => {
      const building = prev[buildingId];
      const updatedComponents = building.components.map(comp => {
        if (comp.id === componentId) {
          const updated = { ...comp, [field]: value };
          // Auto-calculate value when units or rate changes
          if (field === 'units' || field === 'rate') {
            updated.value = calculateComponentValue(updated);
          }
          return updated;
        }
        return comp;
      });

      return {
        ...prev,
        [buildingId]: {
          ...building,
          components: updatedComponents,
          subtotal: updatedComponents.reduce((sum, c) => sum + c.value, 0)
        }
      };
    });
  };

  const handleBuildingValuationUpdate = (buildingId: string, updates: Partial<BuildingValuation>) => {
    setBuildingValuations(prev => {
      const building = prev[buildingId];
      if (!building) return prev;

      return {
        ...prev,
        [buildingId]: {
          ...building,
          ...updates
        }
      };
    });
  };

  const handleAddAddon = () => {
    const newAddon: ValuationAddon = {
      id: generateId(),
      description: '',
      value: 0
    };
    setAddons(prev => [...prev, newAddon]);
  };

  const handleRemoveAddon = (id: string) => {
    setAddons(prev => prev.filter(a => a.id !== id));
  };

  const handleAddonChange = (id: string, field: keyof ValuationAddon, value: any) => {
    setAddons(prev =>
      prev.map(addon => (addon.id === id ? { ...addon, [field]: value } : addon))
    );
  };

  const updateParentData = (updates: Partial<ValuationData>) => {
    const totalPerches = calculateTotalPerches(
      data.land_extent_acres || 0,
      data.land_extent_roods || 0,
      data.land_extent_perches || 0
    );
    onChange({
      valuation_land_extent: totalPerches,
      valuation_rate_per_perch: ratePerPerch,
      valuation_total_land_value: calculateLandValue(),
      valuation_buildings_data: Object.values(buildingValuations),
      valuation_total_buildings_value: calculateTotalBuildings(),
      valuation_addons: addons,
      valuation_total_addons_value: calculateTotalAddons(),
      valuation_market_value: calculateMarketValue(),
      valuation_forced_sale_percentage: forcedSalePercentage,
      valuation_forced_sale_value: calculateForcedSaleValue(),
      valuation_insurance_value: calculateInsuranceValue(),
      ...updates
    });
  };

  // Update parent whenever state changes
  useEffect(() => {
    updateParentData({});
  }, [data.land_extent_acres, data.land_extent_roods, data.land_extent_perches, ratePerPerch, buildingValuations, addons, forcedSalePercentage, manualOverrides]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 bg-indigo-100 rounded-lg">
          <Scale className="h-6 w-6 text-indigo-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Valuation</h2>
          <p className="text-sm text-gray-600 mt-1">
            Comprehensive property valuation breakdown with auto-calculations
          </p>
        </div>
      </div>

      {/* A. LAND VALUATION */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold">
            A
          </div>
          Land Valuation
        </h3>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Land Extent</Label>
              <div className="mt-1 bg-gray-50 border border-gray-300 rounded-lg p-3">
                <div className="grid grid-cols-4 gap-2 mb-2">
                  <div>
                    <div className="text-xs text-gray-600">Acres</div>
                    <div className="text-base font-semibold">{data.land_extent_acres || 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Roods</div>
                    <div className="text-base font-semibold">{data.land_extent_roods || 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Perches</div>
                    <div className="text-base font-semibold">{data.land_extent_perches?.toFixed(2) || '0.00'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Total Perches</div>
                    <div className="text-base font-semibold text-indigo-700">
                      {calculateTotalPerches(
                        data.land_extent_acres || 0,
                        data.land_extent_roods || 0,
                        data.land_extent_perches || 0
                      ).toFixed(2)}
                    </div>
                  </div>
                </div>
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-sm font-medium text-indigo-900">
                    {data.land_extent_formatted || `${data.land_extent_acres || 0}A-${data.land_extent_roods || 0}R-${data.land_extent_perches?.toFixed(1) || '0.0'}P`}
                  </div>
                  {data.land_extent_hectares && (
                    <div className="text-xs text-gray-600 mt-1">
                      {data.land_extent_hectares.toFixed(4)} hectares • {data.land_extent_square_meters?.toFixed(2)} m²
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div>
              <Label>Rate per Perch (LKR)</Label>
              <Input
                type="number"
                value={ratePerPerch || ''}
                onChange={(e) => setRatePerPerch(parseFloat(e.target.value) || 0)}
                step="0.01"
                min="0"
                className="mt-1"
              />
              {data.comparable_properties && data.comparable_properties.length > 0 && (
                <p className="text-xs text-blue-600 mt-1">
                  Suggested from comparables average
                </p>
              )}
            </div>
          </div>

          <CalculatedField
            label="Total Land Value"
            value={data.valuation_total_land_value || calculateLandValue()}
            calculatedValue={calculateLandValue()}
            isManual={!!manualOverrides.land_value}
            onToggle={() => handleToggleManualOverride('land_value')}
            onChange={(val) => onChange({ valuation_total_land_value: val })}
            prefix="LKR"
          />
        </div>
      </div>

      {/* B. BUILDINGS VALUATION */}
      {buildings.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold">
              B
            </div>
            Buildings Valuation
          </h3>

          {Object.keys(buildingValuations).length === 0 && buildings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
              <p className="text-sm text-amber-800 mb-2">
                All buildings have been removed from valuation.
              </p>
              <p className="text-xs text-amber-700">
                Buildings will auto-populate if you modify them in Property Description.
              </p>
            </div>
          )}

          {buildings.map((building, idx) => {
            const valuation = buildingValuations[building.id];
            if (!valuation) return null;

            return (
              <div key={building.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">
                      {building.building_type || building.building_name || `Building ${idx + 1}`}
                      {building.building_name && building.building_name !== building.building_type && (
                        <span className="text-gray-500 text-sm ml-2">({building.building_name})</span>
                      )}
                    </h4>
                    <div className="mt-1 text-xs text-blue-600 italic">
                      Enter the valuation rate per sq.ft below. Floor area is auto-calculated from building floors.
                    </div>
                  </div>
                </div>

                {/* Floor Breakdown */}
                {building.floors && building.floors.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                    <h5 className="text-sm font-semibold text-blue-900 mb-2">Floor Breakdown</h5>
                    <div className="space-y-1 text-xs">
                      {building.floors.map((floor: any, floorIdx: number) => (
                        <div key={floorIdx} className="flex justify-between text-blue-800">
                          <span>{floor.floor_name}</span>
                          <span className="font-medium">{floor.floor_area?.toLocaleString() || 0} sq.ft</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Components Table */}
                {valuation.components.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-200">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">Description</th>
                          <th className="px-3 py-2 text-right font-medium">Units</th>
                          <th className="px-3 py-2 text-right font-medium">Floor Area (sq.ft)</th>
                          <th className="px-3 py-2 text-right font-medium">Rate (LKR/sq.ft)</th>
                          <th className="px-3 py-2 text-right font-medium">Value (LKR)</th>
                          <th className="px-3 py-2"></th>
                        </tr>
                      </thead>
                      <tbody>
                        {valuation.components.map(comp => (
                          <React.Fragment key={comp.id}>
                            <tr className="border-t border-gray-300">
                            <td className="px-3 py-2">
                              <Input
                                type="text"
                                value={comp.description}
                                onChange={(e) =>
                                  handleComponentChange(building.id, comp.id, 'description', e.target.value)
                                }
                                placeholder="e.g., Ground floor, Kitchen"
                                className="min-w-[150px]"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <Input
                                type="number"
                                value={comp.units || ''}
                                onChange={(e) =>
                                  handleComponentChange(building.id, comp.id, 'units', parseFloat(e.target.value) || 0)
                                }
                                min="0"
                                step="1"
                                className="text-right w-20"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <div className="text-right w-24 px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg font-medium text-gray-700">
                                {comp.floor_area?.toLocaleString() || 0}
                              </div>
                            </td>
                            <td className="px-3 py-2">
                              <Input
                                type="number"
                                value={comp.rate || ''}
                                onChange={(e) =>
                                  handleComponentChange(building.id, comp.id, 'rate', parseFloat(e.target.value) || 0)
                                }
                                min="0"
                                step="0.01"
                                className="text-right w-28"
                              />
                            </td>
                            <td className="px-3 py-2 text-right font-medium bg-blue-50">
                              {formatNumber(comp.value, 2)}
                            </td>
                            <td className="px-3 py-2 text-center">
                              <button
                                type="button"
                                onClick={() => handleRemoveBuilding(building.id)}
                                className="text-red-600 hover:text-red-800"
                                title="Remove this building from valuation"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                          {comp.floor_area === 0 && (
                            <tr>
                              <td colSpan={6} className="px-3 py-2">
                                <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-xs text-yellow-800">
                                  Warning: Floor area is 0. Please add floor areas in Property Description for this building.
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                        ))}
                      </tbody>
                      <tfoot className="bg-gray-100 font-semibold">
                        <tr>
                          <td colSpan={4} className="px-3 py-2 text-right">Building Subtotal:</td>
                          <td className="px-3 py-2 text-right text-indigo-700">
                            {formatCurrency(valuation.subtotal, 2)}
                          </td>
                          <td></td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                )}

                {/* Depreciation Section */}
                <div className="border-t pt-4 mt-4">
                  <h5 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Calculator className="h-4 w-4 text-indigo-600" />
                    Depreciation Calculation
                  </h5>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <Label className="text-sm">Construction Year</Label>
                      <Input
                        type="number"
                        value={valuation.construction_year || ''}
                        onChange={(e) => {
                          const year = parseInt(e.target.value) || 0;
                          const age = calculateAge(year);
                          const economicLife = valuation.economic_life_years || getDefaultEconomicLife(building.building_type || '');
                          const depRate = calculateDepreciationRate(age, economicLife);
                          const depAmount = calculateDepreciationAmount(valuation.subtotal, depRate);
                          const depValue = calculateDepreciatedValue(valuation.subtotal, depAmount);

                          handleBuildingValuationUpdate(building.id, {
                            construction_year: year,
                            age_years: age,
                            depreciation_rate_percent: depRate,
                            depreciation_amount: depAmount,
                            depreciated_value: depValue
                          });
                        }}
                        placeholder="e.g., 2010"
                        min="1900"
                        max={new Date().getFullYear()}
                        className="mt-1"
                      />
                    </div>

                    <div>
                      <Label className="text-sm">Age (Years)</Label>
                      <div className="mt-1 px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg font-medium text-gray-700">
                        {valuation.age_years || calculateAge(valuation.construction_year) || 0} years
                      </div>
                    </div>

                    <div>
                      <Label className="text-sm">Economic Life (Years)</Label>
                      <Input
                        type="number"
                        value={valuation.economic_life_years || getDefaultEconomicLife(building.building_type || '')}
                        onChange={(e) => {
                          const economicLife = parseInt(e.target.value) || 50;
                          const age = valuation.age_years || calculateAge(valuation.construction_year);
                          const depRate = calculateDepreciationRate(age, economicLife);
                          const depAmount = calculateDepreciationAmount(valuation.subtotal, depRate);
                          const depValue = calculateDepreciatedValue(valuation.subtotal, depAmount);

                          handleBuildingValuationUpdate(building.id, {
                            economic_life_years: economicLife,
                            depreciation_rate_percent: depRate,
                            depreciation_amount: depAmount,
                            depreciated_value: depValue
                          });
                        }}
                        min="1"
                        max="100"
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Default: {getDefaultEconomicLife(building.building_type || '')} years
                      </p>
                    </div>

                    <div>
                      <Label className="text-sm">Depreciation Rate (%)</Label>
                      <Input
                        type="number"
                        value={valuation.depreciation_rate_percent || ''}
                        onChange={(e) => {
                          const depRate = parseFloat(e.target.value) || 0;
                          const depAmount = calculateDepreciationAmount(valuation.subtotal, depRate);
                          const depValue = calculateDepreciatedValue(valuation.subtotal, depAmount);

                          handleBuildingValuationUpdate(building.id, {
                            depreciation_rate_percent: depRate,
                            depreciation_amount: depAmount,
                            depreciated_value: depValue
                          });
                        }}
                        min="0"
                        max="100"
                        step="0.01"
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Auto-calculated or enter custom rate
                      </p>
                    </div>
                  </div>

                  {/* Depreciation Summary */}
                  <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-700">Replacement Cost:</span>
                        <span className="font-semibold text-gray-900">{formatCurrency(valuation.subtotal, 2)}</span>
                      </div>
                      <div className="flex justify-between text-sm text-red-600">
                        <span>Less: Depreciation ({(valuation.depreciation_rate_percent || 0).toFixed(2)}%):</span>
                        <span className="font-semibold">-{formatCurrency(valuation.depreciation_amount || 0, 2)}</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-indigo-300 text-base font-bold">
                        <span className="text-indigo-900">Depreciated Value:</span>
                        <span className="text-indigo-700">{formatCurrency(valuation.depreciated_value || valuation.subtotal, 2)}</span>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mt-2 italic">
                    💡 Depreciation is calculated using the straight-line method. The depreciated value is used for market value.
                    Insurance value uses the replacement cost (without depreciation).
                  </p>
                </div>
              </div>
            );
          })}

          <CalculatedField
            label="Total Buildings Value"
            value={data.valuation_total_buildings_value || calculateTotalBuildings()}
            calculatedValue={calculateTotalBuildings()}
            isManual={!!manualOverrides.buildings_value}
            onToggle={() => handleToggleManualOverride('buildings_value')}
            onChange={(val) => onChange({ valuation_total_buildings_value: val })}
            prefix="LKR"
          />
        </div>
      )}

      {/* C. ADD-ONS */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold">
            C
          </div>
          Add-ons / Additional Items
        </h3>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
          <Button
            type="button"
            onClick={handleAddAddon}
            variant="outline"
            size="sm"
          >
            <Plus className="h-3 w-3 mr-1" />
            Add Item
          </Button>

          {addons.map((addon, idx) => (
            <div key={addon.id} className="flex items-center gap-3 bg-white p-3 rounded border border-gray-200">
              <span className="text-sm font-medium text-gray-600 w-8">{idx + 1}.</span>
              <Input
                type="text"
                value={addon.description}
                onChange={(e) => handleAddonChange(addon.id, 'description', e.target.value)}
                placeholder="Description (e.g., Swimming pool, Garden landscaping)"
                className="flex-1"
              />
              <Input
                type="number"
                value={addon.value || ''}
                onChange={(e) => handleAddonChange(addon.id, 'value', parseFloat(e.target.value) || 0)}
                placeholder="Value (LKR)"
                step="0.01"
                min="0"
                className="w-40"
              />
              <button
                type="button"
                onClick={() => handleRemoveAddon(addon.id)}
                className="text-red-600 hover:text-red-800"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}

          {addons.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              No add-ons. Click "Add Item" to include additional valuation items like pools, gardens, etc.
            </p>
          )}

          <CalculatedField
            label="Total Add-ons Value"
            value={data.valuation_total_addons_value || calculateTotalAddons()}
            calculatedValue={calculateTotalAddons()}
            isManual={!!manualOverrides.addons_value}
            onToggle={() => handleToggleManualOverride('addons_value')}
            onChange={(val) => onChange({ valuation_total_addons_value: val })}
            prefix="LKR"
          />
        </div>
      </div>

      {/* D. FAIR VALUE SUMMARY */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold">
            D
          </div>
          Fair Value Summary
        </h3>

        <div className="bg-indigo-50 border-2 border-indigo-200 rounded-lg p-6 space-y-4">
          <CalculatedField
            label="Market Value"
            value={data.valuation_market_value || calculateMarketValue()}
            calculatedValue={calculateMarketValue()}
            isManual={!!manualOverrides.market_value}
            onToggle={() => handleToggleManualOverride('market_value')}
            onChange={(val) => onChange({ valuation_market_value: val })}
            prefix="LKR"
            className="border-b border-indigo-200 pb-4"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-b border-indigo-200 pb-4">
            <div>
              <Label>Forced Sale Percentage (%)</Label>
              <Input
                type="number"
                value={forcedSalePercentage || ''}
                onChange={(e) => setForcedSalePercentage(parseFloat(e.target.value) || 90)}
                min="0"
                max="100"
                step="1"
                className="mt-1"
              />
            </div>

            <CalculatedField
              label="Forced Sale Value"
              value={data.valuation_forced_sale_value || calculateForcedSaleValue()}
              calculatedValue={calculateForcedSaleValue()}
              isManual={!!manualOverrides.forced_sale_value}
              onToggle={() => handleToggleManualOverride('forced_sale_value')}
              onChange={(val) => onChange({ valuation_forced_sale_value: val })}
              prefix="LKR"
            />
          </div>

          <CalculatedField
            label="Insurance Value (Buildings + Add-ons, excludes land)"
            value={data.valuation_insurance_value || calculateInsuranceValue()}
            calculatedValue={calculateInsuranceValue()}
            isManual={!!manualOverrides.insurance_value}
            onToggle={() => handleToggleManualOverride('insurance_value')}
            onChange={(val) => onChange({ valuation_insurance_value: val })}
            prefix="LKR"
          />

          {/* Summary Display */}
          <div className="bg-white border border-indigo-300 rounded-lg p-4 mt-4">
            <div className="flex items-center gap-2 mb-3">
              <Calculator className="h-5 w-5 text-indigo-600" />
              <h4 className="font-semibold text-indigo-900">Valuation Summary</h4>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-700">Land Value:</span>
                <span className="font-medium">{formatCurrency(calculateLandValue(), 2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Buildings Value:</span>
                <span className="font-medium">{formatCurrency(calculateTotalBuildings(), 2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Add-ons Value:</span>
                <span className="font-medium">{formatCurrency(calculateTotalAddons(), 2)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-gray-300 text-base">
                <span className="font-semibold text-indigo-900">Total Market Value:</span>
                <span className="font-bold text-indigo-900">{formatCurrency(calculateMarketValue(), 2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Information Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Hybrid Calculations:</strong> Fields with a lock icon are auto-calculated but can be unlocked
          for manual entry. The system tracks which values were manually overridden for reporting purposes.
        </p>
      </div>
    </div>
  );
}
