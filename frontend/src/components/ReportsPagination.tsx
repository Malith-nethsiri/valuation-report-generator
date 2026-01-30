import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface ReportsPaginationProps {
  currentPage: number;
  totalPages: number;
  total: number;
  onPreviousPage: () => void;
  onNextPage: () => void;
  isLoading?: boolean;
}

export const ReportsPagination: React.FC<ReportsPaginationProps> = ({
  currentPage,
  totalPages,
  total,
  onPreviousPage,
  onNextPage,
  isLoading = false,
}) => {
  const canGoPrevious = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  if (total === 0) {
    return null;
  }

  return (
    <div className="flex items-center justify-center gap-4 pt-4">
      {/* Previous button */}
      <button
        onClick={onPreviousPage}
        disabled={isLoading}
        className={`
          p-2 rounded-xl transition-all duration-200
          ${canGoPrevious
            ? 'text-violet-600 hover:bg-violet-100 hover:shadow-md active:scale-95'
            : 'text-gray-300 cursor-default'
          }
          ${isLoading ? 'opacity-50' : ''}
        `}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-6 w-6" />
      </button>

      {/* Page indicator */}
      <div className="flex items-center gap-2 text-sm text-gray-600 min-w-[100px] justify-center">
        <span className="font-semibold text-gray-900">{currentPage}</span>
        <span>/</span>
        <span>{totalPages}</span>
      </div>

      {/* Next button */}
      <button
        onClick={onNextPage}
        disabled={isLoading}
        className={`
          p-2 rounded-xl transition-all duration-200
          ${canGoNext
            ? 'text-violet-600 hover:bg-violet-100 hover:shadow-md active:scale-95'
            : 'text-gray-300 cursor-default'
          }
          ${isLoading ? 'opacity-50' : ''}
        `}
        aria-label="Next page"
      >
        <ChevronRight className="h-6 w-6" />
      </button>
    </div>
  );
};
