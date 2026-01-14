import React, { useEffect, useState } from 'react';
import { UseFormReturn, useFieldArray } from 'react-hook-form';
import { Plus, Trash2, Receipt } from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import { Button } from './Button';
import { bankAccountApi } from '../services/api';
import { BankAccount } from '../types';
import AddBankAccountModal from './AddBankAccountModal';
import toast from 'react-hot-toast';

interface InvoiceDataStepProps {
  formMethods: UseFormReturn<any>;
  properties?: any[];
  isMultiProperty?: boolean;
}

const InvoiceDataStep: React.FC<InvoiceDataStepProps> = ({ formMethods, properties, isMultiProperty = false }) => {
  const { register, watch, setValue, control } = formMethods;

  // Use field array for dynamic invoice items
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'invoice_data.items' as any,
  });

  // State for bank accounts
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
  const [showAddAccountModal, setShowAddAccountModal] = useState(false);

  // Watch for changes
  const invoiceItems = watch('invoice_data.items') || [];
  const travelingCharges = watch('invoice_data.traveling_charges') || 0;
  const discount = watch('invoice_data.discount') || 0;

  // Fetch bank accounts on mount
  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const accounts = await bankAccountApi.getAll();
        setBankAccounts(accounts);
      } catch (error) {
        console.error('Failed to fetch bank accounts:', error);
      }
    };
    fetchAccounts();
  }, []);

  // Auto-populate invoice items for multi-property
  useEffect(() => {
    // Only run once when component mounts with multi-property and no items
    if (isMultiProperty && properties && properties.length > 0 && fields.length === 0) {
      console.log('[Invoice Auto-populate] Properties:', properties);

      properties.forEach((prop: any, index: number) => {
        // Access nested data fields correctly
        const lotDesc = prop.data?.lot_number || prop.data?.property_lot_description || '';
        const planNo = prop.data?.plan_number || '';

        console.log(`[Invoice Auto-populate] Property ${index + 1}:`, {
          lotDesc,
          planNo,
          fullData: prop.data
        });

        append({
          description: `Property No.${index + 1} - Lot ${lotDesc} in Plan No:${planNo}`,
          total: 0
        });
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isMultiProperty, properties]);

  // Migrate old invoice data format
  useEffect(() => {
    const existingInvoiceData = watch('invoice_data');

    if (existingInvoiceData?.items) {
      const hasOldFormat = existingInvoiceData.items.some(
        (item: any) => 'quantity' in item || 'unit_price' in item
      );

      if (hasOldFormat) {
        // Migrate to new format
        const migratedItems = existingInvoiceData.items.map((item: any) => ({
          description: item.description,
          total: item.total
        }));

        setValue('invoice_data.items', migratedItems);

        // Migrate bank_details to manual
        if (existingInvoiceData.bank_details) {
          setValue('invoice_data.manual_bank_details', existingInvoiceData.bank_details);
          setValue('invoice_data.bank_account_ids', []);
        }

        toast.info('Invoice data migrated to new format');
      }
    }

    // Load existing bank account selections
    if (existingInvoiceData?.bank_account_ids) {
      setSelectedAccountIds(existingInvoiceData.bank_account_ids);
    }
  }, []);

  // Calculate subtotal and grand total
  useEffect(() => {
    const subtotal = invoiceItems?.reduce((sum: number, item: any) => sum + (Number(item.total) || 0), 0) || 0;
    const traveling = Number(travelingCharges) || 0;
    const disc = Number(discount) || 0;
    const grandTotal = subtotal + traveling - disc;

    setValue('invoice_data.subtotal' as any, subtotal);
    setValue('invoice_data.total' as any, grandTotal);
  }, [invoiceItems, travelingCharges, discount, setValue]);

  // Update bank account IDs when selection changes
  useEffect(() => {
    setValue('invoice_data.bank_account_ids' as any, selectedAccountIds);
  }, [selectedAccountIds, setValue]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const subtotal = watch('invoice_data.subtotal') || 0;
  const grandTotal = watch('invoice_data.total') || 0;

  const toggleAccountSelection = (accountId: string) => {
    if (selectedAccountIds.includes(accountId)) {
      setSelectedAccountIds(selectedAccountIds.filter(id => id !== accountId));
    } else {
      setSelectedAccountIds([...selectedAccountIds, accountId]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Line Items */}
      <div className="bg-white rounded-2xl border-2 border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-pink-500 to-rose-600 text-white px-6 py-4">
          <div className="flex items-center">
            <Receipt className="h-5 w-5 mr-2" />
            <h4 className="font-bold">Invoice Line Items</h4>
          </div>
        </div>

        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-2 font-semibold text-gray-700">Description</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-700 w-48">Total (LKR)</th>
                  <th className="text-center py-3 px-2 w-16"></th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.id} className="border-b border-gray-100">
                    <td className="py-3 px-2">
                      <Input
                        {...register(`invoice_data.items.${index}.description` as any)}
                        placeholder="Service description"
                        className="w-full"
                      />
                    </td>
                    <td className="py-3 px-2">
                      <Input
                        type="number"
                        step="0.01"
                        {...register(`invoice_data.items.${index}.total` as any, { valueAsNumber: true })}
                        min={0}
                        placeholder="0.00"
                        className="w-full text-right"
                      />
                    </td>
                    <td className="py-3 px-2 text-center">
                      <button
                        type="button"
                        onClick={() => remove(index)}
                        className="text-red-500 hover:text-red-700 transition-colors"
                        disabled={fields.length === 1}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4">
            <Button
              type="button"
              onClick={() =>
                append({
                  description: '',
                  total: 0
                })
              }
              className="flex items-center px-4 py-2 bg-violet-100 hover:bg-violet-200 text-violet-700 rounded-xl font-medium transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Line Item
            </Button>
          </div>
        </div>
      </div>

      {/* Totals Section */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-2xl p-6 border-2 border-gray-200">
        <div className="space-y-4">
          {/* Subtotal */}
          <div className="flex justify-between items-center pb-3 border-b border-gray-300">
            <span className="text-gray-700 font-medium">Subtotal</span>
            <span className="text-xl font-bold text-gray-900">{formatCurrency(subtotal)}</span>
          </div>

          {/* Optional: Traveling Charges */}
          <div className="flex justify-between items-center">
            <div className="flex-1 mr-4">
              <Label htmlFor="invoice_data.traveling_charges">Traveling Charges (Optional)</Label>
              <Input
                type="number"
                step="0.01"
                {...register('invoice_data.traveling_charges' as any, { valueAsNumber: true })}
                placeholder="0.00"
                min={0}
              />
            </div>
            <div className="w-32 text-right pt-6 font-semibold text-gray-700">
              {formatCurrency(travelingCharges)}
            </div>
          </div>

          {/* Optional: Discount */}
          <div className="flex justify-between items-center pb-4 border-b-2 border-gray-300">
            <div className="flex-1 mr-4">
              <Label htmlFor="invoice_data.discount">Discount (Optional)</Label>
              <Input
                type="number"
                step="0.01"
                {...register('invoice_data.discount' as any, { valueAsNumber: true })}
                placeholder="0.00"
                min={0}
              />
            </div>
            <div className="w-32 text-right pt-6 font-semibold text-red-600">
              - {formatCurrency(discount)}
            </div>
          </div>

          {/* Grand Total */}
          <div className="flex justify-between items-center bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl p-4">
            <span className="text-lg font-bold">Grand Total</span>
            <span className="text-2xl font-black">{formatCurrency(grandTotal)}</span>
          </div>
        </div>
      </div>

      {/* Bank Account Selection */}
      <div className="bg-white rounded-2xl border-2 border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <Label className="text-lg font-semibold">Bank Account Details</Label>
          <Button
            type="button"
            onClick={() => setShowAddAccountModal(true)}
            className="px-3 py-1 bg-violet-600 hover:bg-violet-700 text-white text-sm rounded"
          >
            + Add New Account
          </Button>
        </div>

        {bankAccounts.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-gray-600 mb-3">
              Select one or more bank accounts to include in the invoice:
            </p>
            {bankAccounts.map((account) => (
              <label
                key={account.id}
                className={`flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedAccountIds.includes(account.id)
                    ? 'border-violet-500 bg-violet-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedAccountIds.includes(account.id)}
                  onChange={() => toggleAccountSelection(account.id)}
                  className="mt-1 mr-3"
                />
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">{account.bank_name}</p>
                  <p className="text-sm text-gray-600">Account: {account.account_number}</p>
                  <p className="text-sm text-gray-600">Branch: {account.branch_name}</p>
                </div>
              </label>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm mb-3">
            No bank accounts found. Add accounts in your profile or use manual entry below.
          </p>
        )}

        {/* Manual Bank Details Fallback */}
        {selectedAccountIds.length === 0 && (
          <div className="mt-4">
            <Label htmlFor="invoice_data.manual_bank_details">Or Enter Bank Details Manually</Label>
            <textarea
              {...register('invoice_data.manual_bank_details' as any)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              rows={4}
              placeholder="Bank Name&#10;Account Number: 123456789&#10;Branch: Colombo"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter bank account details manually if you haven't added them to your profile
            </p>
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 rounded-xl p-4">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Tip:</span> The invoice will be included in the final DOCX report.
          {isMultiProperty && ' Line items are automatically populated based on the number of properties, but you can customize them as needed.'}
        </p>
      </div>

      {/* Add Bank Account Modal */}
      {showAddAccountModal && (
        <AddBankAccountModal
          onClose={() => setShowAddAccountModal(false)}
          onAccountAdded={(newAccount) => {
            setBankAccounts([...bankAccounts, newAccount]);
            setSelectedAccountIds([...selectedAccountIds, newAccount.id]);
            setShowAddAccountModal(false);
          }}
        />
      )}
    </div>
  );
};

export default InvoiceDataStep;
