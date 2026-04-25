import Autocomplete, { type AutocompleteProps } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import type { SxProps, Theme } from '@mui/material';

const inputSx: SxProps<Theme> = {
  '& .MuiInputBase-root': {
    backgroundColor: 'rgb(15 23 42)',
    color: 'rgb(226 232 240)',
    fontSize: '0.875rem',
  },
  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgb(71 85 105)' },
  '& .MuiInputBase-root:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgb(100 116 139)',
  },
  '& .MuiInputBase-root.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgb(59 130 246 / 0.6)',
  },
  '& .MuiInputBase-input::placeholder': { color: 'rgb(100 116 139)', opacity: 1 },
  '& .MuiSvgIcon-root': { color: 'rgb(100 116 139)' },
};

const paperSx: SxProps<Theme> = {
  backgroundColor: 'rgb(15 23 42)',
  border: '1px solid rgb(51 65 85)',
  '& .MuiAutocomplete-option': {
    color: 'rgb(226 232 240)',
    '&[aria-selected="true"]': { backgroundColor: 'rgb(30 41 59) !important' },
    '&.Mui-focused': { backgroundColor: 'rgb(51 65 85) !important' },
  },
};

type Props<T> = Omit<AutocompleteProps<T, false, false, false>, 'renderInput'> & {
  placeholder?: string;
};

export default function DarkAutocomplete<T>({ placeholder, size = 'small', ...props }: Props<T>) {
  return (
    <Autocomplete
      size={size}
      {...props}
      renderInput={(params) => <TextField {...params} placeholder={placeholder} sx={inputSx} />}
      slotProps={{ paper: { sx: paperSx } }}
    />
  );
}
