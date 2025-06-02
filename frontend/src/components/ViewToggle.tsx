import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { ToggleButton, ToggleButtonGroup, Box, Typography } from '@mui/material';
import { GridView, CalendarMonth } from '@mui/icons-material';
import { RootState } from '../store';
import { setView, DashboardView } from '../store/slices/dashboardSlice';

const ViewToggle: React.FC = () => {
  const { view } = useSelector((state: RootState) => state.dashboard);
  const dispatch = useDispatch();

  const handleViewChange = (
    event: React.MouseEvent<HTMLElement>,
    newView: DashboardView | null,
  ) => {
    if (newView !== null) {
      dispatch(setView(newView));
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <Typography variant="body2" color="text.secondary" fontWeight={500}>
        View:
      </Typography>
      <ToggleButtonGroup
        value={view}
        exclusive
        onChange={handleViewChange}
        aria-label="dashboard view"
        size="small"
        sx={{
          '& .MuiToggleButton-root': {
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
            px: 2,
            py: 1,
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
            },
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          },
        }}
      >
        <ToggleButton value="grid" aria-label="grid view">
          <GridView sx={{ mr: 1, fontSize: 18 }} />
          Grid
        </ToggleButton>
        <ToggleButton value="calendar" aria-label="calendar view">
          <CalendarMonth sx={{ mr: 1, fontSize: 18 }} />
          Calendar
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
};

export default ViewToggle; 