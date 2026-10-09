import { createApi, fetchBaseQuery, type FetchBaseQueryError } from "@reduxjs/toolkit/query/react";
import type { RootState } from "../../app/store";

export interface MediaItem {
    id: string;
    title: string;
    description: string;
    image_url: string;
    song_url: string;
    created_at: string;
}

export interface CreateMediaArgs {
    title: string;
    description: string;
    image: File;
    song: File;
}

export interface UpdateMediaArgs {
    id: string;
    // Leave a field out to keep its current value.
    title?: string;
    description?: string;
    image?: File;
    song?: File;
}

interface UploadTarget {
    path: string;
    upload_url: string;
}

interface UploadedPaths {
    image_path?: string;
    song_path?: string;
}

type Step<T> = { data: T } | { error: FetchBaseQueryError };

const baseQuery = fetchBaseQuery({
    baseUrl: `${import.meta.env.VITE_API_URL}/media`,
    prepareHeaders: (headers, { getState }) => {
        const token = (getState() as RootState).auth.token;
        if (token) headers.set("Authorization", `Bearer ${token}`);
        return headers;
    },
});

// The type of the `baseQuery` that RTK Query passes to a queryFn.
type BaseQuery = (args: Parameters<typeof baseQuery>[0]) => ReturnType<typeof baseQuery>;

// Upload step 1 for one file: the backend checks its type and size and says where to upload it.
async function startUpload(request: BaseQuery, kind: "image" | "audio", file: File): Promise<Step<UploadTarget>> {
    const result = await request({
        url: "/uploads",
        method: "POST",
        body: { kind, content_type: file.type, size: file.size },
    });
    if (result.error) return { error: result.error };
    return { data: result.data as UploadTarget };
}

// Upload step 2 for one file: send it straight to Supabase. Plain fetch, not
// baseQuery, so our Authorization header is never sent to Supabase.
async function sendFile(target: UploadTarget, file: File): Promise<FetchBaseQueryError | null> {
    let response: Response;
    try {
        response = await fetch(target.upload_url, {
            method: "PUT",
            headers: { "Content-Type": file.type },
            body: file,
        });
    } catch {
        return { status: "FETCH_ERROR", error: "Could not reach file storage" };
    }
    if (response.ok) return null;
    // Supabase errors have a `message`, which getErrorMessage shows.
    const data: unknown = await response.json().catch(() => undefined);
    return { status: response.status, data };
}

// Upload steps 1 and 2 for whichever files were picked. Returns the paths to send in upload step 3.
async function uploadFiles(request: BaseQuery, image?: File, song?: File): Promise<Step<UploadedPaths>> {
    // Upload step 1 runs for both files before upload step 2 sends either, so a rejected
    // song doesn't leave an uploaded image behind in the bucket.
    const imageTarget = image ? await startUpload(request, "image", image) : undefined;
    if (imageTarget && "error" in imageTarget) return imageTarget;
    const songTarget = song ? await startUpload(request, "audio", song) : undefined;
    if (songTarget && "error" in songTarget) return songTarget;

    if (image && imageTarget) {
        const error = await sendFile(imageTarget.data, image);
        if (error) return { error };
    }
    if (song && songTarget) {
        const error = await sendFile(songTarget.data, song);
        if (error) return { error };
    }
    return { data: { image_path: imageTarget?.data.path, song_path: songTarget?.data.path } };
}

export const mediaApi = createApi({
    reducerPath: "mediaApi",
    baseQuery,
    tagTypes: ["Media"],
    endpoints: (builder) => ({
        getMedia: builder.query<MediaItem[], void>({
            query: () => "",
            providesTags: ["Media"],
        }),
        createMedia: builder.mutation<MediaItem, CreateMediaArgs>({
            async queryFn({ title, description, image, song }, _api, _extraOptions, request) {
                const uploaded = await uploadFiles(request, image, song);
                if ("error" in uploaded) return uploaded;
                // Upload step 3: the backend checks both files and saves the row.
                const saved = await request({
                    url: "",
                    method: "POST",
                    body: { title, description, ...uploaded.data },
                });
                if (saved.error) return { error: saved.error };
                return { data: saved.data as MediaItem };
            },
            invalidatesTags: ["Media"],
        }),
        updateMedia: builder.mutation<MediaItem, UpdateMediaArgs>({
            async queryFn({ id, title, description, image, song }, _api, _extraOptions, request) {
                const uploaded = await uploadFiles(request, image, song);
                if ("error" in uploaded) return uploaded;
                // Fields left undefined are dropped from the JSON, so the backend keeps them.
                const saved = await request({
                    url: `/${id}`,
                    method: "PATCH",
                    body: { title, description, ...uploaded.data },
                });
                if (saved.error) return { error: saved.error };
                return { data: saved.data as MediaItem };
            },
            invalidatesTags: ["Media"],
        }),
        deleteMedia: builder.mutation<void, string>({
            query: (id) => ({ url: `/${id}`, method: "DELETE" }),
            invalidatesTags: ["Media"],
        }),
    }),
});

export const {
    useGetMediaQuery,
    useCreateMediaMutation,
    useUpdateMediaMutation,
    useDeleteMediaMutation,
} = mediaApi;
