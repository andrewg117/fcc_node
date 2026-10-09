import { useCallback } from "react";
import { useAppDispatch } from "../../app/hooks";
import { authApi } from "./authApi";
import { logout } from "./authSlice";

export function useSignOut() {
    const dispatch = useAppDispatch();
    return useCallback(() => {
        dispatch(logout());
        dispatch(authApi.util.resetApiState());
    }, [dispatch]);
}
