import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { removeToken } from '../../lib/auth';
import { resetRestSession } from '../../lib/api';
import { router } from 'expo-router';

export default function ProfileScreen() {
    
    const handleLogout = async () => {
        await removeToken();
        router.replace('/(auth)/login');
    };

    const handleRest = async () => {
        try {
            await resetRestSession();
            Alert.alert("Thành công", "Đã ghi nhận bạn vừa nghỉ ngơi. Chúc bạn lái xe an toàn!");
        } catch (err) {
            Alert.alert("Lỗi", "Không thể ghi nhận trạng thái nghỉ ngơi lúc này.");
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <View style={styles.avatar} />
                <Text style={styles.name}>Tài xế Demo</Text>
                <Text style={styles.email}>demo@example.com</Text>
            </View>

            <View style={styles.actions}>
                <TouchableOpacity style={[styles.button, styles.restButton]} onPress={handleRest}>
                    <Text style={styles.buttonText}>☕ Tôi đã nghỉ ngơi</Text>
                </TouchableOpacity>

                <TouchableOpacity style={[styles.button, styles.logoutButton]} onPress={handleLogout}>
                    <Text style={[styles.buttonText, { color: '#ef4444' }]}>Đăng xuất</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f8fafc', padding: 20 },
    header: { alignItems: 'center', marginTop: 60, marginBottom: 40 },
    avatar: { width: 100, height: 100, borderRadius: 50, backgroundColor: '#cbd5e1', marginBottom: 15 },
    name: { fontSize: 24, fontWeight: 'bold', color: '#1e293b' },
    email: { fontSize: 16, color: '#64748b' },
    actions: { gap: 15 },
    button: { padding: 15, borderRadius: 12, alignItems: 'center', backgroundColor: 'white', borderWidth: 1, borderColor: '#e2e8f0' },
    restButton: { backgroundColor: '#3b82f6', borderColor: '#3b82f6' },
    logoutButton: { borderColor: '#ef4444' },
    buttonText: { fontSize: 16, fontWeight: 'bold', color: 'white' }
});
