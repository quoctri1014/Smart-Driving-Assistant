import { useState, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, Image, ActivityIndicator } from 'react-native';
import { getViolations } from '../../lib/api';

const API_BASE = process.env.EXPO_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://192.168.1.100:8000';

export default function HistoryScreen() {
    const [violations, setViolations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await getViolations(0, 50);
            setViolations(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const renderItem = ({ item }: { item: any }) => (
        <View style={styles.card}>
            <View style={styles.info}>
                <Text style={styles.type}>{item.violation_type.toUpperCase()}</Text>
                <Text style={styles.time}>{new Date(item.timestamp).toLocaleString('vi-VN')}</Text>
                <Text style={[styles.severity, item.severity === 'critical' ? styles.critical : styles.warning]}>
                    Mức độ: {item.severity}
                </Text>
            </View>
            {item.image_path ? (
                <Image 
                    source={{ uri: `${API_BASE}/${item.image_path.replace('./', '')}` }} 
                    style={styles.image} 
                />
            ) : (
                <View style={styles.noImage}><Text>No Image</Text></View>
            )}
        </View>
    );

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Lịch sử Vi phạm</Text>
            {loading ? (
                <ActivityIndicator size="large" color="#2563eb" style={{marginTop: 50}} />
            ) : (
                <FlatList 
                    data={violations}
                    keyExtractor={item => item.id.toString()}
                    renderItem={renderItem}
                    contentContainerStyle={{ paddingBottom: 20 }}
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f8fafc', padding: 15 },
    header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, color: '#1e293b', marginTop: 40 },
    card: { backgroundColor: 'white', borderRadius: 12, padding: 15, marginBottom: 15, flexDirection: 'row', elevation: 2 },
    info: { flex: 1, justifyContent: 'center' },
    type: { fontSize: 16, fontWeight: 'bold', color: '#334155' },
    time: { fontSize: 13, color: '#64748b', marginTop: 4 },
    severity: { fontSize: 14, fontWeight: 'bold', marginTop: 8 },
    critical: { color: '#ef4444' },
    warning: { color: '#eab308' },
    image: { width: 80, height: 80, borderRadius: 8, backgroundColor: '#e2e8f0' },
    noImage: { width: 80, height: 80, borderRadius: 8, backgroundColor: '#e2e8f0', justifyContent: 'center', alignItems: 'center' }
});
