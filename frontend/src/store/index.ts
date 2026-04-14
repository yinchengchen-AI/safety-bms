import { configureStore } from '@reduxjs/toolkit'
import { baseApi } from './api/baseApi'
import authReducer from './slices/authSlice'
import uiReducer from './slices/uiSlice'

// 注册所有 API endpoints
import './api/usersApi'
import './api/customersApi'
import './api/contractsApi'
import './api/servicesApi'
import './api/invoicesApi'
import './api/paymentsApi'
import './api/dashboardApi'
import './api/analyticsApi'
import './api/rolesApi'
import './api/permissionsApi'
import './api/departmentsApi'
import './api/notificationsApi'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiReducer,
    [baseApi.reducerPath]: baseApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(baseApi.middleware),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
