import React, { useState } from 'react';
import { PropertyLocationSection } from '../components/PropertyLocationSection';
import { AccessDirectionsSection } from '../components/AccessDirectionsSection';
import type { Report } from '../types';

export function TestComponents() {
  const [formData, setFormData] = useState<Partial<Report>>({
    // Pre-fill with some test data
    property_village: '',
    property_district: '',
    property_province: '',
  });

  const updateFormData = (updates: Partial<Report>) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  // Sample applicant address
  const applicantAddress = {
    line1: 'No: 43, Highway City',
    line2: 'Kadawatha',
    district: 'Gampaha',
    province: 'Western Province',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Component Testing Page</h1>
          <p className="mt-2 text-gray-600">
            Testing PropertyLocationSection and AccessDirectionsSection components
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {/* Property Location Section */}
        <div className="bg-white p-8 rounded-lg shadow">
          <PropertyLocationSection
            formData={formData}
            updateFormData={updateFormData}
            applicantAddress={applicantAddress}
          />
        </div>

        {/* Access Directions Section */}
        <div className="bg-white p-8 rounded-lg shadow">
          <AccessDirectionsSection
            formData={formData}
            updateFormData={updateFormData}
          />
        </div>

        {/* Debug Panel */}
        <div className="bg-gray-900 text-gray-100 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold">Form Data (Debug Panel)</h3>
            <button
              onClick={() => console.log('Form Data:', formData)}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Log to Console
            </button>
          </div>
          <div className="bg-gray-800 p-4 rounded overflow-auto max-h-96">
            <pre className="text-xs text-green-400">
              {JSON.stringify(formData, null, 2)}
            </pre>
          </div>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-400">Total Fields:</div>
              <div className="text-xl font-bold">{Object.keys(formData).length}</div>
            </div>
            <div>
              <div className="text-gray-400">Filled Fields:</div>
              <div className="text-xl font-bold text-green-400">
                {Object.values(formData).filter(v => v !== '' && v !== null && v !== undefined).length}
              </div>
            </div>
            <div>
              <div className="text-gray-400">Property Location:</div>
              <div className="text-xl font-bold text-blue-400">
                {formData.property_district || 'Not set'}
              </div>
            </div>
            <div>
              <div className="text-gray-400">Route Generated:</div>
              <div className="text-xl font-bold text-purple-400">
                {formData.access_route_data ? 'Yes' : 'No'}
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
          <h3 className="font-bold text-blue-900 mb-3">Testing Instructions:</h3>
          <ol className="space-y-2 text-sm text-blue-800 list-decimal list-inside">
            <li>
              <strong>Test Administrative Dropdowns:</strong> Select a district (e.g., Kurunegala) and watch
              the DS Division dropdown populate with 30 divisions.
            </li>
            <li>
              <strong>Test "Same as Applicant" Toggle:</strong> Check the checkbox at the top of Property Location
              section to auto-fill the address.
            </li>
            <li>
              <strong>Test Municipal Checkbox:</strong> Check "Within Municipal Council Limit" to reveal the
              Ward Number field.
            </li>
            <li>
              <strong>Test Route Generation:</strong> Fill in GPS coordinates for starting point and property,
              then click "Generate Route & Directions".
            </li>
            <li>
              <strong>Check Debug Panel:</strong> Watch the debug panel update as you fill fields.
            </li>
          </ol>
        </div>

        {/* Sample Data */}
        <div className="bg-green-50 border border-green-200 p-6 rounded-lg">
          <h3 className="font-bold text-green-900 mb-3">Sample Test Data:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-green-800 mb-2">Property Location:</h4>
              <ul className="space-y-1 text-green-700">
                <li>Property Number: <code className="bg-white px-2 py-0.5 rounded">No: 1202</code></li>
                <li>Village: <code className="bg-white px-2 py-0.5 rounded">Hanhamunawa</code></li>
                <li>District: <code className="bg-white px-2 py-0.5 rounded">Kurunegala</code></li>
                <li>DS Division: <code className="bg-white px-2 py-0.5 rounded">Bamunakotuwa</code></li>
                <li>GN Division: <code className="bg-white px-2 py-0.5 rounded">Bamunna</code></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-green-800 mb-2">GPS Coordinates:</h4>
              <ul className="space-y-1 text-green-700">
                <li>Property Lat: <code className="bg-white px-2 py-0.5 rounded">7.4867</code></li>
                <li>Property Lng: <code className="bg-white px-2 py-0.5 rounded">80.3642</code></li>
                <li>Starting Lat: <code className="bg-white px-2 py-0.5 rounded">7.4867</code></li>
                <li>Starting Lng: <code className="bg-white px-2 py-0.5 rounded">80.3642</code></li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TestComponents;
