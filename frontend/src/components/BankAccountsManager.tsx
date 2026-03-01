import React, { useState, useEffect } from 'react';
import { CreditCard, Edit, Trash2, Plus } from 'lucide-react';
import { Button } from './Button';
import { bankAccountApi } from '../services/api';
import { BankAccount } from '../types';
import AddBankAccountModal from './AddBankAccountModal';
import BankAccountForm from './BankAccountForm';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';
import toast from 'react-hot-toast';

const BankAccountsManager: React.FC = () => {
    const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
    const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
    const [showAddAccountModal, setShowAddAccountModal] = useState(false);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [accountToDelete, setAccountToDelete] = useState<BankAccount | null>(null);

    useEffect(() => {
        const loadBankAccounts = async () => {
            try {
                const accounts = await bankAccountApi.getAll();
                setBankAccounts(accounts);
            } catch (err) {
                console.error('Failed to load bank accounts:', err);
            }
        };

        loadBankAccounts();
    }, []);

    const handleAddAccount = async (accountData: any) => {
        try {
            const newAccount = await bankAccountApi.create(accountData);
            setBankAccounts([...bankAccounts, newAccount]);
            setShowAddAccountModal(false);
            toast.success('Bank account added successfully');
        } catch (error) {
            console.error('Failed to add bank account:', error);
            toast.error('Failed to add bank account');
        }
    };

    const handleUpdateAccount = async (accountId: string, updateData: any) => {
        try {
            const updated = await bankAccountApi.update(accountId, updateData);
            setBankAccounts(bankAccounts.map(acc => acc.id === accountId ? updated : acc));
            setEditingAccountId(null);
            toast.success('Bank account updated successfully');
        } catch (error) {
            console.error('Failed to update bank account:', error);
            toast.error('Failed to update bank account');
        }
    };

    const handleDeleteClick = (account: BankAccount) => {
        setAccountToDelete(account);
        setDeleteConfirmOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!accountToDelete) return;

        try {
            await bankAccountApi.delete(accountToDelete.id);
            setBankAccounts(bankAccounts.filter(acc => acc.id !== accountToDelete.id));
            toast.success('Bank account deleted successfully');
        } catch (error) {
            console.error('Failed to delete bank account:', error);
            toast.error('Failed to delete bank account');
        } finally {
            setAccountToDelete(null);
            setDeleteConfirmOpen(false);
        }
    };

    return (
        <>
            <section>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                        <CreditCard className="mr-2 text-emerald-600" />
                        Bank Accounts (Optional)
                    </h2>
                    <Button
                        type="button"
                        onClick={() => setShowAddAccountModal(true)}
                        className="flex items-center px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm"
                    >
                        <Plus className="h-4 w-4 mr-2" />
                        Add Account
                    </Button>
                </div>

                <p className="text-sm text-gray-600 mb-4">
                    Add bank accounts to your profile for quick selection when generating invoices.
                    These accounts are optional and can be updated anytime.
                </p>

                {bankAccounts.length === 0 ? (
                    <div className="bg-gray-50 rounded-lg p-6 text-center border-2 border-dashed border-gray-300">
                        <CreditCard className="mx-auto h-12 w-12 text-gray-400 mb-3" />
                        <p className="text-gray-600">No bank accounts added yet.</p>
                        <p className="text-sm text-gray-500 mt-1">Add accounts to include in invoices.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {bankAccounts.map(account => (
                            <div key={account.id} className="bg-white border border-gray-200 rounded-lg p-4">
                                {editingAccountId === account.id ? (
                                    <BankAccountForm
                                        initialData={account}
                                        onSave={(updateData) => handleUpdateAccount(account.id, updateData)}
                                        onCancel={() => setEditingAccountId(null)}
                                        isEdit={true}
                                    />
                                ) : (
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <p className="font-semibold text-gray-900">{account.bank_name}</p>
                                            <p className="text-sm text-gray-600 mt-1">Account: {account.account_number}</p>
                                            <p className="text-sm text-gray-600">Branch: {account.branch_name}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                type="button"
                                                onClick={() => setEditingAccountId(account.id)}
                                                className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded"
                                            >
                                                <Edit className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                type="button"
                                                onClick={() => handleDeleteClick(account)}
                                                className="p-2 bg-red-100 hover:bg-red-200 text-red-700 rounded"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {showAddAccountModal && (
                <AddBankAccountModal
                    onClose={() => setShowAddAccountModal(false)}
                    onAccountAdded={(newAccount) => {
                        setBankAccounts([...bankAccounts, newAccount]);
                        setShowAddAccountModal(false);
                    }}
                />
            )}

            <DeleteConfirmDialog
                isOpen={deleteConfirmOpen}
                onClose={() => {
                    setDeleteConfirmOpen(false);
                    setAccountToDelete(null);
                }}
                onConfirm={handleDeleteConfirm}
                title="Delete Bank Account"
                description={`Are you sure you want to delete the bank account "${accountToDelete?.bank_name}"? This action cannot be undone.`}
                confirmButtonText="Delete Account"
            />
        </>
    );
};

export default BankAccountsManager;
