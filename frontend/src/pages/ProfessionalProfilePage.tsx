import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import {
    User, Mail, Phone, MapPin, GraduationCap, Award, Building,
    Save, Eye, AlertCircle, CheckCircle, Sparkles, CreditCard, Edit, Trash2, Plus
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { AutocompleteInput } from '../components/AutocompleteInput';
import { LetterheadPreview } from '../components/LetterheadPreview';
import { LetterheadGallery } from '../components/LetterheadGallery';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Label } from '../components/Label';
import { Textarea } from '../components/Textarea';
import { api, bankAccountApi } from '../services/api';
import { BankAccount } from '../types';
import AddBankAccountModal from '../components/AddBankAccountModal';
import BankAccountForm from '../components/BankAccountForm';
import { DeleteConfirmDialog } from '../components/DeleteConfirmDialog';
import toast from 'react-hot-toast';

// Validation schema for professional profile
const professionalProfileSchema = z.object({
    // Personal Information
    full_name: z.string().min(2, 'Full name is required'),
    honorific: z.string().optional(),

    // Academic Information
    academic_qualifications: z.string().min(1, 'Academic qualifications are required'),

    // Professional Credentials
    membership_level: z.string().min(1, 'Membership level is required'),
    membership_number: z.string().min(1, 'Membership number is required'),
    professional_designation: z.string().min(1, 'Professional designation is required'),
    panel_valuer_banks: z.array(z.string()).optional(),

    // Residential Address (Required for letterhead)
    house_number: z.string().min(1, 'House number is required'),
    area_development: z.string().min(1, 'Area/Development is required'),
    village: z.string().optional(),
    locality: z.string().min(1, 'Locality is required'),

    // Contact Information
    phone_primary: z.string().min(1, 'Primary phone is required'),
    phone_secondary: z.string().optional(),

    // Office Information (Optional)
    office_department: z.string().optional(),
    office_region: z.string().optional(),
    office_street_city: z.string().optional(),
    office_phone: z.string().optional(),
});

type ProfessionalProfileData = z.infer<typeof professionalProfileSchema>;

interface AutocompleteData {
    honorifics: string[];
    membership_levels: string[];
    academic_qualifications: string[];
    professional_designations: string[];
    sri_lankan_banks: string[];
    professional_institutes: string[];
    office_departments: string[];
    provinces: string[];
    cities: string[];
    universities: string[];
    residential_areas: string[];
}

