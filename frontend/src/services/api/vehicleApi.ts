import type {
  Vehicle,
  VehicleCreate,
  VehicleUpdate,
  VehicleTemplate,
  ReportVehicle,
  VehicleValuationSuggestion,
} from '../../types';
import { api } from './client';

export const vehicleApi = {
  // Get all vehicles for the authenticated user
  getVehicles: async (skip: number = 0, limit: number = 100): Promise<Vehicle[]> => {
    const response = await api.get<Vehicle[]>(`/api/vehicles?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Get vehicle templates (Vehicle Library)
  getTemplates: async (): Promise<VehicleTemplate[]> => {
    const response = await api.get<VehicleTemplate[]>('/api/vehicles/templates');
    return response.data;
  },

  // Get a specific vehicle by ID
  getVehicle: async (id: number): Promise<Vehicle> => {
    const response = await api.get<Vehicle>(`/api/vehicles/${id}`);
    return response.data;
  },

  // Create a new vehicle
  createVehicle: async (vehicleData: VehicleCreate): Promise<Vehicle> => {
    const response = await api.post<Vehicle>('/api/vehicles', vehicleData);
    return response.data;
  },

  // Update a vehicle
  updateVehicle: async (id: number, vehicleData: VehicleUpdate): Promise<Vehicle> => {
    const response = await api.put<Vehicle>(`/api/vehicles/${id}`, vehicleData);
    return response.data;
  },

  // Delete a vehicle (soft delete by default)
  deleteVehicle: async (id: number, hardDelete: boolean = false): Promise<void> => {
    await api.delete(`/api/vehicles/${id}?hard_delete=${hardDelete}`);
  },

  // Duplicate a vehicle
  duplicateVehicle: async (id: number): Promise<Vehicle> => {
    const response = await api.post<Vehicle>(`/api/vehicles/${id}/duplicate`);
    return response.data;
  },

  // Get AI valuation suggestion
  getValuationSuggestion: async (id: number): Promise<VehicleValuationSuggestion> => {
    const response = await api.post<VehicleValuationSuggestion>(`/api/vehicles/${id}/suggest-valuation`);
    return response.data;
  },

  // Add vehicle to a report
  addToReport: async (reportId: number, vehicleId: number, vehicleOrder?: number): Promise<ReportVehicle> => {
    const params = vehicleOrder ? `?vehicle_order=${vehicleOrder}` : '';
    const response = await api.post<ReportVehicle>(`/api/reports/${reportId}/vehicles/${vehicleId}${params}`);
    return response.data;
  },

  // Remove vehicle from a report
  removeFromReport: async (reportId: number, vehicleId: number): Promise<void> => {
    await api.delete(`/api/reports/${reportId}/vehicles/${vehicleId}`);
  },

  // Get all vehicles for a report
  getReportVehicles: async (reportId: number): Promise<ReportVehicle[]> => {
    const response = await api.get<ReportVehicle[]>(`/api/reports/${reportId}/vehicles`);
    return response.data;
  },

  // Update a vehicle within a report
  updateReportVehicle: async (reportId: number, vehicleId: number, vehicleData: VehicleUpdate): Promise<Vehicle> => {
    const response = await api.put<Vehicle>(`/api/reports/${reportId}/vehicles/${vehicleId}`, vehicleData);
    return response.data;
  },

  // Reorder vehicles in a report
  reorderReportVehicles: async (reportId: number, vehicleOrderMap: Record<number, number>): Promise<void> => {
    await api.put(`/api/reports/${reportId}/vehicles/reorder`, vehicleOrderMap);
  },
};
