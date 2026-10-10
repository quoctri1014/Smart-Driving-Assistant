import React from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { theme } from '../lib/theme';
import { CheckCircle, Clock, Navigation2, ShieldCheck, ChevronRight, Home } from 'lucide-react-native';

function SummaryRow({
  icon: Icon, label, value, color,
}: { icon: any; label: string; value: string; color?: string }) {
  return (
    <View style={styles.row}>
      <View style={[styles.rowIcon, { backgroundColor: color ? `${color}14` : theme.colors.elevated }]}>
        <Icon size={16} color={color ?? theme.colors.text.muted} />
      </View>
      <View style={styles.rowContent}>
        <Text style={styles.rowLabel}>{label}</Text>
        <Text style={styles.rowValue}>{value}</Text>
      </View>
    </View>
  );
}

export default function TripSummary() {
  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Success icon */}
        <View style={styles.iconWrap}>
          <View style={styles.iconOuter}>
            <View style={styles.iconInner}>
              <CheckCircle size={40} color={theme.colors.success} />
            </View>
          </View>
        </View>

        <Text style={styles.title}>Chuyến đi hoàn thành</Text>
        <Text style={styles.subtitle}>Cảm ơn bạn đã lái xe an toàn</Text>

        {/* Stats card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>TÓM TẮT HÀNH TRÌNH</Text>

          <SummaryRow icon={Clock} label="Thời lượng" value="Xem thời gian đã ghi nhận trong lịch sử hành trình" color={theme.colors.info} />
          <View style={styles.divider} />
          <SummaryRow icon={Navigation2} label="Quãng đường" value="Chưa có dữ liệu GPS" color={theme.colors.primary} />
          <View style={styles.divider} />
          <SummaryRow icon={ShieldCheck} label="Điểm an toàn" value="Chưa có chỉ số được xác thực" color={theme.colors.success} />
        </View>

        {/* Safety tip */}
        <View style={styles.tipCard}>
          <Text style={styles.tipTitle}>💡 Mẹo lái xe an toàn</Text>
          <Text style={styles.tipText}>
            Nghỉ ngơi ít nhất 15 phút sau mỗi 2 giờ lái xe liên tục để tránh buồn ngủ và giảm thiểu tai nạn.
          </Text>
        </View>

        {/* Actions */}
        <TouchableOpacity style={styles.primaryBtn} onPress={() => router.replace('/')}>
          <Home size={16} color="white" />
          <Text style={styles.primaryBtnText}>Về trang chủ</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.secondaryBtn} onPress={() => router.replace('/history' as any)}>
          <Text style={styles.secondaryBtnText}>Xem lịch sử hành trình</Text>
          <ChevronRight size={14} color={theme.colors.primary} />
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: theme.colors.bg },
  scroll:  { flex: 1 },
  content: { padding: 20, alignItems: 'center', paddingBottom: 40 },

  iconWrap: { marginTop: 32, marginBottom: 20, alignItems: 'center' },
  iconOuter: {
    width: 96, height: 96, borderRadius: 48,
    backgroundColor: 'rgba(16,185,129,0.10)',
    alignItems: 'center', justifyContent: 'center',
  },
  iconInner: {
    width: 72, height: 72, borderRadius: 36,
    backgroundColor: 'rgba(16,185,129,0.15)',
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: 'rgba(16,185,129,0.25)',
  },

  title:    { fontSize: 22, fontWeight: '700', color: theme.colors.text.primary, marginBottom: 6 },
  subtitle: { fontSize: 13, color: theme.colors.text.muted, marginBottom: 28 },

  card: {
    width: '100%',
    backgroundColor: theme.colors.surface,
    borderRadius: 14,
    borderWidth: 1, borderColor: theme.colors.border,
    padding: 16, marginBottom: 14,
  },
  cardTitle: {
    fontSize: 10, fontWeight: '700', color: theme.colors.text.muted,
    letterSpacing: 1, textTransform: 'uppercase', marginBottom: 14,
  },

  row:     { flexDirection: 'row', alignItems: 'center', paddingVertical: 4 },
  rowIcon: { width: 36, height: 36, borderRadius: 9, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  rowContent: { flex: 1 },
  rowLabel: { fontSize: 11, color: theme.colors.text.muted, marginBottom: 2 },
  rowValue: { fontSize: 14, fontWeight: '600', color: theme.colors.text.primary },

  divider: { height: 1, backgroundColor: theme.colors.border, marginVertical: 10 },

  tipCard: {
    width: '100%',
    backgroundColor: 'rgba(59,127,255,0.07)',
    borderRadius: 12,
    borderWidth: 1, borderColor: 'rgba(59,127,255,0.15)',
    padding: 14, marginBottom: 28,
  },
  tipTitle: { fontSize: 13, fontWeight: '600', color: '#93C5FD', marginBottom: 6 },
  tipText:  { fontSize: 12, color: theme.colors.text.muted, lineHeight: 18 },

  primaryBtn: {
    width: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: theme.colors.primary, paddingVertical: 14,
    borderRadius: 12, marginBottom: 12,
  },
  primaryBtnText: { color: 'white', fontSize: 15, fontWeight: '700' },

  secondaryBtn: {
    width: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4,
    paddingVertical: 12, borderRadius: 12,
    borderWidth: 1, borderColor: theme.colors.border,
    backgroundColor: 'transparent',
  },
  secondaryBtnText: { color: theme.colors.primary, fontSize: 14, fontWeight: '600' },
});
