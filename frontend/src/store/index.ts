import { configureStore } from "@reduxjs/toolkit";
import authSlice from "./slices/authSlice";
import settingsSlice from "./slices/settingsSlice";

// 创建 Store
export const store = configureStore({
  reducer: {
    auth: authSlice,
    settings: settingsSlice,
  },
});

// 导出类型
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;