/**
 * VehicleLibrarySelector - Modal for selecting vehicle templates from library
 *
 * Used in multi-property context to quickly add vehicles from saved templates.
 * Shows a searchable list of templates with key info.
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Search,
  Car,
  Library,
  Calendar,
  Loader2,
  Plus,
  ChevronRight,
} from 'lucide-react';
import { vehicleApi } from '../../services/api';
import type { VehicleTemplate } from '../../types';

interface VehicleLibrarySelectorProps {
  isOpen: boolean;
  onSelect: (template: VehicleTemplate) => void;
  onCreateNew: () => void;
  onClose: () => void;
}

export const VehicleLibrarySelector: React.FC<VehicleLibrarySelectorProps> = ({
  isOpen,
  onSelect,
  onCreateNew,
  onClose,
}) => {
  const [templates, setTemplates] = useState<VehicleTemplate[]>([]);
  const [filteredTemplates, setFilteredTemplates] = useState<VehicleTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Load templates when modal opens
  useEffect(() => {
    if (isOpen) {
      loadTemplates();
      setSearchQuery('');
    }
  }, [isOpen]);

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
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onKeyDown={handleKeyDown}>
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                <Library className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Vehicle Library</h3>
                <p className="text-sm text-white/80">
                  Select a template or create a new vehicle
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="px-6 py-4 border-b border-gray-200 flex-shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by make, model, or registration..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Create New Option */}
          <button
            onClick={onCreateNew}
            className="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-dashed border-gray-300 hover:border-cyan-400 hover:bg-cyan-50/50 transition-all mb-4 group"
          >
            <div className="p-3 bg-cyan-100 rounded-xl group-hover:bg-cyan-200 transition-colors">
              <Plus className="h-6 w-6 text-cyan-600" />
            </div>
            <div className="flex-1 text-left">
              <h4 className="font-semibold text-gray-900">Create New Vehicle</h4>
              <p className="text-sm text-gray-500">Start from scratch with a blank form</p>
            </div>
            <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-cyan-500" />
          </button>

          {/* Loading */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-cyan-500" />
              <span className="ml-2 text-gray-600">Loading templates...</span>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && templates.length === 0 && (
            <div className="text-center py-8">
              <Library className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No saved templates yet</p>
              <p className="text-sm text-gray-400">
                Create a vehicle and save it to the library for quick reuse
              </p>
            </div>
          )}

          {/* No Search Results */}
          {!isLoading && templates.length > 0 && filteredTemplates.length === 0 && (
            <div className="text-center py-8">
              <Search className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No templates match your search</p>
            </div>
          )}

          {/* Templates List */}
          {!isLoading && filteredTemplates.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-500 mb-3">
                Saved Templates ({filteredTemplates.length})
              </h4>
              {filteredTemplates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => onSelect(template)}
                  className="w-full flex items-center gap-4 p-4 rounded-xl border border-gray-200 hover:border-cyan-400 hover:bg-cyan-50/50 transition-all group text-left"
                >
                  <div className="p-3 bg-gray-100 rounded-xl group-hover:bg-cyan-100 transition-colors">
                    <Car className="h-5 w-5 text-gray-600 group-hover:text-cyan-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-gray-900 truncate">
                      {template.make || 'Unknown'} {template.model || ''}
                    </h4>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      {template.registration_number && (
                        <span>{template.registration_number}</span>
                      )}
                      {template.year_of_manufacture && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {template.year_of_manufacture}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-cyan-500 flex-shrink-0" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex-shrink-0">
          <button
            onClick={onClose}
            className="w-full px-4 py-2.5 text-gray-700 font-medium rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default VehicleLibrarySelector;
