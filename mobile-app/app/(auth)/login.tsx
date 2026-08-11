import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { router } from 'expo-router';
import { setToken } from '../../lib/auth';

const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://192.168.1.100:8000/api/v1";

export default function LoginScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = async () => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const res = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString()
            });

            if (!res.ok) throw new Error("Sai email hoặc mật khẩu");

            const data = await res.json();
            await setToken(data.access_token);
            router.replace('/(tabs)/live');
        } catch (err: any) {
            Alert.alert("Lỗi", err.message || "Không thể đăng nhập");
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Smart Driving</Text>
            <Text style={styles.subtitle}>Đăng nhập để xem lịch sử</Text>
            
            <TextInput 
                style={styles.input}
                placeholder="Email (demo@example.com)"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
            />
            <TextInput 
                style={styles.input}
                placeholder="Mật khẩu"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />
            
            <TouchableOpacity style={styles.button} onPress={handleLogin}>
                <Text style={styles.buttonText}>Đăng nhập</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#f8fafc' },
    title: { fontSize: 32, fontWeight: 'bold', color: '#1e293b', textAlign: 'center' },
    subtitle: { fontSize: 16, color: '#64748b', textAlign: 'center', marginBottom: 40 },
    input: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 15, borderWidth: 1, borderColor: '#e2e8f0' },
    button: { backgroundColor: '#2563eb', padding: 15, borderRadius: 10, alignItems: 'center' },
    buttonText: { color: 'white', fontWeight: 'bold', fontSize: 16 }
});
