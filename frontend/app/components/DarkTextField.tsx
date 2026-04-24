import TextField, { type TextFieldProps } from '@mui/material/TextField';
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
  '& .MuiInputBase-input': { colorScheme: 'dark' },
  '& .MuiInputAdornment-root': { color: 'rgb(100 116 139)' },
};

export default function DarkTextField({ sx, size = 'small', ...props }: TextFieldProps) {
  return <TextField size={size} sx={{ ...inputSx, ...sx }} {...props} />;
}
