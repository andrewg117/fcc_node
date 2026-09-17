import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const serverApi = createApi({
  reducerPath: "serverApi",
  baseQuery: fetchBaseQuery({ baseUrl: `${import.meta.env.VITE_API_URL}/server` }),
  endpoints: (builder) => ({
    getHome: builder.query<string, void>({
      query: () => ({ url: "/", responseHandler: "text" }),
    }),
  }),
});

export const { useGetHomeQuery } = serverApi;