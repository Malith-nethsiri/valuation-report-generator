/**
 * Tests for the unified PropertyReportForm component.
 * Covers bare land and residential modes: rendering, data cleaning, draft keys.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    loading: vi.fn(),
  },
  Toaster: () => null,
}));

// Mock the AuthContext
const mockUser = {
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
};

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isLoading: false,
    isAuthenticated: true,
  }),
}));

// Mock the API
vi.mock('../../services/api', () => ({
  reportApi: {
    getReport: vi.fn(),
    createReport: vi.fn(),
    updateReport: vi.fn(),
  },
  generateReportDocx: vi.fn(),
}));

// Mock secureStorage
vi.mock('../../utils/secureStorage', () => ({
  authTokenStorage: {
    getToken: () => 'mock-token',
    setToken: vi.fn(),
    removeToken: vi.fn(),
  },
}));

// Mock react-router-dom useParams
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({}),
  };
});

// Mock MultiStepForm to avoid deep dependency tree
vi.mock('../../components/MultiStepForm', () => ({
  default: ({ onSubmit, reportType }: any) => (
    <div data-testid="multi-step-form" data-report-type={reportType || 'default'}>
      <button
        data-testid="submit-btn"
        onClick={() => onSubmit({ property_photos: [] }, 'complete')}
      >
        Submit
      </button>
    </div>
  ),
  ResidentialPropertyFormData: {},
}));

import PropertyReportForm from '../../pages/PropertyReportForm';

describe('PropertyReportForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Bare Land mode', () => {
    it('renders without errors', () => {
      render(
        <BrowserRouter>
          <PropertyReportForm reportType="bare_land" />
        </BrowserRouter>
      );

      expect(screen.getByText(/creating bare land report as/i)).toBeTruthy();
      expect(screen.getByText('Test User')).toBeTruthy();
    });

    it('passes reportType="bare_land" to MultiStepForm', () => {
      render(
        <BrowserRouter>
          <PropertyReportForm reportType="bare_land" />
        </BrowserRouter>
      );

      const form = screen.getByTestId('multi-step-form');
      expect(form.getAttribute('data-report-type')).toBe('bare_land');
    });

    it('clears correct localStorage keys on submit', async () => {
      const { reportApi } = await import('../../services/api');
      vi.mocked(reportApi.createReport).mockResolvedValueOnce({
        id: 1,
        created_at: new Date().toISOString(),
        applicant_full_name: 'Test',
      });

      localStorage.setItem('bareLandFormDraft', 'test');
      localStorage.setItem('bareLandFormStep', '2');

      render(
        <BrowserRouter>
          <PropertyReportForm reportType="bare_land" />
        </BrowserRouter>
      );

      const submitBtn = screen.getByTestId('submit-btn');
      submitBtn.click();

      await waitFor(() => {
        expect(localStorage.getItem('bareLandFormDraft')).toBeNull();
        expect(localStorage.getItem('bareLandFormStep')).toBeNull();
      });
    });
  });

  describe('Residential Property mode', () => {
    it('renders without errors', () => {
      render(
        <BrowserRouter>
          <PropertyReportForm reportType="residential_property" />
        </BrowserRouter>
      );

      expect(screen.getByText(/creating residential property report as/i)).toBeTruthy();
    });

    it('passes no reportType to MultiStepForm for residential', () => {
      render(
        <BrowserRouter>
          <PropertyReportForm reportType="residential_property" />
        </BrowserRouter>
      );

      const form = screen.getByTestId('multi-step-form');
      expect(form.getAttribute('data-report-type')).toBe('default');
    });

    it('clears correct localStorage keys on submit', async () => {
      const { reportApi } = await import('../../services/api');
      vi.mocked(reportApi.createReport).mockResolvedValueOnce({
        id: 2,
        created_at: new Date().toISOString(),
        applicant_full_name: 'Test',
      });

      localStorage.setItem('residentialFormDraft', 'test');
      localStorage.setItem('residentialFormStep', '3');

      render(
        <BrowserRouter>
          <PropertyReportForm reportType="residential_property" />
        </BrowserRouter>
      );

      const submitBtn = screen.getByTestId('submit-btn');
      submitBtn.click();

      await waitFor(() => {
        expect(localStorage.getItem('residentialFormDraft')).toBeNull();
        expect(localStorage.getItem('residentialFormStep')).toBeNull();
      });
    });
  });
});
