import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export interface User {
  name: string;
  email: string;
}

export interface CreateUserResponse {
  message: string;
  data: User;
}

export const serverApi = createApi({
  reducerPath: "serverApi",
  baseQuery: fetchBaseQuery({ baseUrl: `${import.meta.env.VITE_API_URL}/server` }),
  endpoints: (builder) => ({
    getHome: builder.query<string, void>({
      query: () => ({ url: "/", responseHandler: "text" }),
    }),
    getUser: builder.query<string, number>({
      query: (id) => ({ url: `/user/${id}`, responseHandler: "text" }),
    }),
    createUser: builder.mutation<CreateUserResponse, User>({
      query: (user) => ({ url: "/user", method: "POST", body: user }),
    }),
  }),
});

export const { useGetHomeQuery, useGetUserQuery, useCreateUserMutation } = serverApi;