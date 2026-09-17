import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

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
    baseQuery: fetchBaseQuery({ baseUrl: `${import.meta.env.VITE_API_URL}/auth` }),
    endpoints: (builder) => ({
        register: builder.mutation<RegisterResponse, User>({
            query: (user) => ({ url: "/register", method: "POST", body: user }),
        }),
        login: builder.mutation<LoginResponse, LoginRequest>({
            query: (credentials) => ({ url: "/login", method: "POST", body: credentials }),
        }),
    }),
});

export const { useRegisterMutation, useLoginMutation } = authApi;
