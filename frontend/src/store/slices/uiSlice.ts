import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface UiState {
  siderCollapsed: boolean
  theme: 'light' | 'dark'
}

const initialState: UiState = {
  siderCollapsed: false,
  theme: 'light',
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSider(state) {
      state.siderCollapsed = !state.siderCollapsed
    },
    setSiderCollapsed(state, action: PayloadAction<boolean>) {
      state.siderCollapsed = action.payload
    },
    setTheme(state, action: PayloadAction<'light' | 'dark'>) {
      state.theme = action.payload
    },
  },
})

export const { toggleSider, setSiderCollapsed, setTheme } = uiSlice.actions
export default uiSlice.reducer
