import Select, { type SelectProps } from '@mui/material/Select';
import FormControl from '@mui/material/FormControl';
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
  '& .MuiSvgIcon-root': { color: 'rgb(100 116 139)' },
};

const paperSx: SxProps<Theme> = {
  backgroundColor: 'rgb(15 23 42)',
  border: '1px solid rgb(51 65 85)',
  '& .MuiMenuItem-root': {
    color: 'rgb(226 232 240)',
    fontSize: '0.875rem',
    '&:hover': { backgroundColor: 'rgb(51 65 85)' },
    '&.Mui-selected': {
      backgroundColor: 'rgb(30 41 59)',
      '&:hover': { backgroundColor: 'rgb(51 65 85)' },
    },
  },
};

export default function DarkSelect({ children, MenuProps, ...props }: SelectProps) {
  return (
    <FormControl size="small" sx={inputSx}>
      <Select
        {...props}
        MenuProps={{
          ...MenuProps,
          slotProps: { paper: { sx: paperSx }, ...MenuProps?.slotProps },
        }}
      >
        {children}
      </Select>
    </FormControl>
  );
}
