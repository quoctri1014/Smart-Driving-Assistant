import * as SecureStore from 'expo-secure-store';

export async function setToken(token: string) {
    await SecureStore.setItemAsync('token', token);
}

export async function getToken(): Promise<string | null> {
    return await SecureStore.getItemAsync('token');
}

export async function removeToken() {
    await SecureStore.deleteItemAsync('token');
}

export async function isAuthenticated(): Promise<boolean> {
    const token = await getToken();
    return !!token;
}
