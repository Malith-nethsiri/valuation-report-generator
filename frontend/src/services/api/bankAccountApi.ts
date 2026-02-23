import type { BankAccount, BankAccountCreate, BankAccountUpdate } from '../../types';
import { api } from './client';

export const bankAccountApi = {
  getAll: async (): Promise<BankAccount[]> => {
    const response = await api.get<BankAccount[]>('/api/users/me/bank-accounts');
    return response.data;
  },

  create: async (account: BankAccountCreate): Promise<BankAccount> => {
    const response = await api.post<BankAccount>('/api/users/me/bank-accounts', account);
    return response.data;
  },

  update: async (accountId: string, account: BankAccountUpdate): Promise<BankAccount> => {
    const response = await api.patch<BankAccount>(`/api/users/me/bank-accounts/${accountId}`, account);
    return response.data;
  },

  delete: async (accountId: string): Promise<void> => {
    await api.delete(`/api/users/me/bank-accounts/${accountId}`);
  },
};
