/**
 * Manual Address Input Component
 *
 * Fallback component when Google Maps/Places API is unavailable.
 * Provides a traditional form-based address input with:
 * - Street address text field
 * - Village/Town text field
 * - District dropdown
 * - DS Division dropdown
 * - Optional manual coordinate entry
 */

import React, { useState, useEffect } from 'react';
import {
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Box,
  Typography,
  Alert,
  Collapse,
  Button,
  InputAdornment,
} from '@mui/material';
import {
  LocationOn as LocationIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

// Sri Lanka districts
const DISTRICTS = [
  'Ampara',
  'Anuradhapura',
  'Badulla',
  'Batticaloa',
  'Colombo',
  'Galle',
  'Gampaha',
  'Hambantota',
  'Jaffna',
  'Kalutara',
  'Kandy',
  'Kegalle',
  'Kilinochchi',
  'Kurunegala',
  'Mannar',
  'Matale',
  'Matara',
  'Monaragala',
  'Mullaitivu',
  'Nuwara Eliya',
  'Polonnaruwa',
  'Puttalam',
  'Ratnapura',
  'Trincomalee',
  'Vavuniya',
];

export interface ManualAddressData {
  streetAddress: string;
  villageTown: string;
  district: string;
  dsDivision: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
  formattedAddress: string;
}

interface ManualAddressInputProps {
  value?: Partial<ManualAddressData>;
  onChange: (data: ManualAddressData) => void;
  showCoordinates?: boolean;
  required?: boolean;
  disabled?: boolean;
  error?: string;
}

export const ManualAddressInput: React.FC<ManualAddressInputProps> = ({
  value,
  onChange,
  showCoordinates = true,
  required = false,
  disabled = false,
  error,
}) => {
  const [streetAddress, setStreetAddress] = useState(value?.streetAddress || '');
  const [villageTown, setVillageTown] = useState(value?.villageTown || '');
  const [district, setDistrict] = useState(value?.district || '');
  const [dsDivision, setDsDivision] = useState(value?.dsDivision || '');
  const [lat, setLat] = useState(value?.coordinates?.lat?.toString() || '');
  const [lng, setLng] = useState(value?.coordinates?.lng?.toString() || '');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Build formatted address when fields change
  useEffect(() => {
    const parts = [streetAddress, villageTown, dsDivision, district].filter(
      (p) => p.trim()
    );
    const formattedAddress = parts.join(', ');

    // Parse coordinates if provided
    let coordinates: { lat: number; lng: number } | undefined;
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    if (!isNaN(latNum) && !isNaN(lngNum)) {
      coordinates = { lat: latNum, lng: lngNum };
    }

    onChange({
      streetAddress,
      villageTown,
      district,
      dsDivision,
      coordinates,
      formattedAddress,
    });
  }, [streetAddress, villageTown, district, dsDivision, lat, lng, onChange]);

  // Validate coordinates
  const isLatValid = lat === '' || (!isNaN(parseFloat(lat)) && parseFloat(lat) >= -90 && parseFloat(lat) <= 90);
  const isLngValid = lng === '' || (!isNaN(parseFloat(lng)) && parseFloat(lng) >= -180 && parseFloat(lng) <= 180);

  return (
    <Box>
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2">
          Google Maps is currently unavailable. Please enter the address manually.
        </Typography>
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {/* Street Address */}
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Street Address / House Number"
            value={streetAddress}
            onChange={(e) => setStreetAddress(e.target.value)}
            required={required}
            disabled={disabled}
            placeholder="e.g., No. 123, Main Street"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LocationIcon color="action" />
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        {/* Village/Town */}
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Village / Town"
            value={villageTown}
            onChange={(e) => setVillageTown(e.target.value)}
            required={required}
            disabled={disabled}
            placeholder="e.g., Nugegoda"
          />
        </Grid>

        {/* DS Division */}
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="DS Division"
            value={dsDivision}
            onChange={(e) => setDsDivision(e.target.value)}
            disabled={disabled}
            placeholder="e.g., Maharagama"
            helperText="Divisional Secretariat Division"
          />
        </Grid>

        {/* District */}
        <Grid item xs={12} sm={6}>
          <FormControl fullWidth required={required} disabled={disabled}>
            <InputLabel>District</InputLabel>
            <Select
              value={district}
              label="District"
              onChange={(e) => setDistrict(e.target.value)}
            >
              <MenuItem value="">
                <em>Select District</em>
              </MenuItem>
              {DISTRICTS.map((d) => (
                <MenuItem key={d} value={d}>
                  {d}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Advanced: Coordinates */}
        {showCoordinates && (
          <Grid item xs={12}>
            <Button
              size="small"
              onClick={() => setShowAdvanced(!showAdvanced)}
              startIcon={showAdvanced ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              sx={{ mb: 1 }}
            >
              {showAdvanced ? 'Hide' : 'Show'} Manual Coordinates
            </Button>

            <Collapse in={showAdvanced}>
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Only enter coordinates if you know the exact GPS location.
                  Incorrect coordinates may affect the valuation report.
                </Typography>
              </Alert>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Latitude"
                    value={lat}
                    onChange={(e) => setLat(e.target.value)}
                    disabled={disabled}
                    error={!isLatValid}
                    helperText={
                      !isLatValid
                        ? 'Must be between -90 and 90'
                        : 'e.g., 6.9271'
                    }
                    placeholder="e.g., 6.9271"
                    type="number"
                    inputProps={{
                      step: 'any',
                      min: -90,
                      max: 90,
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Longitude"
                    value={lng}
                    onChange={(e) => setLng(e.target.value)}
                    disabled={disabled}
                    error={!isLngValid}
                    helperText={
                      !isLngValid
                        ? 'Must be between -180 and 180'
                        : 'e.g., 79.8612'
                    }
                    placeholder="e.g., 79.8612"
                    type="number"
                    inputProps={{
                      step: 'any',
                      min: -180,
                      max: 180,
                    }}
                  />
                </Grid>
              </Grid>
            </Collapse>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ManualAddressInput;
