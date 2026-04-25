import { Slider, SliderProps, type SxProps, type Theme } from '@mui/material';

const sliderSx: SxProps<Theme> = {
  color: 'rgb(59 130 246)',
  height: 4,
  padding: '13px 0',
  '& .MuiSlider-track': { border: 'none' },
  '& .MuiSlider-thumb': {
    backgroundColor: 'rgb(59 130 246)',
    width: 18,
    height: 18,
    '&:hover, &.Mui-focusVisible': {
      boxShadow: '0 0 0 8px rgb(59 130 246 / 0.16)',
    },
  },
  '& .MuiSlider-rail': {
    backgroundColor: 'rgb(51 65 85)',
    opacity: 1,
  },
};

export default function DarkSlider({ sx, ...props }: SliderProps) {
  return <Slider {...props} sx={{ ...sliderSx, ...sx }} />;
}
