import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Animated, Easing,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { theme } from '../lib/theme';
import {
  ShieldAlert, X, Wifi, WifiOff, ChevronDown, Navigation,
} from 'lucide-react-native';
import { useDrivingSocket } from '../lib/useDrivingSocket';
import { deriveDrivingUIState } from '../lib/driving/alert-engine';

type SessionState = 'IDLE' | 'PREPARING' | 'CONNECTING' | 'STREAMING' | 'STOPPING' | 'ENDED' | 'ERROR';

const ALERT_STYLE: Record<string, { bg: string; border: string; text: string }> = {
  normal:   { bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.3)', text: '#34D399' },
  warning:  { bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.3)', text: '#FCD34D' },
  danger:   { bg: 'rgba(239,68,68,0.15)',  border: 'rgba(239,68,68,0.3)',  text: '#FCA5A5' },
};

export default function DriveMode() {
  const [permission, requestPermission] = useCameraPermissions();
  const [sessionState, setSessionState] = useState<SessionState>('IDLE');
  const [simulatedSpeed, setSimulatedSpeed] = useState(55);

  const cameraRef       = useRef<CameraView>(null);
  const isProcessing    = useRef(false);
  const captureInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const pulseAnim       = useRef(new Animated.Value(1)).current;

  const {
    status: socketStatus, result: roadResult, isStale,
    connect, disconnect, sendFrame, sendMetadata,
  } = useDrivingSocket();

  const uiState = deriveDrivingUIState(roadResult, null, isStale, true);
  const isStreaming = sessionState === 'STREAMING';
  const isDanger    = uiState.priority === 'COLLISION_DANGER';

  /* Pulse animation for live dot */
  useEffect(() => {
    if (!isStreaming) return;
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 0.4, duration: 900, useNativeDriver: true, easing: Easing.ease }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 900, useNativeDriver: true, easing: Easing.ease }),
      ])
    ).start();
    return () => pulseAnim.setValue(1);
  }, [isStreaming]);

  const startCapture = useCallback(() => {
    captureInterval.current = setInterval(async () => {
      if (isProcessing.current || !cameraRef.current) return;
      isProcessing.current = true;
      try {
        const photo = await cameraRef.current.takePictureAsync({ quality: 0.5, base64: true });
        if (photo?.base64) {
          await sendFrame(photo.base64);
          sendMetadata({ vehicle_speed: simulatedSpeed });
        }
      } catch { /* silent */ }
      finally { isProcessing.current = false; }
    }, 500);
  }, [sendFrame, sendMetadata, simulatedSpeed]);

  const stopCapture = useCallback(() => {
    if (captureInterval.current) { clearInterval(captureInterval.current); captureInterval.current = null; }
  }, []);

  useEffect(() => {
    if (sessionState === 'CONNECTING' && socketStatus === 'CONNECTED') {
      setSessionState('STREAMING');
      startCapture();
    }
    if ((socketStatus === 'ERROR' || socketStatus === 'DISCONNECTED') && sessionState === 'STREAMING') {
      stopCapture();
      setSessionState('ERROR');
    }
  }, [socketStatus, sessionState, startCapture, stopCapture]);

  const handleStart = () => { setSessionState('CONNECTING'); connect(); };
  const handleEnd   = () => {
    setSessionState('STOPPING');
    stopCapture(); disconnect();
    setSessionState('ENDED');
    router.replace('/trip-summary' as any);
  };

  /* ── Permission screens ── */
  if (!permission) return <View style={{ flex: 1, backgroundColor: theme.colors.bg }} />;
  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.permWrap}>
        <View style={styles.permCard}>
          <ShieldAlert size={40} color={theme.colors.warning} style={{ marginBottom: 16 }} />
          <Text style={styles.permTitle}>Yêu cầu quyền Camera</Text>
          <Text style={styles.permDesc}>Cần quyền truy cập camera để phân tích AI và phát hiện nguy hiểm theo thời gian thực.</Text>
          <TouchableOpacity style={styles.permBtn} onPress={requestPermission}>
            <Text style={styles.permBtnText}>Cấp quyền truy cập</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const alertStyle = isDanger ? ALERT_STYLE.danger
    : (uiState.priority !== 'NORMAL' && uiState.priority !== 'UNAVAILABLE') ? ALERT_STYLE.warning
    : ALERT_STYLE.normal;

  return (
    <View style={styles.root}>
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />

      {/* ── Danger full-screen overlay ── */}
      {isDanger && (
        <View style={styles.dangerOverlay}>
          <ShieldAlert size={64} color="white" />
          <Text style={styles.dangerTitle}>{uiState.message}</Text>
          <Text style={styles.dangerSub}>GIẢM TỐC NGAY!</Text>
        </View>
      )}

      {/* ── Main HUD ── */}
      <View style={styles.hud}>
        {/* Top bar */}
        <SafeAreaView edges={['top']}>
          <View style={styles.topBar}>
            <TouchableOpacity
              style={styles.iconBtn}
              onPress={() => { stopCapture(); disconnect(); router.back(); }}
            >
              <X size={18} color={theme.colors.text.primary} />
            </TouchableOpacity>

            {/* Status indicator */}
            <View style={styles.statusPill}>
              <Animated.View style={[styles.statusDot, {
                backgroundColor: isStreaming ? theme.colors.success
                  : sessionState === 'ERROR' ? theme.colors.danger : '#475569',
                opacity: isStreaming ? pulseAnim : 1,
              }]} />
              {socketStatus === 'CONNECTED' || isStreaming
                ? <Wifi size={11} color={theme.colors.success} />
                : <WifiOff size={11} color={theme.colors.text.muted} />
              }
              <Text style={styles.statusText}>
                {isStreaming ? 'AI LIVE'
                  : sessionState === 'CONNECTING' ? 'KẾT NỐI...'
                  : sessionState === 'ERROR' ? 'LỖI KẾT NỐI'
                  : 'CHỜ BẮT ĐẦU'}
              </Text>
            </View>

            {/* Speed adjust */}
            <View style={styles.speedAdj}>
              <TouchableOpacity onPress={() => setSimulatedSpeed(s => Math.max(0, s - 5))} style={styles.adjBtn}>
                <Text style={styles.adjBtnText}>−</Text>
              </TouchableOpacity>
              <Text style={styles.adjLabel}>SPD</Text>
              <TouchableOpacity onPress={() => setSimulatedSpeed(s => Math.min(200, s + 5))} style={styles.adjBtn}>
                <Text style={styles.adjBtnText}>+</Text>
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>

        {/* Alert banner */}
        {!isDanger && uiState.priority !== 'NORMAL' && uiState.priority !== 'UNAVAILABLE' && isStreaming && (
          <View style={[styles.alertBanner, { backgroundColor: alertStyle.bg, borderColor: alertStyle.border }]}>
            <ChevronDown size={14} color={alertStyle.text} style={{ marginRight: 6 }} />
            <Text style={[styles.alertText, { color: alertStyle.text }]}>{uiState.message}</Text>
          </View>
        )}

        {/* Bottom HUD */}
        <SafeAreaView edges={['bottom']} style={styles.bottomWrap}>
          <View style={styles.bottomHud}>
            {/* Speed panel */}
            <View style={styles.speedPanel}>
              <Text style={styles.speedLabel}>TỐCKM/H (GIẢ LẬP)</Text>
              <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 4 }}>
                <Text style={styles.speedValue}>{simulatedSpeed}</Text>
                <Text style={styles.speedUnit}>km/h</Text>
              </View>
              {uiState.recommendedSpeed != null && (
                <View style={styles.recRow}>
                  <Navigation size={11} color={theme.colors.success} />
                  <Text style={styles.recText}>Đề xuất: {uiState.recommendedSpeed} km/h</Text>
                </View>
              )}
            </View>

            {/* Start / Stop button */}
            <TouchableOpacity
              style={[
                styles.actionBtn,
                {
                  backgroundColor: isStreaming ? theme.colors.danger
                    : sessionState === 'CONNECTING' ? '#1E3A8A'
                    : theme.colors.primary,
                  opacity: (sessionState === 'CONNECTING' || sessionState === 'STOPPING') ? 0.7 : 1,
                },
              ]}
              onPress={isStreaming ? handleEnd : handleStart}
              disabled={sessionState === 'CONNECTING' || sessionState === 'STOPPING'}
              activeOpacity={0.85}
            >
              <Text style={styles.actionBtnText}>
                {isStreaming ? 'KẾT THÚC' : sessionState === 'CONNECTING' ? 'ĐANG KẾT NỐI' : 'BẮT ĐẦU LÁI'}
              </Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: 'black' },
  hud:  { position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, justifyContent: 'space-between' },

  dangerOverlay: {
    position: 'absolute', top: 0, bottom: 0, left: 0, right: 0,
    backgroundColor: 'rgba(220,38,38,0.75)',
    alignItems: 'center', justifyContent: 'center', zIndex: 20,
  },
  dangerTitle: { color: 'white', fontSize: 28, fontWeight: '900', marginTop: 16, textAlign: 'center' },
  dangerSub:   { color: 'rgba(255,255,255,0.9)', fontSize: 18, fontWeight: '700', marginTop: 8, letterSpacing: 2 },

  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },

  iconBtn: {
    width: 40, height: 40, borderRadius: 10,
    backgroundColor: 'rgba(10,14,26,0.75)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
    alignItems: 'center', justifyContent: 'center',
  },
  statusPill: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    backgroundColor: 'rgba(10,14,26,0.80)',
    paddingHorizontal: 12, paddingVertical: 7,
    borderRadius: 100, borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
  },
  statusDot: { width: 7, height: 7, borderRadius: 4 },
  statusText: { color: 'rgba(255,255,255,0.85)', fontSize: 11, fontWeight: '700', letterSpacing: 0.8 },

  speedAdj: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  adjBtn: {
    width: 28, height: 28, borderRadius: 8,
    backgroundColor: 'rgba(10,14,26,0.75)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
    alignItems: 'center', justifyContent: 'center',
  },
  adjBtnText: { color: 'white', fontSize: 18, fontWeight: '300', lineHeight: 26 },
  adjLabel: { color: 'rgba(255,255,255,0.5)', fontSize: 10, fontWeight: '700' },

  alertBanner: {
    flexDirection: 'row', alignItems: 'center',
    alignSelf: 'center', marginTop: 12,
    paddingHorizontal: 16, paddingVertical: 10,
    borderRadius: 10, borderWidth: 1,
    maxWidth: '85%',
  },
  alertText: { fontSize: 13, fontWeight: '600', flex: 1 },

  bottomWrap: { padding: 16 },
  bottomHud: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12 },

  speedPanel: {
    backgroundColor: 'rgba(10,14,26,0.82)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)',
    borderRadius: 14, padding: 14,
  },
  speedLabel: { fontSize: 9, fontWeight: '700', color: 'rgba(255,255,255,0.4)', letterSpacing: 1, marginBottom: 2 },
  speedValue: { fontSize: 42, fontWeight: '800', color: '#F1F5F9', lineHeight: 46 },
  speedUnit:  { fontSize: 14, fontWeight: '600', color: 'rgba(255,255,255,0.5)', marginBottom: 6 },
  recRow:     { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  recText:    { fontSize: 11, color: theme.colors.success, fontWeight: '600' },

  actionBtn: {
    flex: 1, paddingVertical: 16, borderRadius: 14,
    alignItems: 'center', justifyContent: 'center',
  },
  actionBtnText: { color: 'white', fontSize: 14, fontWeight: '800', letterSpacing: 1.2 },

  permWrap: { flex: 1, backgroundColor: theme.colors.bg, alignItems: 'center', justifyContent: 'center', padding: 24 },
  permCard: {
    backgroundColor: theme.colors.surface, borderRadius: 16,
    borderWidth: 1, borderColor: theme.colors.border,
    padding: 28, alignItems: 'center', maxWidth: 320,
  },
  permTitle: { fontSize: 18, fontWeight: '700', color: theme.colors.text.primary, marginBottom: 10 },
  permDesc:  { fontSize: 13, color: theme.colors.text.muted, textAlign: 'center', lineHeight: 20, marginBottom: 24 },
  permBtn:   { backgroundColor: theme.colors.primary, paddingHorizontal: 24, paddingVertical: 12, borderRadius: 10 },
  permBtnText: { color: 'white', fontWeight: '700', fontSize: 14 },
});
