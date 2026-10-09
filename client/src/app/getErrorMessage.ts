import type { SerializedError } from "@reduxjs/toolkit";
import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";

interface ValidationIssue {
    loc: (string | number)[];
    msg: string;
}

export function getErrorMessage(error: FetchBaseQueryError | SerializedError): string {
    if (!("status" in error)) return error.message ?? "Something went wrong";
    if (error.status === "FETCH_ERROR") return "Could not reach the server";

    const data = error.data as { message?: unknown; detail?: unknown } | undefined;
    if (typeof data?.message === "string") return data.message;
    if (Array.isArray(data?.detail)) {
        return (data.detail as ValidationIssue[])
            .map((issue) => `${issue.loc.at(-1)}: ${issue.msg}`)
            .join(". ");
    }
    return "Something went wrong";
}
