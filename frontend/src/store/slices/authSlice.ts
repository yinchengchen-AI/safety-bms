import { createSlice, PayloadAction, createSelector } from '@reduxjs/toolkit'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  access_token: string | null
  refresh_token: string | null
  isAuthenticated: boolean
}

const initialState: AuthState = {
  user: null,
  access_token: null,
  refresh_token: null,
  isAuthenticated: false,
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
    },
    logout(state) {
      state.user = null
      state.access_token = null
      state.refresh_token = null
      state.isAuthenticated = false
    },
  },
})

export const { setCredentials, setUser, logout } = authSlice.actions
export default authSlice.reducer

// Selectors
export const selectCurrentUser = (state: { auth: AuthState }) => state.auth.user
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectUserRoles = createSelector(
  [selectCurrentUser],
  (user) => user?.roles.map((r) => r.name) ?? []
)
