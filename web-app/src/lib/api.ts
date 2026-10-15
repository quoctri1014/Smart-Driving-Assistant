import { getToken } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` : "http://127.0.0.1:8000/api/v1";

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    const token = getToken();
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
        // Handle unauthorized
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
        throw new Error("Unauthorized");
    }

    return response;
}

export async function getViolations(skip = 0, limit = 50) {
    const res = await fetchWithAuth(`/violations?skip=${skip}&limit=${limit}`);
    return res.json();
}

export async function getSessions(skip = 0, limit = 50) {
    const res = await fetchWithAuth(`/sessions?skip=${skip}&limit=${limit}`);
    return res.json();
}
