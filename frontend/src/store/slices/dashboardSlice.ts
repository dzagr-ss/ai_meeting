import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type DashboardView = 'grid' | 'calendar';

interface DashboardState {
  view: DashboardView;
}

const initialState: DashboardState = {
  view: 'grid',
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setView: (state, action: PayloadAction<DashboardView>) => {
      state.view = action.payload;
    },
    toggleView: (state) => {
      state.view = state.view === 'grid' ? 'calendar' : 'grid';
    },
  },
});

export const { setView, toggleView } = dashboardSlice.actions;
export default dashboardSlice.reducer; 