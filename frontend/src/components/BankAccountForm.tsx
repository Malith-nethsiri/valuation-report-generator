import React, { useState } from 'react';
import { BankAccount, BankAccountCreate, BankAccountUpdate } from '../types';
import { Input } from './Input';
import { Label } from './Label';
import { Button } from './Button';

interface BankAccountFormProps {
  initialData?: BankAccount;
  onSave: (data: BankAccountCreate | BankAccountUpdate) => void;
  onCancel: () => void;
  isEdit?: boolean;
}

const SRI_LANKAN_BANKS = [
  'Bank of Ceylon',
  'People\'s Bank',
  'Commercial Bank of Ceylon',
  'Hatton National Bank',
  'Sampath Bank',
  'Nations Trust Bank',
  'DFCC Bank',
  'Seylan Bank',
  'Union Bank',
  'Pan Asia Banking Corporation',
  'National Development Bank',
  'Cargills Bank',
  'Amana Bank',
  'ICICI Bank',
  'Standard Chartered Bank',
  'Citibank',
  'HSBC',
];

const BankAccountForm: React.FC<BankAccountFormProps> = ({
  initialData,
  onSave,
  onCancel,
  isEdit = false,
}) => {
  const [formData, setFormData] = useState({
    bank_name: initialData?.bank_name || '',
    account_number: initialData?.account_number || '',
    branch_name: initialData?.branch_name || '',
  });

  const [errors, setErrors] = useState({
    bank_name: '',
    account_number: '',
    branch_name: '',
  });

  const [showBankSuggestions, setShowBankSuggestions] = useState(false);
  const [filteredBanks, setFilteredBanks] = useState<string[]>([]);

  const handleBankNameChange = (value: string) => {
    setFormData({ ...formData, bank_name: value });
    setErrors({ ...errors, bank_name: '' });

    // Filter banks based on input
    if (value) {
      const filtered = SRI_LANKAN_BANKS.filter(bank =>
        bank.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredBanks(filtered);
      setShowBankSuggestions(true);
    } else {
      setFilteredBanks([]);
      setShowBankSuggestions(false);
    }
  };

  const handleBankSelect = (bank: string) => {
    setFormData({ ...formData, bank_name: bank });
    setShowBankSuggestions(false);
    setFilteredBanks([]);
  };

  const validateForm = () => {
    const newErrors = {
      bank_name: '',
      account_number: '',
      branch_name: '',
    };

    let isValid = true;

    if (!formData.bank_name.trim()) {
      newErrors.bank_name = 'Bank name is required';
      isValid = false;
    }

    if (!formData.account_number.trim()) {
      newErrors.account_number = 'Account number is required';
      isValid = false;
    }

    if (!formData.branch_name.trim()) {
      newErrors.branch_name = 'Branch name is required';
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (validateForm()) {
      onSave(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} action="#" className="space-y-4 bg-white rounded-lg p-4 border border-gray-200">
      <div>
        <Label htmlFor="bank_name">Bank Name</Label>
        <div className="relative">
          <Input
            id="bank_name"
            type="text"
            value={formData.bank_name}
            onChange={(e) => handleBankNameChange(e.target.value)}
            onFocus={() => {
              if (formData.bank_name) {
                const filtered = SRI_LANKAN_BANKS.filter(bank =>
                  bank.toLowerCase().includes(formData.bank_name.toLowerCase())
                );
                setFilteredBanks(filtered);
                setShowBankSuggestions(true);
              }
            }}
            onBlur={() => {
              // Delay to allow click on suggestion
              setTimeout(() => setShowBankSuggestions(false), 200);
            }}
            placeholder="e.g., Bank of Ceylon"
            error={!!errors.bank_name}
          />
          {errors.bank_name && (
            <p className="text-xs text-red-500 mt-1">{errors.bank_name}</p>
          )}

          {/* Bank suggestions dropdown */}
          {showBankSuggestions && filteredBanks.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
              {filteredBanks.map((bank, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleBankSelect(bank)}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                >
                  {bank}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div>
        <Label htmlFor="account_number">Account Number</Label>
        <Input
          id="account_number"
          type="text"
          value={formData.account_number}
          onChange={(e) => {
            setFormData({ ...formData, account_number: e.target.value });
            setErrors({ ...errors, account_number: '' });
          }}
          placeholder="e.g., 123456789"
          error={!!errors.account_number}
        />
        {errors.account_number && (
          <p className="text-xs text-red-500 mt-1">{errors.account_number}</p>
        )}
      </div>

      <div>
        <Label htmlFor="branch_name">Branch Name</Label>
        <Input
          id="branch_name"
          type="text"
          value={formData.branch_name}
          onChange={(e) => {
            setFormData({ ...formData, branch_name: e.target.value });
            setErrors({ ...errors, branch_name: '' });
          }}
          placeholder="e.g., Colombo Fort"
          error={!!errors.branch_name}
        />
        {errors.branch_name && (
          <p className="text-xs text-red-500 mt-1">{errors.branch_name}</p>
        )}
      </div>

      <div className="flex gap-2 justify-end pt-2">
        <Button
          type="button"
          onClick={onCancel}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800"
        >
          Cancel
        </Button>
        <Button
          type="submit"
          className="bg-violet-600 hover:bg-violet-700 text-white"
        >
          {isEdit ? 'Update' : 'Add'} Account
        </Button>
      </div>
    </form>
  );
};

export default BankAccountForm;
