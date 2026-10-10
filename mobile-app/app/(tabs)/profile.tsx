import { View, Text, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { removeToken } from '../../lib/auth';
import { resetRestSession } from '../../lib/api';
import { router } from 'expo-router';
import { Coffee, LogOut, ChevronRight, User, Shield, Bell, Info } from 'lucide-react-native';
import { theme } from '../../lib/theme';
import { useEffect, useState } from 'react';
import { fetchWithAuth } from '../../lib/api';

function MenuRow({
  icon: Icon, label, color, onPress, isDestructive = false,
}: {
  icon: any; label: string; color?: string; onPress: () => void; isDestructive?: boolean;
}) {
  const iconColor = isDestructive ? theme.colors.danger : (color ?? theme.colors.primary);
  return (
    <TouchableOpacity
      style={styles.menuRow}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.menuIcon, { backgroundColor: isDestructive ? theme.colors.dangerBg : (color ? `${color}14` : theme.colors.primaryBg) }]}>
        <Icon size={16} color={iconColor} />
      </View>
      <Text style={[styles.menuLabel, isDestructive && { color: theme.colors.danger }]}>{label}</Text>
      <ChevronRight size={14} color={theme.colors.text.muted} style={{ marginLeft: 'auto' }} />
    </TouchableOpacity>
  );
}

export default function ProfileScreen() {
  const [profile, setProfile] = useState<{ full_name: string; email: string; role: string } | null>(null);
  useEffect(() => { fetchWithAuth('/auth/me').then(res => {
    if (!res.ok) throw new Error('Profile unavailable');
    return res.json();
  }).then(setProfile).catch(() => setProfile(null)); }, []);
  const handleLogout = async () => {
    Alert.alert('Đăng xuất', 'Bạn có chắc muốn đăng xuất không?', [
      { text: 'Huỷ', style: 'cancel' },
      {
        text: 'Đăng xuất', style: 'destructive',
        onPress: async () => {
          await removeToken();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  const handleRest = async () => {
    try {
      await resetRestSession();
      Alert.alert('✓ Ghi nhận thành công', 'Đã ghi nhận bạn vừa nghỉ ngơi. Chúc bạn lái xe an toàn!');
    } catch {
      Alert.alert('Lỗi', 'Không thể ghi nhận trạng thái nghỉ ngơi lúc này.');
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* Profile header card */}
        <View style={styles.profileCard}>
          <View style={styles.avatarWrap}>
            <View style={styles.avatar}>
              <User size={32} color="rgba(255,255,255,0.8)" />
            </View>
          </View>
          <Text style={styles.name}>{profile?.full_name || 'Chưa tải được hồ sơ'}</Text>
          <Text style={styles.email}>{profile?.email || '—'}</Text>
          <View style={styles.roleBadge}>
            <Shield size={11} color={theme.colors.primary} style={{ marginRight: 4 }} />
            <Text style={styles.roleText}>
              {profile?.role === 'ENTERPRISE_ADMIN'
                ? 'Quản trị doanh nghiệp'
                : profile?.role === 'FLEET_DISPATCHER'
                ? 'Điều độ viên'
                : 'Tài xế đội xe'}
            </Text>
          </View>
        </View>

        {/* Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Hành động nhanh</Text>
          <View style={styles.menuCard}>
            <MenuRow
              icon={Coffee}
              label="Ghi nhận đã nghỉ ngơi"
              color={theme.colors.success}
              onPress={handleRest}
            />
          </View>
        </View>

        {/* Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Cài đặt</Text>
          <View style={styles.menuCard}>
            <MenuRow
              icon={Bell}
              label="Thông báo"
              onPress={() => Alert.alert('Sắp ra mắt', 'Tính năng này đang được phát triển')}
            />
            <View style={styles.divider} />
            <MenuRow
              icon={Info}
              label="Về ứng dụng"
              onPress={() => Alert.alert('Smart Driving Assistant', 'Phiên bản 2.0\nHệ thống AI giám sát giao thông')}
            />
          </View>
        </View>

        {/* Logout */}
        <View style={[styles.section, { marginBottom: 32 }]}>
          <View style={styles.menuCard}>
            <MenuRow
              icon={LogOut}
              label="Đăng xuất"
              onPress={handleLogout}
              isDestructive
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: theme.colors.bg },
  container: { flex: 1, backgroundColor: theme.colors.bg, paddingHorizontal: 16 },

  profileCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 16, borderWidth: 1, borderColor: theme.colors.border,
    alignItems: 'center', paddingVertical: 28, paddingHorizontal: 20,
    marginTop: 16, marginBottom: 24,
  },
  avatarWrap: {
    width: 76, height: 76, borderRadius: 38,
    padding: 3,
    backgroundColor: 'transparent',
    marginBottom: 12,
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(59,127,255,0.3)',
  },
  avatar: {
    width: 68, height: 68, borderRadius: 34,
    backgroundColor: theme.colors.elevated,
    alignItems: 'center', justifyContent: 'center',
  },
  name: { fontSize: 18, fontWeight: '700', color: theme.colors.text.primary },
  email: { fontSize: 13, color: theme.colors.text.muted, marginTop: 3 },
  roleBadge: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: theme.colors.primaryBg,
    paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 100, marginTop: 12,
    borderWidth: 1, borderColor: 'rgba(59,127,255,0.18)',
  },
  roleText: { fontSize: 11, fontWeight: '600', color: theme.colors.primary },

  section: { marginBottom: 16 },
  sectionTitle: {
    fontSize: 11, fontWeight: '600', color: theme.colors.text.muted,
    textTransform: 'uppercase', letterSpacing: 0.8,
    marginBottom: 8, paddingLeft: 4,
  },

  menuCard: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12, borderWidth: 1, borderColor: theme.colors.border,
    overflow: 'hidden',
  },
  menuRow: {
    flexDirection: 'row', alignItems: 'center',
    padding: 14, gap: 12,
  },
  menuIcon: {
    width: 32, height: 32, borderRadius: 8,
    alignItems: 'center', justifyContent: 'center',
  },
  menuLabel: {
    fontSize: 14, fontWeight: '500', color: theme.colors.text.primary, flex: 1,
  },
  divider: { height: 1, backgroundColor: theme.colors.border, marginHorizontal: 14 },
});
