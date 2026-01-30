/**
 * VehicleLibraryPage - Page for managing saved vehicle templates
 *
 * Features:
 * - Display all saved vehicle templates in a grid
 * - Quick actions: Use template, View/Edit, Delete
 * - Search/filter by make, model, registration
 * - Empty state when no templates saved
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Car,
  Plus,
  Search,
  Trash2,
  Copy,
  ArrowLeft,
  Library,
  Calendar,
  Gauge,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { vehicleApi } from '../services/api';
import type { VehicleTemplate, Vehicle } from '../types';
import { Button } from '../components/Button';

const VehicleLibraryPage: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<VehicleTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<VehicleTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);

  // Filter templates when search changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredTemplates(templates);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredTemplates(
        templates.filter(
          (t) =>
            t.make?.toLowerCase().includes(query) ||
            t.model?.toLowerCase().includes(query) ||
            t.registration_number?.toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, templates]);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      const data = await vehicleApi.getTemplates();
      setTemplates(data);
      setFilteredTemplates(data);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast.error('Failed to load vehicle library');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseTemplate = async (template: VehicleTemplate) => {
    try {
      // Get full vehicle data
      const fullVehicle = await vehicleApi.getVehicle(template.id);

      // Create a copy of the vehicle (not a template)
      const vehicleData = {
        ...fullVehicle,
        is_template: false,
        status: 'draft',
        registration_number: '', // Clear unique identifiers
      };
      delete (vehicleData as any).id;
      delete (vehicleData as any).user_id;
      delete (vehicleData as any).created_at;
      delete (vehicleData as any).updated_at;

      const newVehicle = await vehicleApi.createVehicle(vehicleData);
      toast.success('Vehicle created from template');
      navigate(`/reports/vehicle/${newVehicle.id}`);
    } catch (error) {
      console.error('Error using template:', error);
      toast.error('Failed to create vehicle from template');
    }
  };

  const handleDeleteTemplate = async (templateId: number) => {
    if (!window.confirm('Are you sure you want to delete this template from the library?')) {
      return;
    }

    try {
      setDeletingId(templateId);
      // Update the vehicle to remove template flag (soft delete from library)
      await vehicleApi.updateVehicle(templateId, { is_template: false });
      setTemplates((prev) => prev.filter((t) => t.id !== templateId));
      toast.success('Template removed from library');
    } catch (error) {
      console.error('Error deleting template:', error);
      toast.error('Failed to delete template');
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const formatCurrency = (value?: number) => {
    if (!value) return '-';
    return `Rs. ${value.toLocaleString()}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50/30">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                to="/dashboard"
                className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors duration-200"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to Dashboard
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl shadow-lg">
                <Library className="h-5 w-5 text-white" />
              </div>
              <div className="text-right">
                <h1 className="font-semibold text-gray-900">Vehicle Library</h1>
                <p className="text-sm text-gray-500">
                  {templates.length} saved template{templates.length !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search & Actions Bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by make, model, or registration..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500 bg-white"
            />
          </div>

          {/* New Vehicle Button */}
          <Link to="/reports/new/vehicle">
            <Button className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700">
              <Plus className="h-5 w-5" />
              New Vehicle Report
            </Button>
          </Link>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
            <span className="ml-2 text-gray-600">Loading library...</span>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && templates.length === 0 && (
          <div className="text-center py-16">
            <div className="inline-flex p-4 bg-cyan-50 rounded-full mb-4">
              <Library className="h-12 w-12 text-cyan-500" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No vehicles in library</h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Save vehicles to your library for quick reuse. When creating or editing a vehicle
              report, click "Save to Library" to add it here.
            </p>
            <Link to="/reports/new/vehicle">
              <Button className="bg-gradient-to-r from-cyan-500 to-blue-600">
                <Plus className="h-5 w-5 mr-2" />
                Create Your First Vehicle Report
              </Button>
            </Link>
          </div>
        )}

        {/* No Search Results */}
        {!isLoading && templates.length > 0 && filteredTemplates.length === 0 && (
          <div className="text-center py-16">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No matches found</h3>
            <p className="text-gray-600">Try adjusting your search query</p>
          </div>
        )}

        {/* Templates Grid */}
        {!isLoading && filteredTemplates.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTemplates.map((template) => (
              <div
                key={template.id}
                className="bg-white rounded-2xl border border-gray-200/50 shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden group"
              >
                {/* Card Header */}
                <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/20 rounded-lg">
                      <Car className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white truncate">
                        {template.make || 'Unknown'} {template.model || ''}
                      </h3>
                      <p className="text-sm text-white/80 truncate">
                        {template.registration_number || 'No registration'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 space-y-3">
                  {/* Year */}
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <span>Year: {template.year_of_manufacture || '-'}</span>
                  </div>

                  {/* Market Value */}
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Gauge className="h-4 w-4 text-gray-400" />
                    <span>Value: {formatCurrency(template.market_value)}</span>
                  </div>

                  {/* Created Date */}
                  <div className="text-xs text-gray-400">
                    Saved on {formatDate(template.created_at)}
                  </div>
                </div>

                {/* Card Actions */}
                <div className="px-5 py-4 bg-gray-50 border-t border-gray-100 flex gap-2">
                  <button
                    onClick={() => handleUseTemplate(template)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Copy className="h-4 w-4" />
                    Use Template
                  </button>
                  <button
                    onClick={() => handleDeleteTemplate(template.id)}
                    disabled={deletingId === template.id}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    title="Remove from library"
                  >
                    {deletingId === template.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default VehicleLibraryPage;