const ProfessionalProfilePage: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPreview, setShowPreview] = useState(true);
    const [autocompleteData, setAutocompleteData] = useState<AutocompleteData | null>(null);
    const [panelBanks, setPanelBanks] = useState<string[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('classic');

    // Bank Account Management State
    const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
    const [editingAccountId, setEditingAccountId] = useState<string | null>(null);
    const [showAddAccountModal, setShowAddAccountModal] = useState(false);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [accountToDelete, setAccountToDelete] = useState<BankAccount | null>(null);

    const { user, updateUserProfile } = useAuth();
    const navigate = useNavigate();

    const {
        register,
        handleSubmit,
        formState: { errors, isValid },
        watch,
        setValue,
        getValues
    } = useForm<ProfessionalProfileData>({
        resolver: zodResolver(professionalProfileSchema),
        mode: 'onChange',
        defaultValues: {
            full_name: user?.full_name || '',
            honorific: user?.honorific || '',
            academic_qualifications: user?.academic_qualifications || '',
            membership_level: user?.membership_level || '',
            membership_number: user?.membership_number || '',
            professional_designation: user?.professional_designation || '',
            house_number: user?.house_number || '',
            area_development: user?.area_development || '',
            village: user?.village || '',
            locality: user?.locality || '',
            phone_primary: user?.phone_primary || '',
            phone_secondary: user?.phone_secondary || '',
            office_department: user?.office_department || '',
            office_region: user?.office_region || '',
            office_street_city: user?.office_street_city || '',
            office_phone: user?.office_phone || '',
        }
    });

    // Watch all values for real-time preview
    const watchedValues = watch();

    // Load autocomplete data
    useEffect(() => {
        const loadAutocompleteData = async () => {
            try {
                const response = await api.get('/api/autocomplete');
                setAutocompleteData(response.data);
            } catch (err) {
                console.error('Failed to load autocomplete data:', err);
            }
        };

        const loadBankAccounts = async () => {
            try {
                const accounts = await bankAccountApi.getAll();
                setBankAccounts(accounts);
            } catch (err) {
                console.error('Failed to load bank accounts:', err);
            }
        };

        loadAutocompleteData();
        loadBankAccounts();

        // Load existing panel banks
        if (user?.panel_valuer_banks) {
            setPanelBanks(user.panel_valuer_banks);
        }

        // Load user's preferred letterhead template
        if (user?.preferred_letterhead_template) {
            setSelectedTemplate(user.preferred_letterhead_template);
        }
    }, [user]);

    // Clear error after 5 seconds
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(''), 5000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const onSubmit = async (data: ProfessionalProfileData) => {
        setIsLoading(true);
        setError('');

        try {
            const updateData = {
                ...data,
                panel_valuer_banks: panelBanks,
                preferred_letterhead_template: selectedTemplate
            };

            await updateUserProfile(updateData);
            navigate('/dashboard', {
                state: { message: 'Professional profile completed successfully!' }
            });
        } catch (err: any) {
            setError(err.message || 'Failed to update profile. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    // Bank Account CRUD Handlers
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

    // Combine user data with current form data for preview
    const getPreviewData = () => ({
        full_name: watchedValues.full_name || '',
        honorific: watchedValues.honorific || '',
        email: user?.email || '',
        ...watchedValues,
        panel_valuer_banks: panelBanks
    });

    if (!autocompleteData) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-emerald-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-blue-50">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 mb-4 shadow-lg shadow-emerald-500/25">
                        <User className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-emerald-900 to-green-900 bg-clip-text text-transparent">
                        Complete Your Professional Profile
                    </h1>
                    <p className="text-gray-600 mt-2">
                        This information will be used to generate professional letterheads for your reports
                    </p>
                </div>

                <div className="grid lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
                    {/* Form Section */}
                    <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8">
                        {/* Error message */}
                        {error && (
                            <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-100">
                                <div className="flex items-center">
                                    <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                                    <p className="text-red-600 text-sm font-medium">{error}</p>
                                </div>
                            </div>
                        )}

                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                            {/* Personal Information */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <User className="mr-2 text-emerald-600" />
                                    Personal Information
                                </h2>

                                <div className="space-y-2 mb-4">
                                    <Label htmlFor="full_name" className="text-gray-700 font-medium">
                                        Full Name *
                                    </Label>
                                    <Input
                                        id="full_name"
                                        placeholder="Enter your full name"
                                        {...register('full_name')}
                                        className={errors.full_name ? 'border-red-300' : ''}
                                    />
                                    {errors.full_name && (
                                        <p className="text-red-500 text-sm">{errors.full_name.message}</p>
                                    )}
                                </div>

                                <AutocompleteInput
                                    label="Title/Honorific (Optional)"
                                    value={watchedValues.honorific || ''}
                                    onChange={(value) => setValue('honorific', value)}
                                    suggestions={autocompleteData.honorifics}
                                    placeholder="e.g., Mr., Dr., Prof."
                                    required={false}
                                />
                            </section>

                            {/* Academic Information */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <GraduationCap className="mr-2 text-emerald-600" />
                                    Academic Qualifications
                                </h2>

                                <AutocompleteInput
                                    label="Academic Qualifications"
                                    value={watchedValues.academic_qualifications || ''}
                                    onChange={(value) => setValue('academic_qualifications', value)}
                                    suggestions={autocompleteData.academic_qualifications}
                                    placeholder="e.g., B.Sc Estate Management and Valuation"
                                    required
                                    error={errors.academic_qualifications?.message}
                                />
                            </section>

                            {/* Professional Credentials */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <Award className="mr-2 text-emerald-600" />
                                    Professional Credentials
                                </h2>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <AutocompleteInput
                                        label="Membership Level"
                                        value={watchedValues.membership_level || ''}
                                        onChange={(value) => setValue('membership_level', value)}
                                        suggestions={autocompleteData.membership_levels}
                                        placeholder="e.g., Fellow Member"
                                        required
                                        error={errors.membership_level?.message}
                                    />

                                    <div className="space-y-2">
                                        <Label htmlFor="membership_number" className="text-gray-700 font-medium">
                                            Membership Number *
                                        </Label>
                                        <Input
                                            id="membership_number"
                                            placeholder="e.g., F-260"
                                            {...register('membership_number')}
                                            className={errors.membership_number ? 'border-red-300' : ''}
                                        />
                                        {errors.membership_number && (
                                            <p className="text-red-500 text-sm">{errors.membership_number.message}</p>
                                        )}
                                    </div>
                                </div>

                                <AutocompleteInput
                                    label="Professional Designation"
                                    value={watchedValues.professional_designation || ''}
                                    onChange={(value) => setValue('professional_designation', value)}
                                    suggestions={autocompleteData.professional_designations}
                                    placeholder="e.g., Chartered Valuer"
                                    required
                                    error={errors.professional_designation?.message}
                                />

                                <AutocompleteInput
                                    label="Panel Valuer Banks (Optional)"
                                    value=""
                                    onChange={() => { }} // Handled by multiSelect
                                    suggestions={autocompleteData.sri_lankan_banks}
                                    placeholder="Select banks where you are a panel valuer"
                                    multiSelect
                                    selectedItems={panelBanks}
                                    onSelectionChange={setPanelBanks}
                                />
                            </section>

                            {/* Residential Address */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <MapPin className="mr-2 text-emerald-600" />
                                    Residential Address
                                </h2>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="house_number" className="text-gray-700 font-medium">
                                            House Number *
                                        </Label>
                                        <Input
                                            id="house_number"
                                            placeholder="e.g., No: 43"
                                            {...register('house_number')}
                                            className={errors.house_number ? 'border-red-300' : ''}
                                        />
                                        {errors.house_number && (
                                            <p className="text-red-500 text-sm">{errors.house_number.message}</p>
                                        )}
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="area_development" className="text-gray-700 font-medium">
                                            Area/Development *
                                        </Label>
                                        <Input
                                            id="area_development"
                                            placeholder="e.g., Highway City"
                                            {...register('area_development')}
                                            className={errors.area_development ? 'border-red-300' : ''}
                                        />
                                        {errors.area_development && (
                                            <p className="text-red-500 text-sm">{errors.area_development.message}</p>
                                        )}
                                    </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="village" className="text-gray-700 font-medium">
                                            Village (Optional)
                                        </Label>
                                        <Input
                                            id="village"
                                            placeholder="Village name"
                                            {...register('village')}
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="locality" className="text-gray-700 font-medium">
                                            Locality *
                                        </Label>
                                        <Input
                                            id="locality"
                                            placeholder="e.g., Thorawatta"
                                            {...register('locality')}
                                            className={errors.locality ? 'border-red-300' : ''}
                                        />
                                        {errors.locality && (
                                            <p className="text-red-500 text-sm">{errors.locality.message}</p>
                                        )}
                                    </div>
                                </div>
                            </section>

                            {/* Contact Information */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <Phone className="mr-2 text-emerald-600" />
                                    Contact Information
                                </h2>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="phone_primary" className="text-gray-700 font-medium">
                                            Primary Phone *
                                        </Label>
                                        <Input
                                            id="phone_primary"
                                            type="tel"
                                            placeholder="e.g., 077-8843656"
                                            {...register('phone_primary')}
                                            className={errors.phone_primary ? 'border-red-300' : ''}
                                        />
                                        {errors.phone_primary && (
                                            <p className="text-red-500 text-sm">{errors.phone_primary.message}</p>
                                        )}
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="phone_secondary" className="text-gray-700 font-medium">
                                            Secondary Phone (Optional)
                                        </Label>
                                        <Input
                                            id="phone_secondary"
                                            type="tel"
                                            placeholder="Additional phone number"
                                            {...register('phone_secondary')}
                                        />
                                    </div>
                                </div>
                            </section>

                            {/* Office Information */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <Building className="mr-2 text-emerald-600" />
                                    Office Information (Optional)
                                </h2>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <AutocompleteInput
                                        label="Department (Optional)"
                                        value={watchedValues.office_department || ''}
                                        onChange={(value) => setValue('office_department', value)}
                                        suggestions={autocompleteData.office_departments}
                                        placeholder="e.g., Valuation Department"
                                    />

                                    <AutocompleteInput
                                        label="Region/Province (Optional)"
                                        value={watchedValues.office_region || ''}
                                        onChange={(value) => setValue('office_region', value)}
                                        suggestions={autocompleteData.provinces}
                                        placeholder="e.g., Northwestern Province"
                                    />
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <AutocompleteInput
                                        label="Office Address (Optional)"
                                        value={watchedValues.office_street_city || ''}
                                        onChange={(value) => setValue('office_street_city', value)}
                                        suggestions={autocompleteData.cities}
                                        placeholder="Street and city"
                                    />

                                    <div className="space-y-2">
                                        <Label htmlFor="office_phone" className="text-gray-700 font-medium">
                                            Office Phone (Optional)
                                        </Label>
                                        <Input
                                            id="office_phone"
                                            type="tel"
                                            placeholder="Office phone number"
                                            {...register('office_phone')}
                                        />
                                    </div>
                                </div>
                            </section>

                            {/* Bank Account Management */}
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
                                    Add bank accounts to your profile for quick selection when generating invoices. These accounts are optional and can be updated anytime.
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

                            {/* Letterhead Template Selection */}
                            <section>
                                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                                    <Sparkles className="mr-2 text-emerald-600" />
                                    Choose Your Letterhead Template
                                </h2>
                                <p className="text-gray-600 mb-4 text-sm">
                                    Select the letterhead design for your reports. You can change this anytime.
                                </p>

                                <LetterheadGallery
                                    selectedTemplate={selectedTemplate}
                                    onTemplateSelect={setSelectedTemplate}
                                    userData={getPreviewData()}
                                />
                            </section>

                            {/* Submit Button */}
                            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                                <Button
                                    type="button"
                                    onClick={() => setShowPreview(!showPreview)}
                                    className="flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg"
                                >
                                    <Eye className="mr-2 h-4 w-4" />
                                    {showPreview ? 'Hide' : 'Show'} Preview
                                </Button>

                                <Button
                                    type="submit"
                                    disabled={!isValid || isLoading}
                                    className="flex items-center px-8 py-3 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-semibold rounded-2xl shadow-lg disabled:opacity-50"
                                >
                                    {isLoading ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="mr-2 h-4 w-4" />
                                            Complete Profile
                                            <Sparkles className="ml-2 h-4 w-4" />
                                        </>
                                    )}
                                </Button>
                            </div>
                        </form>
                    </div>

                    {/* Preview Section */}
                    {showPreview && (
                        <div className="lg:sticky lg:top-8 lg:h-fit">
                            <LetterheadPreview
                                userData={getPreviewData()}
                                templateId={selectedTemplate}
                            />
                        </div>
                    )}
                </div>
            </div>

            {/* Add Bank Account Modal */}
            {showAddAccountModal && (
                <AddBankAccountModal
                    onClose={() => setShowAddAccountModal(false)}
                    onAccountAdded={(newAccount) => {
                        setBankAccounts([...bankAccounts, newAccount]);
                        setShowAddAccountModal(false);
                    }}
                />
            )}

            {/* Delete Bank Account Confirmation Dialog */}
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
        </div>
    );
};

export default ProfessionalProfilePage;
