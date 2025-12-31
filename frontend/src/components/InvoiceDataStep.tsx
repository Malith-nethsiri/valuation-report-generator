import React, { useEffect } from 'react';
import { UseFormReturn, useFieldArray } from 'react-hook-form';
import { Plus, Trash2, Receipt } from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import { Button } from './Button';
import { MultiPropertyFormData } from './MultiPropertyStepForm';

interface InvoiceDataStepProps {
  formMethods: UseFormReturn<MultiPropertyFormData>;
}

const InvoiceDataStep: React.FC<InvoiceDataStepProps> = ({ formMethods }) => {
  const { register, watch, setValue, control } = formMethods;

  // Use field array for dynamic invoice items
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'invoice_data.items' as any,
  });

  // Watch for changes
  const invoiceItems = watch('invoice_data.items') || [];
  const travelingCharges = watch('invoice_data.traveling_charges') || 0;
  const discount = watch('invoice_data.discount') || 0;
  const properties = watch('properties') || [];

  // Auto-populate invoice items on mount if empty
  useEffect(() => {
    if (invoiceItems.length === 0 && properties.length > 0) {
      // Auto-populate with one line item per property
      properties.forEach((prop: any, index: number) => {
        append({
          description: `Valuation of Property ${index + 1}${prop.property_lot_description ? ` - ${prop.property_lot_description}` : ''}`,
          quantity: 1,
          unit_price: 0,
          total: 0,
        });
      });
    }
  }, []);

  // Auto-calculate line item totals
  useEffect(() => {
    invoiceItems?.forEach((item: any, index: number) => {
      const quantity = item.quantity || 0;
      const unitPrice = item.unit_price || 0;
      const total = quantity * unitPrice;

      if (item.total !== total) {
        setValue(`invoice_data.items.${index}.total` as any, total);
      }
    });
  }, [invoiceItems]);

  // Calculate subtotal and grand total
  useEffect(() => {
    const subtotal = invoiceItems?.reduce((sum: number, item: any) => sum + (item.total || 0), 0) || 0;
    const traveling = Number(travelingCharges) || 0;
    const disc = Number(discount) || 0;
    const grandTotal = subtotal + traveling - disc;

    setValue('invoice_data.subtotal' as any, subtotal);
    setValue('invoice_data.total' as any, grandTotal);
  }, [invoiceItems, travelingCharges, discount]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const subtotal = watch('invoice_data.subtotal') || 0;
  const grandTotal = watch('invoice_data.total') || 0;

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
                  <th className="text-center py-3 px-2 font-semibold text-gray-700 w-24">Qty</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-700 w-32">Unit Price (LKR)</th>
                  <th className="text-right py-3 px-2 font-semibold text-gray-700 w-32">Total (LKR)</th>
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
                        {...register(`invoice_data.items.${index}.quantity` as any, { valueAsNumber: true })}
                        min={1}
                        defaultValue={1}
                        className="w-full text-center"
                      />
                    </td>
                    <td className="py-3 px-2">
                      <Input
                        type="number"
                        step="0.01"
                        {...register(`invoice_data.items.${index}.unit_price` as any, { valueAsNumber: true })}
                        min={0}
                        placeholder="0.00"
                        className="w-full text-right"
                      />
                    </td>
                    <td className="py-3 px-2">
                      <div className="text-right font-semibold text-gray-900">
                        {formatCurrency(invoiceItems[index]?.total || 0)}
                      </div>
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
                  quantity: 1,
                  unit_price: 0,
                  total: 0,
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

      {/* Payment Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Label htmlFor="invoice_data.payment_terms">Payment Terms</Label>
          <textarea
            {...register('invoice_data.payment_terms' as any)}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            rows={4}
            placeholder="e.g., Payment due within 30 days of report date"
          />
          <p className="text-xs text-gray-500 mt-1">
            Specify when payment is expected
          </p>
        </div>

        <div>
          <Label htmlFor="invoice_data.bank_details">Bank Details</Label>
          <textarea
            {...register('invoice_data.bank_details' as any)}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            rows={4}
            placeholder="Bank Name&#10;Account Number: 123456789&#10;Branch: Colombo"
          />
          <p className="text-xs text-gray-500 mt-1">
            Bank account details for payment
          </p>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 rounded-xl p-4">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Tip:</span> The invoice will be included in the final DOCX report.
          Line items are automatically populated based on the number of properties, but you can customize them as needed.
        </p>
      </div>
    </div>
  );
};

export default InvoiceDataStep;
