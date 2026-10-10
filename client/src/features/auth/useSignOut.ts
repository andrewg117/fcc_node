import { useCallback } from "react";
import { useAppDispatch } from "../../app/hooks";
import { mediaApi } from "../media/mediaApi";
import { authApi } from "./authApi";
import { logout } from "./authSlice";

export function useSignOut() {
    const dispatch = useAppDispatch();
    return useCallback(() => {
        dispatch(logout());
        dispatch(authApi.util.resetApiState());
        dispatch(mediaApi.util.resetApiState());
    }, [dispatch]);
}
