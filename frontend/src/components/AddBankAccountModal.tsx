import React from 'react';
import { createPortal } from 'react-dom';
import { BankAccount } from '../types';
import { bankAccountApi } from '../services/api';
import BankAccountForm from './BankAccountForm';
import { X } from 'lucide-react';
import toast from 'react-hot-toast';

interface AddBankAccountModalProps {
  onClose: () => void;
  onAccountAdded: (account: BankAccount) => void;
}

const AddBankAccountModal: React.FC<AddBankAccountModalProps> = ({
  onClose,
  onAccountAdded,
}) => {
  const [isLoading, setIsLoading] = React.useState(false);

  const handleSave = async (accountData: any) => {
    setIsLoading(true);
    try {
      const newAccount = await bankAccountApi.create(accountData);
      toast.success('Bank account added successfully');
      onAccountAdded(newAccount);
    } catch (error) {
      console.error('Failed to add bank account:', error);
      toast.error('Failed to add bank account');
    } finally {
      setIsLoading(false);
    }
  };

  // Use portal to render modal outside the parent form context
  // This prevents nested form issues that cause "Leave site?" warnings
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Add Bank Account</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isLoading}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          <p className="text-sm text-gray-600 mb-4">
            Add a bank account to your profile. This account will be available for selection in invoice generation.
          </p>
          <BankAccountForm
            onSave={handleSave}
            onCancel={onClose}
            isEdit={false}
          />
        </div>

        {isLoading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-2xl">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600"></div>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
};

export default AddBankAccountModal;
