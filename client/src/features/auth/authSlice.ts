import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export interface AuthUser {
    name: string;
    email: string;
}
export interface AuthState {
    user: AuthUser | null;
    token: string | null;
}

const STORAGE_KEY = 'auth';

function loadInitialState(): AuthState {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return { user: null, token: null };
        const parsed = JSON.parse(raw);
        return { user: parsed.user ?? null, token: parsed.token ?? null };
    } catch {
        return { user: null, token: null };
    }
}

const authSlice = createSlice({
    name: 'auth',
    initialState: loadInitialState(),
    reducers: {
        setCredentials: (state, action: PayloadAction<{ user: AuthUser; token: string; }>) => {
            state.user = action.payload.user;
            state.token = action.payload.token;
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        },
        logout: (state) => {
            state.user = null;
            state.token = null;
            localStorage.removeItem(STORAGE_KEY);
        },
    },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
