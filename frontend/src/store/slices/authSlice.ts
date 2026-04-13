import { createSlice, PayloadAction, createSelector } from '@reduxjs/toolkit'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  access_token: string | null
  refresh_token: string | null
  isAuthenticated: boolean
  isInitialized: boolean
  permissions: string[]
}

const initialState: AuthState = {
  user: null,
  access_token: null,
  refresh_token: null,
  isAuthenticated: false,
  isInitialized: false,
  permissions: [],
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials(state, action: PayloadAction<{ access_token: string; refresh_token: string }>) {
      state.access_token = action.payload.access_token
      state.refresh_token = action.payload.refresh_token
      state.isAuthenticated = true
    },
    setUser(state, action: PayloadAction<User>) {
      state.user = action.payload
      state.isAuthenticated = true
      state.isInitialized = true
    },
    setPermissions(state, action: PayloadAction<string[]>) {
      state.permissions = action.payload
    },
    setInitialized(state) {
      state.isInitialized = true
    },
    logout(state) {
      state.user = null
      state.access_token = null
      state.refresh_token = null
      state.isAuthenticated = false
      state.isInitialized = true
      state.permissions = []
    },
  },
})

export const { setCredentials, setUser, setPermissions, setInitialized, logout } = authSlice.actions
export default authSlice.reducer

// Selectors
export const selectCurrentUser = (state: { auth: AuthState }) => state.auth.user
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectIsInitialized = (state: { auth: AuthState }) => state.auth.isInitialized
export const selectUserPermissions = (state: { auth: AuthState }) => state.auth.permissions
export const selectUserRoles = createSelector(
  [selectCurrentUser],
  (user) => user?.roles.map((r) => r.name) ?? []
)
