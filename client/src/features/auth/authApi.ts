import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import type { RootState } from "../../app/store";

export interface User  {
    name: string;
    email: string;
}

export interface RegisterRequest  {
    name: string;
    email: string;
    password: string;
}

export interface RegisterResponse {
    message: string;
    data: User;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface LoginResponse {
    message: string;
    token: string;
    data: User;
}

export const authApi = createApi({
    reducerPath: "authApi",
    baseQuery: fetchBaseQuery({ 
        baseUrl: `${import.meta.env.VITE_API_URL}/auth`,
        prepareHeaders: (headers, { getState }) => {
            const token = (getState() as RootState).auth.token;
            if (token) headers.set("Authorization", `Bearer ${token}`);
            return headers;
        },
    }),
    endpoints: (builder) => ({
        register: builder.mutation<RegisterResponse, RegisterRequest>({
            query: (body) => ({ url: "/register", method: "POST", body: body }),
        }),
        login: builder.mutation<LoginResponse, LoginRequest>({
            query: (credentials) => ({ url: "/login", method: "POST", body: credentials }),
        }),
        getMe: builder.query<User, void>({
            query: () => "/me",
        }),
        deregister: builder.mutation<void, void>({
            query: () => ({ url: "/deregister", method: "DELETE" }),
        }),
    }),
});

export const {
    useRegisterMutation,
    useLoginMutation,
    useGetMeQuery,
    useDeregisterMutation,
} = authApi;
