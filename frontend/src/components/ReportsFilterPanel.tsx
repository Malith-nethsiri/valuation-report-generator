import React from 'react';
import { X, Search, Calendar, User, MapPin, Hash } from 'lucide-react';
import { ReportFilters } from '../types';

interface ReportsFilterPanelProps {
  isVisible: boolean;
  filters: ReportFilters;
  onFilterChange: (filters: Partial<ReportFilters>) => void;
  onClearFilters: () => void;
  isLoading?: boolean;
}

export const ReportsFilterPanel: React.FC<ReportsFilterPanelProps> = ({
  isVisible,
  filters,
  onFilterChange,
  onClearFilters,
  isLoading = false,
}) => {
  const hasActiveFilters =
    filters.reference?.trim() ||
    filters.applicant_name?.trim() ||
    filters.village?.trim() ||
    filters.report_date?.trim();

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className={`
        overflow-hidden transition-all duration-300 ease-in-out
        ${isVisible ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}
      `}
    >
      <div className="bg-gray-50/80 backdrop-blur-sm rounded-2xl border border-gray-200/50 p-4 mb-4">
        {/* Header with Clear button */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Search className="h-4 w-4" />
            <span className="font-medium">Search Filters</span>
            {isLoading && (
              <div className="animate-spin h-4 w-4 border-2 border-violet-500 border-t-transparent rounded-full" />
            )}
          </div>
          {hasActiveFilters && (
            <button
              onClick={onClearFilters}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-all duration-200"
            >
              <X className="h-4 w-4" />
              Clear All
            </button>
          )}
        </div>

        {/* Filter Grid - 2 rows */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Row 1: Reference Number + Applicant Name */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Hash className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Reference Number"
              value={filters.reference || ''}
              onChange={(e) => onFilterChange({ reference: e.target.value })}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200 text-sm"
            />
          </div>

          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Applicant Name"
              value={filters.applicant_name || ''}
              onChange={(e) => onFilterChange({ applicant_name: e.target.value })}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200 text-sm"
            />
          </div>

          {/* Row 2: Village + Date */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MapPin className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Village Name"
              value={filters.village || ''}
              onChange={(e) => onFilterChange({ village: e.target.value })}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200 text-sm"
            />
          </div>

          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Calendar className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="date"
              placeholder="Report Date"
              value={filters.report_date || ''}
              onChange={(e) => onFilterChange({ report_date: e.target.value })}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all duration-200 text-sm"
            />
          </div>
        </div>

        {/* Active filters summary */}
        {hasActiveFilters && (
          <div className="mt-3 flex flex-wrap gap-2">
            {filters.reference?.trim() && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-violet-100 text-violet-700 text-xs rounded-lg">
                <Hash className="h-3 w-3" />
                {filters.reference}
                <button
                  onClick={() => onFilterChange({ reference: '' })}
                  className="ml-1 hover:text-violet-900"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.applicant_name?.trim() && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-violet-100 text-violet-700 text-xs rounded-lg">
                <User className="h-3 w-3" />
                {filters.applicant_name}
                <button
                  onClick={() => onFilterChange({ applicant_name: '' })}
                  className="ml-1 hover:text-violet-900"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.village?.trim() && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-violet-100 text-violet-700 text-xs rounded-lg">
                <MapPin className="h-3 w-3" />
                {filters.village}
                <button
                  onClick={() => onFilterChange({ village: '' })}
                  className="ml-1 hover:text-violet-900"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.report_date?.trim() && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-violet-100 text-violet-700 text-xs rounded-lg">
                <Calendar className="h-3 w-3" />
                {new Date(filters.report_date).toLocaleDateString()}
                <button
                  onClick={() => onFilterChange({ report_date: '' })}
                  className="ml-1 hover:text-violet-900"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
