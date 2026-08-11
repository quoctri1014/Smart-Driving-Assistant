import React, { useState, useEffect, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { router } from 'expo-router';
import { theme } from '../lib/theme';
import { ShieldAlert, LogOut, Info } from 'lucide-react-native';
import { useDrivingSocket } from '../lib/useDrivingSocket';
import { deriveDrivingUIState } from '../lib/driving/alert-engine';

type DriveSessionState = 'IDLE' | 'PREPARING' | 'CONNECTING' | 'STREAMING' | 'STOPPING' | 'ENDED' | 'ERROR';

export default function DriveMode() {
  const [permission, requestPermission] = useCameraPermissions();
  const [sessionState, setSessionState] = useState<DriveSessionState>('IDLE');
  
  // Phase H - Simulated speed for demo
  const [simulatedSpeed, setSimulatedSpeed] = useState(55);

  const cameraRef = useRef<CameraView>(null);
  const isProcessingFrame = useRef(false);
  const captureIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionStartTime = useRef<number | null>(null);
  
  // State from socket
  const { status: socketStatus, result: roadResult, isStale, connect, disconnect, sendFrame, sendMetadata } = useDrivingSocket();

  // Derive UI state based on web-app's alert engine (Phase K)
  // For Mobile, driver DMS is NOT SUPPORTED ON SINGLE PHONE (Phase L) -> pass null and driverStale=true
  const uiState = deriveDrivingUIState(roadResult, null, isStale, true);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>Camera permission required.</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Handle capture loop (Phase D)
  const startCaptureLoop = useCallback(() => {
    // 2 FPS for prototype -> 500ms
    captureIntervalRef.current = setInterval(async () => {
      if (isProcessingFrame.current || !cameraRef.current) return;
      isProcessingFrame.current = true;
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.5,
          base64: true,
          // Low res if supported, wait Expo Camera doesn't let us define width/height in takePictureAsync directly 
          // in modern sdk, but quality 0.5 reduces size.
        });
        if (photo?.base64) {
          await sendFrame(photo.base64);
          sendMetadata({ vehicle_speed: simulatedSpeed });
        }
      } catch (err) {
        console.error("Frame capture failed:", err);
      } finally {
        isProcessingFrame.current = false;
      }
    }, 500); // Low FPS prototype
  }, [sendFrame, sendMetadata, simulatedSpeed]);

  const stopCaptureLoop = useCallback(() => {
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }
  }, []);

  // Sync WS status -> Session State
  useEffect(() => {
    if (sessionState === 'CONNECTING' && socketStatus === 'CONNECTED') {
      setSessionState('STREAMING');
      startCaptureLoop();
    }
    if (socketStatus === 'ERROR' || socketStatus === 'DISCONNECTED') {
      if (sessionState === 'STREAMING') {
        stopCaptureLoop();
        setSessionState('ERROR');
      }
    }
  }, [socketStatus, sessionState, startCaptureLoop, stopCaptureLoop]);

  const handleStartDrive = () => {
    setSessionState('CONNECTING');
    sessionStartTime.current = Date.now();
    connect();
  };

  const handleEndDrive = () => {
    setSessionState('STOPPING');
    stopCaptureLoop();
    disconnect();
    setSessionState('ENDED');
    // Navigate to Trip Summary (Phase M)
    router.replace('/trip-summary' as any);
  };

  const isDanger = uiState.priority === 'COLLISION_DANGER';

  return (
    <View style={styles.container}>
      <CameraView 
        ref={cameraRef}
        style={styles.camera} 
        facing="back"
      >
        {/* Full screen takeover for danger (Phase T) */}
        {isDanger && (
          <View style={[styles.dangerOverlay]}>
            <ShieldAlert size={80} color="white" />
            <Text style={styles.dangerText}>{uiState.message}</Text>
            <Text style={styles.dangerSubText}>BRAKE NOW!</Text>
          </View>
        )}

        <View style={styles.uiContainer}>
          {/* Top Bar */}
          <View style={styles.topBar}>
            <TouchableOpacity 
              style={styles.backButton}
              onPress={() => {
                stopCaptureLoop();
                disconnect();
                router.back();
              }}
            >
              <LogOut size={24} color={theme.colors.text.primary} />
            </TouchableOpacity>

            <View style={[
              styles.statusBadge, 
              { backgroundColor: sessionState === 'STREAMING' ? theme.colors.success + '40' : theme.colors.surface }
            ]}>
              <View style={[
                styles.statusDot, 
                { backgroundColor: sessionState === 'STREAMING' ? theme.colors.success : theme.colors.text.muted }
              ]} />
              <Text style={styles.statusText}>
                {sessionState === 'STREAMING' ? 'AI ACTIVE' : sessionState}
              </Text>
            </View>
          </View>

          {/* Banner Alert */}
          {uiState.priority === 'UNAVAILABLE' && !isDanger && sessionState === 'STREAMING' && (
             <View style={styles.warningBanner}>
               <Info size={20} color="white" style={{ marginRight: 8 }} />
               <Text style={styles.warningText}>AI Connection Lost / Reconnecting...</Text>
             </View>
          )}

          {uiState.priority !== 'NORMAL' && uiState.priority !== 'UNAVAILABLE' && !isDanger && sessionState === 'STREAMING' && (
            <View style={styles.warningBanner}>
              <Info size={20} color="white" style={{ marginRight: 8 }} />
              <Text style={styles.warningText}>{uiState.message}</Text>
            </View>
          )}

          {/* Bottom HUD */}
          <View style={styles.bottomHud}>
            <View style={styles.hudPanel}>
              <Text style={styles.hudLabel}>SPEED (SIM)</Text>
              <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
                <Text style={styles.speedText}>{simulatedSpeed}</Text>
                <Text style={styles.unitText}> km/h</Text>
              </View>
              {uiState.recommendedSpeed && (
                <Text style={styles.recommendedText}>Rec: {uiState.recommendedSpeed} km/h</Text>
              )}
            </View>

            <TouchableOpacity 
              style={[
                styles.actionButton,
                { backgroundColor: sessionState === 'STREAMING' ? theme.colors.danger : theme.colors.primary }
              ]}
              onPress={sessionState === 'STREAMING' ? handleEndDrive : handleStartDrive}
              disabled={sessionState === 'CONNECTING' || sessionState === 'STOPPING'}
            >
              <Text style={styles.actionButtonText}>
                {sessionState === 'STREAMING' ? 'END TRIP' : (sessionState === 'CONNECTING' ? 'CONNECTING...' : 'START DRIVE')}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: 'black' },
  camera: { flex: 1 },
  uiContainer: {
    flex: 1,
    justifyContent: 'space-between',
    padding: 20,
    paddingTop: 60, // Safe area approx
  },
  dangerOverlay: {
    ...StyleSheet.absoluteFill as any,
    backgroundColor: 'rgba(239, 68, 68, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  dangerText: {
    color: 'white',
    fontSize: 32,
    fontWeight: '900',
    marginTop: 20,
    textAlign: 'center',
    textShadowColor: 'rgba(0,0,0,0.5)',
    textShadowOffset: { width: 0, height: 4 },
    textShadowRadius: 10,
  },
  dangerSubText: { color: 'white', fontSize: 24, fontWeight: 'bold' },
  topBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', zIndex: 20 },
  backButton: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: 'rgba(30, 41, 59, 0.8)',
    justifyContent: 'center', alignItems: 'center',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  statusBadge: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 16, borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  statusDot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  statusText: { color: 'white', fontSize: 12, fontWeight: 'bold' },
  warningBanner: {
    flexDirection: 'row', backgroundColor: 'rgba(245, 158, 11, 0.9)',
    padding: 16, borderRadius: 12, alignItems: 'center', alignSelf: 'center',
    marginTop: 20, zIndex: 20,
  },
  warningText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
  bottomHud: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', zIndex: 20 },
  hudPanel: {
    backgroundColor: 'rgba(15, 23, 42, 0.8)', padding: 16, borderRadius: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  hudLabel: { color: theme.colors.text.muted, fontSize: 12, fontWeight: 'bold', marginBottom: 4 },
  speedText: { color: theme.colors.text.primary, fontSize: 36, fontWeight: '900' },
  unitText: { color: theme.colors.text.secondary, fontSize: 16, fontWeight: '600' },
  recommendedText: { color: theme.colors.success, fontSize: 14, fontWeight: 'bold', marginTop: 4 },
  actionButton: { paddingHorizontal: 24, paddingVertical: 16, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  actionButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  permissionContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.bg, padding: 20 },
  permissionText: { color: theme.colors.text.primary, fontSize: 18, textAlign: 'center', marginBottom: 20 },
  button: { backgroundColor: theme.colors.primary, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 8 },
  buttonText: { color: 'white', fontWeight: 'bold' }
});
