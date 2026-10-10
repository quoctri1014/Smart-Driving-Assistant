import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  StatusBar,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import {
  ShieldCheck,
  Car,
  AlertTriangle,
  Clock,
  TrendingUp,
  Cpu,
  ChevronRight,
  Activity,
  Zap,
  Eye,
  CheckCircle2,
} from 'lucide-react-native';
import { theme } from '../../lib/theme';
import { getToken } from '../../lib/auth';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://192.168.1.100:8000/api/v1';
const { width } = Dimensions.get('window');

interface DashboardStats {
  safetyScore: number;
  totalTrips: number;
  totalDistanceKm: number;
  totalDrivingHours: number;
  totalViolations: number;
  recentViolations: Array<{
    id: number;
    type: string;
    timestamp: string;
    severity: 'low' | 'medium' | 'high';
  }>;
}

export default function MobileDashboardScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<DashboardStats>({
    safetyScore: 100,
    totalTrips: 0,
    totalDistanceKm: 0,
    totalDrivingHours: 0,
    totalViolations: 0,
    recentViolations: [],
  });

  const loadData = async () => {
    try {
      const token = await getToken();

      // Fetch sessions and violations
      const [sessRes, violRes] = await Promise.all([
        fetch(`${API_URL}/sessions/?skip=0&limit=50`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }).catch(() => null),
        fetch(`${API_URL}/violations/?skip=0&limit=10`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }).catch(() => null),
      ]);

      let tripCount = 0;
      let distKm = 0;
      let driveHours = 0;
      let violCount = 0;

      if (sessRes && sessRes.ok) {
        const sessData = await sessRes.json();
        if (Array.isArray(sessData)) {
          tripCount = sessData.length;
          const totalMins = sessData.reduce((acc: number, s: any) => acc + (s.total_minutes || 0), 0);
          driveHours = parseFloat((totalMins / 60).toFixed(1));
          distKm = parseFloat((driveHours * 40).toFixed(1));
        }
      }

      let recentViols: any[] = [];
      if (violRes && violRes.ok) {
        const violData = await violRes.json();
        if (Array.isArray(violData)) {
          violCount = violData.length;
          recentViols = violData.slice(0, 5).map((v: any) => ({
            id: v.id,
            type: v.violation_type,
            timestamp: new Date(v.timestamp).toLocaleString('vi-VN', {
              hour: '2-digit',
              minute: '2-digit',
              day: '2-digit',
              month: '2-digit',
            }),
            severity: v.violation_type.includes('Drowsiness') || v.violation_type.includes('Collision') ? 'high' : 'medium',
          }));
        }
      }
      const calculatedScore = Math.max(60, 100 - violCount * 3);

      setStats({
        safetyScore: calculatedScore,
        totalTrips: tripCount,
        totalDistanceKm: distKm,
        totalDrivingHours: driveHours,
        totalViolations: violCount,
        recentViolations: recentViols,
      });
    } catch (e) {
      console.warn('Dashboard fetch error', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return theme.colors.success;
    if (score >= 75) return theme.colors.primary;
    if (score >= 60) return theme.colors.warning;
    return theme.colors.danger;
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Lái xe rất an toàn';
    if (score >= 75) return 'An toàn - Ổn định';
    if (score >= 60) return 'Cần cẩn thận hơn';
    return 'Rủi ro cao';
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="#0B0F17" />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Xin chào,</Text>
          <Text style={styles.driverName}>Tài xế Nguyễn Văn A</Text>
        </View>
        <View style={styles.aiBadge}>
          <Activity size={12} color="#10B981" />
          <Text style={styles.aiBadgeText}>AI Sẵn sàng</Text>
        </View>
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.primary}
          />
        }
      >
        {/* Main Drive CTA Button */}
        <TouchableOpacity
          style={styles.driveCtaButton}
          activeOpacity={0.88}
          onPress={() => router.push('/drive')}
        >
          <View style={styles.driveCtaGlow} />
          <View style={styles.driveCtaLeft}>
            <View style={styles.driveIconWrap}>
              <Car size={26} color="#ffffff" />
            </View>
            <View>
              <Text style={styles.driveCtaTitle}>Bắt đầu chuyến đi</Text>
              <Text style={styles.driveCtaSubtitle}>Kích hoạt 12 hệ thống AI hỗ trợ lái xe</Text>
            </View>
          </View>
          <View style={styles.driveCtaArrow}>
            <ChevronRight size={22} color="#ffffff" />
          </View>
        </TouchableOpacity>

        {/* Safety Score Card */}
        <View style={styles.scoreCard}>
          <View style={styles.scoreHeader}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <ShieldCheck size={20} color={getScoreColor(stats.safetyScore)} />
              <Text style={styles.cardTitle}>Điểm An Toàn Hành Trình</Text>
            </View>
            <Text style={[styles.scoreBadgeText, { color: getScoreColor(stats.safetyScore) }]}>
              {getScoreLabel(stats.safetyScore)}
            </Text>
          </View>

          <View style={styles.scoreBody}>
            <View style={styles.scoreNumberWrap}>
              <Text style={[styles.scoreNumber, { color: getScoreColor(stats.safetyScore) }]}>
                {stats.safetyScore}
              </Text>
              <Text style={styles.scoreMax}>/100</Text>
            </View>
            <View style={styles.scoreProgressTrack}>
              <View
                style={[
                  styles.scoreProgressFill,
                  {
                    width: `${stats.safetyScore}%`,
                    backgroundColor: getScoreColor(stats.safetyScore),
                  },
                ]}
              />
            </View>
            <Text style={styles.scoreTip}>
              {stats.safetyScore >= 90
                ? 'Tuyệt vời! Bạn đang duy trì khoảng cách và sự tập trung rất tốt.'
                : 'Chú ý quan sát khoảng cách an toàn và nghỉ ngơi khi buồn ngủ.'}
            </Text>
          </View>
        </View>

        {/* Quick KPI Stats Grid */}
        <View style={styles.kpiGrid}>
          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrap, { backgroundColor: 'rgba(59,130,246,0.12)' }]}>
              <Car size={18} color="#3B82F6" />
            </View>
            <Text style={styles.kpiValue}>{stats.totalTrips}</Text>
            <Text style={styles.kpiLabel}>Chuyến đi</Text>
          </View>

          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrap, { backgroundColor: 'rgba(16,185,129,0.12)' }]}>
              <TrendingUp size={18} color="#10B981" />
            </View>
            <Text style={styles.kpiValue}>{stats.totalDistanceKm} <Text style={styles.kpiUnit}>km</Text></Text>
            <Text style={styles.kpiLabel}>Quãng đường</Text>
          </View>

          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrap, { backgroundColor: 'rgba(168,85,247,0.12)' }]}>
              <Clock size={18} color="#A855F7" />
            </View>
            <Text style={styles.kpiValue}>{stats.totalDrivingHours} <Text style={styles.kpiUnit}>giờ</Text></Text>
            <Text style={styles.kpiLabel}>Thời gian lái</Text>
          </View>

          <View style={styles.kpiCard}>
            <View style={[styles.kpiIconWrap, { backgroundColor: 'rgba(239,68,68,0.12)' }]}>
              <AlertTriangle size={18} color="#EF4444" />
            </View>
            <Text style={[styles.kpiValue, { color: stats.totalViolations > 0 ? '#F87171' : '#10B981' }]}>
              {stats.totalViolations}
            </Text>
            <Text style={styles.kpiLabel}>Cảnh báo</Text>
          </View>
        </View>

        {/* AI Engine Status Overview */}
        <View style={styles.aiStatusCard}>
          <View style={styles.aiStatusHeader}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Cpu size={18} color="#3B82F6" />
              <Text style={styles.cardTitle}>Hệ Thống Trí Tuệ Nhân Tạo</Text>
            </View>
            <View style={styles.activePill}>
              <Text style={styles.activePillText}>12/12 Hoạt động</Text>
            </View>
          </View>

          <View style={styles.aiFeatureList}>
            {[
              { label: 'Nhận diện phương tiện & Tracker', active: true },
              { label: 'Cảnh báo khoảng cách & va chạm', active: true },
              { label: 'Giám sát buồn ngủ & chớp mắt', active: true },
              { label: 'Nhận diện biển báo & gợi ý tốc độ', active: true },
              { label: 'Kiểm tra thắt dây an toàn & Mũ BH', active: true },
              { label: 'Đếm xe theo làn & Biển số OCR', active: true },
            ].map((feat, idx) => (
              <View key={idx} style={styles.aiFeatureItem}>
                <CheckCircle2 size={14} color="#10B981" />
                <Text style={styles.aiFeatureText}>{feat.label}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Recent Violations / Alerts */}
        <View style={styles.recentSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.cardTitle}>Cảnh Báo Gần Nhất</Text>
            <TouchableOpacity onPress={() => router.push('/(tabs)/history')}>
              <Text style={styles.viewAllText}>Xem tất cả</Text>
            </TouchableOpacity>
          </View>

          {stats.recentViolations.length === 0 ? (
            <View style={styles.emptyViolations}>
              <CheckCircle2 size={32} color="#10B981" />
              <Text style={styles.emptyViolationsText}>Không có cảnh báo vi phạm nào!</Text>
            </View>
          ) : (
            stats.recentViolations.map((v) => (
              <View key={v.id} style={styles.violationItem}>
                <View
                  style={[
                    styles.violationDot,
                    {
                      backgroundColor:
                        v.severity === 'high' ? '#EF4444' : '#F59E0B',
                    },
                  ]}
                />
                <View style={{ flex: 1 }}>
                  <Text style={styles.violationType}>{v.type}</Text>
                  <Text style={styles.violationTime}>{v.timestamp}</Text>
                </View>
                <View
                  style={[
                    styles.severityBadge,
                    {
                      backgroundColor:
                        v.severity === 'high'
                          ? 'rgba(239,68,68,0.15)'
                          : 'rgba(245,158,11,0.15)',
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.severityText,
                      {
                        color:
                          v.severity === 'high' ? '#F87171' : '#FBBF24',
                      },
                    ]}
                  >
                    {v.severity === 'high' ? 'Cao' : 'Vừa'}
                  </Text>
                </View>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0B0F17',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
    backgroundColor: '#111827',
  },
  greeting: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  driverName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#F9FAFB',
    marginTop: 1,
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    backgroundColor: 'rgba(16,185,129,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.3)',
  },
  aiBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#10B981',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    gap: 16,
    paddingBottom: 32,
  },
  driveCtaButton: {
    position: 'relative',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#2563EB',
    borderRadius: 16,
    padding: 18,
    overflow: 'hidden',
    shadowColor: '#2563EB',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 8,
  },
  driveCtaGlow: {
    position: 'absolute',
    top: -20,
    right: -20,
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  driveCtaLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    flex: 1,
  },
  driveIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  driveCtaTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  driveCtaSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
  driveCtaArrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreCard: {
    backgroundColor: '#111827',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.07)',
  },
  scoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#F3F4F6',
  },
  scoreBadgeText: {
    fontSize: 12,
    fontWeight: '700',
  },
  scoreBody: {
    alignItems: 'center',
    paddingVertical: 6,
  },
  scoreNumberWrap: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  scoreNumber: {
    fontSize: 42,
    fontWeight: '900',
    letterSpacing: -1,
  },
  scoreMax: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginLeft: 4,
  },
  scoreProgressTrack: {
    width: '100%',
    height: 8,
    backgroundColor: '#1F2937',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 10,
  },
  scoreProgressFill: {
    height: '100%',
    borderRadius: 4,
  },
  scoreTip: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
    marginTop: 2,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  kpiCard: {
    width: (width - 32 - 10) / 2,
    backgroundColor: '#111827',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.07)',
  },
  kpiIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  kpiValue: {
    fontSize: 20,
    fontWeight: '800',
    color: '#F9FAFB',
  },
  kpiUnit: {
    fontSize: 12,
    fontWeight: '500',
    color: '#9CA3AF',
  },
  kpiLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  aiStatusCard: {
    backgroundColor: '#111827',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.07)',
  },
  aiStatusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  activePill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    backgroundColor: 'rgba(59,130,246,0.15)',
  },
  activePillText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#60A5FA',
  },
  aiFeatureList: {
    gap: 8,
  },
  aiFeatureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  aiFeatureText: {
    fontSize: 12,
    color: '#D1D5DB',
  },
  recentSection: {
    backgroundColor: '#111827',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.07)',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  viewAllText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#3B82F6',
  },
  emptyViolations: {
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  emptyViolationsText: {
    fontSize: 13,
    color: '#9CA3AF',
  },
  violationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
    gap: 10,
  },
  violationDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  violationType: {
    fontSize: 13,
    fontWeight: '600',
    color: '#E5E7EB',
  },
  violationTime: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 2,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  severityText: {
    fontSize: 10,
    fontWeight: '700',
  },
});
