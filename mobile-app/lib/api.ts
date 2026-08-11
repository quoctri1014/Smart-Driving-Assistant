import { getToken, removeToken } from "./auth";
import { router } from 'expo-router';

// LƯU Ý: Phải thay bằng IP của máy tính (LAN IP) nếu chạy trên thiết bị thật.
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://192.168.1.100:8000/api/v1";

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    const token = await getToken();
    const headers = {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        await removeToken();
        router.replace('/(auth)/login');
        throw new Error("Unauthorized");
    }

    return response;
}

export async function getViolations(skip = 0, limit = 50) {
    const res = await fetchWithAuth(`/violations?skip=${skip}&limit=${limit}`);
    return res.json();
}

export async function resetRestSession() {
    const res = await fetchWithAuth(`/sessions/reset-rest`, { method: "POST" });
    return res.json();
}
