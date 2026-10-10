import { useState, useEffect } from 'react';
import {
  View, Text, FlatList, StyleSheet, Image,
  ActivityIndicator, TouchableOpacity, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AlertOctagon, RefreshCw } from 'lucide-react-native';
import { getViolations } from '../../lib/api';
import { theme } from '../../lib/theme';

const API_BASE = process.env.EXPO_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://192.168.1.100:8000';

const SEVERITY_CONFIG: Record<string, { bg: string; color: string; label: string }> = {
  critical: { bg: 'rgba(239,68,68,0.14)', color: '#FCA5A5',  label: 'Nghiêm trọng' },
  high:     { bg: 'rgba(239,68,68,0.10)', color: '#F87171',  label: 'Cao' },
  medium:   { bg: 'rgba(245,158,11,0.14)', color: '#FCD34D', label: 'Trung bình' },
  low:      { bg: 'rgba(59,127,255,0.12)', color: '#93C5FD', label: 'Thấp' },
};

const TYPE_LABELS: Record<string, string> = {
  no_helmet:  'Không đội mũ',
  speeding:   'Vượt tốc độ',
  no_seatbelt:'Không dây an toàn',
};

function ViolationCard({ item }: { item: any }) {
  const sev = SEVERITY_CONFIG[item.severity] ?? SEVERITY_CONFIG.low;
  const typeLabel = TYPE_LABELS[item.violation_type] ?? item.violation_type?.replace('_', ' ');

  return (
    <View style={styles.card}>
      <View style={styles.cardLeft}>
        {/* Violation type + time */}
        <View style={styles.typeRow}>
          <View style={[styles.typeBadge, { backgroundColor: 'rgba(239,68,68,0.10)' }]}>
            <AlertOctagon size={11} color="#F87171" style={{ marginRight: 4 }} />
            <Text style={[styles.typeBadgeText, { color: '#FCA5A5' }]}>
              {typeLabel.toUpperCase()}
            </Text>
          </View>
          <View style={[styles.sevBadge, { backgroundColor: sev.bg }]}>
            <Text style={[styles.sevText, { color: sev.color }]}>{sev.label}</Text>
          </View>
        </View>

        <Text style={styles.timeText}>
          {new Date(item.timestamp).toLocaleString('vi-VN')}
        </Text>

        {item.plate_text && (
          <View style={styles.plateRow}>
            <Text style={styles.plateLabel}>BSX:</Text>
            <Text style={styles.plateValue}>{item.plate_text}</Text>
          </View>
        )}
      </View>

      {/* Thumbnail */}
      {item.image_path ? (
        <Image
          source={{ uri: `${API_BASE}/${item.image_path.replace('./', '')}` }}
          style={styles.thumb}
          resizeMode="cover"
        />
      ) : (
        <View style={[styles.thumb, styles.thumbPlaceholder]}>
          <AlertOctagon size={22} color={theme.colors.text.disabled} />
        </View>
      )}
    </View>
  );
}

export default function HistoryScreen() {
  const [violations, setViolations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(false);

  const loadData = async () => {
    try {
      setError(false);
      const data = await getViolations(0, 50);
      setViolations(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Lịch sử vi phạm</Text>
            <Text style={styles.subtitle}>
              {violations.length > 0 ? `${violations.length} bản ghi` : 'Không có dữ liệu'}
            </Text>
          </View>
          <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh}>
            <RefreshCw size={16} color={theme.colors.text.muted} />
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={theme.colors.primary} />
            <Text style={styles.loadingText}>Đang tải dữ liệu...</Text>
          </View>
        ) : error ? (
          <View style={styles.center}>
            <AlertOctagon size={40} color={theme.colors.text.muted} style={{ marginBottom: 12 }} />
            <Text style={styles.errorText}>Không thể tải dữ liệu</Text>
            <TouchableOpacity style={styles.retryBtn} onPress={loadData}>
              <Text style={styles.retryText}>Thử lại</Text>
            </TouchableOpacity>
          </View>
        ) : violations.length === 0 ? (
          <View style={styles.center}>
            <AlertOctagon size={48} color={theme.colors.text.disabled} style={{ marginBottom: 12 }} />
            <Text style={styles.emptyTitle}>Chưa có vi phạm</Text>
            <Text style={styles.emptyDesc}>Dữ liệu vi phạm sẽ xuất hiện sau khi AI phát hiện</Text>
          </View>
        ) : (
          <FlatList
            data={violations}
            keyExtractor={(item) => item.id.toString()}
            renderItem={({ item }) => <ViolationCard item={item} />}
            contentContainerStyle={{ paddingBottom: 20 }}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                tintColor={theme.colors.primary}
                colors={[theme.colors.primary]}
              />
            }
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  container: { flex: 1, backgroundColor: theme.colors.bg, paddingHorizontal: 16 },

  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 16, paddingBottom: 20,
  },
  title: { fontSize: 20, fontWeight: '700', color: theme.colors.text.primary },
  subtitle: { fontSize: 12, color: theme.colors.text.muted, marginTop: 2 },

  refreshBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: theme.colors.surface,
    borderWidth: 1, borderColor: theme.colors.border,
    alignItems: 'center', justifyContent: 'center',
  },

  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: theme.colors.border,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardLeft: { flex: 1 },

  typeRow: { flexDirection: 'row', gap: 6, marginBottom: 8 },
  typeBadge: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 6,
  },
  typeBadgeText: { fontSize: 10, fontWeight: '700', letterSpacing: 0.4 },

  sevBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  sevText: { fontSize: 10, fontWeight: '600' },

  timeText: { fontSize: 12, color: theme.colors.text.muted },
  plateRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6 },
  plateLabel: { fontSize: 11, color: theme.colors.text.muted },
  plateValue: {
    fontSize: 12, fontWeight: '700', color: theme.colors.text.primary,
    backgroundColor: theme.colors.elevated,
    paddingHorizontal: 6, paddingVertical: 1, borderRadius: 4,
    fontVariant: ['tabular-nums'],
    letterSpacing: 0.5,
  },

  thumb: { width: 72, height: 72, borderRadius: 10 },
  thumbPlaceholder: {
    backgroundColor: theme.colors.elevated,
    alignItems: 'center', justifyContent: 'center',
  },

  center: {
    flex: 1, alignItems: 'center', justifyContent: 'center', paddingBottom: 60,
  },
  loadingText: { color: theme.colors.text.muted, marginTop: 14, fontSize: 13 },
  errorText: { fontSize: 15, fontWeight: '600', color: theme.colors.text.secondary, marginBottom: 12 },
  emptyTitle: { fontSize: 16, fontWeight: '600', color: theme.colors.text.secondary, marginBottom: 6 },
  emptyDesc: { fontSize: 13, color: theme.colors.text.muted, textAlign: 'center', maxWidth: 240, lineHeight: 18 },

  retryBtn: {
    paddingHorizontal: 20, paddingVertical: 10,
    backgroundColor: theme.colors.primaryBg,
    borderRadius: 10, borderWidth: 1, borderColor: theme.colors.primary,
  },
  retryText: { color: theme.colors.primary, fontWeight: '600', fontSize: 13 },
});
