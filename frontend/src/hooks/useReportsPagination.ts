import { useState, useEffect, useCallback, useRef } from 'react';
import { Report, ReportStats, ReportFilters } from '../types';
import { reportApi } from '../services/api';

const STORAGE_KEY = 'dashboard_reports_state';
const PAGE_SIZE = 8;
const DEBOUNCE_DELAY = 300;

interface StoredState {
  page: number;
  filters: ReportFilters;
  isFiltersVisible: boolean;
}

interface UseReportsPaginationReturn {
  // Data
  reports: Report[];
  stats: ReportStats;

  // Pagination
  currentPage: number;
  totalPages: number;
  total: number;

  // Filters
  filters: ReportFilters;
  isFiltersVisible: boolean;

  // Loading states
  isLoading: boolean;

  // Actions
  goToNextPage: () => void;
  goToPreviousPage: () => void;
  setFilters: (filters: Partial<ReportFilters>) => void;
  clearFilters: () => void;
  toggleFiltersVisibility: () => void;
  resetAndRefresh: () => void;
}

const defaultStats: ReportStats = {
  total_count: 0,
  this_month_count: 0,
  completed_count: 0,
  draft_count: 0,
};

const defaultFilters: ReportFilters = {
  reference: '',
  applicant_name: '',
  village: '',
  report_date: '',
};

export function useReportsPagination(): UseReportsPaginationReturn {
  // Load initial state from sessionStorage
  const loadStoredState = (): StoredState => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.error('Failed to load stored state:', e);
    }
    return {
      page: 1,
      filters: defaultFilters,
      isFiltersVisible: false,
    };
  };

  const storedState = loadStoredState();

  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<ReportStats>(defaultStats);
  const [currentPage, setCurrentPage] = useState(storedState.page);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFiltersState] = useState<ReportFilters>(storedState.filters);
  const [isFiltersVisible, setIsFiltersVisible] = useState(storedState.isFiltersVisible);
  const [isLoading, setIsLoading] = useState(true);

  // Debounce timer ref
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Save state to sessionStorage
  const saveState = useCallback((state: StoredState) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      console.error('Failed to save state:', e);
    }
  }, []);

  // Fetch reports with current pagination and filters
  const fetchReports = useCallback(async (page: number, currentFilters: ReportFilters) => {
    setIsLoading(true);
    try {
      // Clean up empty filter values before sending
      const cleanFilters: ReportFilters = {};
      if (currentFilters.reference?.trim()) {
        cleanFilters.reference = currentFilters.reference.trim();
      }
      if (currentFilters.applicant_name?.trim()) {
        cleanFilters.applicant_name = currentFilters.applicant_name.trim();
      }
      if (currentFilters.village?.trim()) {
        cleanFilters.village = currentFilters.village.trim();
      }
      if (currentFilters.report_date?.trim()) {
        cleanFilters.report_date = currentFilters.report_date.trim();
      }

      const hasFilters = Object.keys(cleanFilters).length > 0;

      let response;
      try {
        response = await reportApi.getReports(
          page,
          PAGE_SIZE,
          hasFilters ? cleanFilters : undefined
        );
      } catch (apiError) {
        console.error('[useReportsPagination] API call failed:', apiError);
        setReports([]);
        setStats(defaultStats);
        setTotalPages(1);
        setTotal(0);
        return;
      }

      // Handle the paginated response with defensive checks
      const items = response?.items ?? [];
      const responseStats = response?.stats ?? defaultStats;
      const responseTotalPages = response?.total_pages ?? 1;
      const responseTotal = response?.total ?? 0;

      setReports(items);
      setStats(responseStats);
      setTotalPages(responseTotalPages);
      setTotal(responseTotal);

      // If we got no results but we're not on page 1, go to page 1
      if (items.length === 0 && page > 1) {
        setCurrentPage(1);
        return fetchReports(1, currentFilters);
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      setReports([]);
      setStats(defaultStats);
      setTotalPages(1);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save state whenever it changes
  useEffect(() => {
    saveState({
      page: currentPage,
      filters,
      isFiltersVisible,
    });
  }, [currentPage, filters, isFiltersVisible, saveState]);

  // Fetch reports on mount and when page/filters change (with debouncing for filters)
  useEffect(() => {
    // Clear any existing debounce timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Check if any filter has content
    const hasActiveFilters =
      filters.reference?.trim() ||
      filters.applicant_name?.trim() ||
      filters.village?.trim() ||
      filters.report_date?.trim();

    // If filters are being typed, debounce the request
    if (hasActiveFilters) {
      debounceTimer.current = setTimeout(() => {
        fetchReports(currentPage, filters);
      }, DEBOUNCE_DELAY);
    } else {
      // No filters, fetch immediately
      fetchReports(currentPage, filters);
    }

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [currentPage, filters, fetchReports]);

  // Pagination handlers
  const goToNextPage = useCallback(async () => {
    // If we have a date filter and we're on the last page, try to navigate to next date
    if (filters.report_date && currentPage >= totalPages) {
      try {
        const nextDate = await reportApi.getAdjacentReportDate(
          filters.report_date,
          'next'
        );
        if (nextDate) {
          setFiltersState(prev => ({ ...prev, report_date: nextDate }));
          setCurrentPage(1);
          return;
        }
      } catch (error) {
        console.error('Failed to get adjacent date:', error);
      }
    }

    // Normal pagination
    if (currentPage < totalPages) {
      setCurrentPage(prev => prev + 1);
    }
  }, [currentPage, totalPages, filters.report_date]);

  const goToPreviousPage = useCallback(async () => {
    // If we have a date filter and we're on the first page, try to navigate to previous date
    if (filters.report_date && currentPage === 1) {
      try {
        const prevDate = await reportApi.getAdjacentReportDate(
          filters.report_date,
          'previous'
        );
        if (prevDate) {
          // When going to previous date, we want to start at page 1 of that date
          setFiltersState(prev => ({ ...prev, report_date: prevDate }));
          setCurrentPage(1);
          return;
        }
      } catch (error) {
        console.error('Failed to get adjacent date:', error);
      }
    }

    // Normal pagination
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
    }
  }, [currentPage, filters.report_date]);

  // Filter handlers
  const setFilters = useCallback((newFilters: Partial<ReportFilters>) => {
    setFiltersState(prev => ({ ...prev, ...newFilters }));
    // Reset to page 1 when filters change
    setCurrentPage(1);
  }, []);

  const clearFilters = useCallback(() => {
    setFiltersState(defaultFilters);
    setCurrentPage(1);
  }, []);

  const toggleFiltersVisibility = useCallback(() => {
    setIsFiltersVisible(prev => !prev);
  }, []);

  // Reset everything and refresh (used after creating/duplicating reports)
  const resetAndRefresh = useCallback(() => {
    setFiltersState(defaultFilters);
    setCurrentPage(1);
    fetchReports(1, defaultFilters);
  }, [fetchReports]);

  return {
    reports,
    stats,
    currentPage,
    totalPages,
    total,
    filters,
    isFiltersVisible,
    isLoading,
    goToNextPage,
    goToPreviousPage,
    setFilters,
    clearFilters,
    toggleFiltersVisibility,
    resetAndRefresh,
  };
}
