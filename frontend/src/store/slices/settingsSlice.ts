// Settings Slice
import { createSlice } from '@reduxjs/toolkit';

const settingsSlice = createSlice({
  name: "settings",
  initialState: {
    visible: false,
  },
  reducers: {
    showSettings: (state) => {
      state.visible = true;
    },
    hideSettings: (state) => {
      state.visible = false;
    },
    toggleSettings: (state) => {
      state.visible = !state.visible;
    },
  },
});

export const { showSettings, hideSettings, toggleSettings } = settingsSlice.actions;
export default settingsSlice.reducer;
