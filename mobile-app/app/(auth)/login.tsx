import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  StatusBar,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { router } from 'expo-router';
import { Shield, Sparkles, Lock, Mail, ArrowRight, CheckCircle2 } from 'lucide-react-native';
import { setToken } from '../../lib/auth';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://192.168.1.100:8000/api/v1';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Thông báo', 'Vui lòng nhập đầy đủ Email và Mật khẩu');
      return;
    }

    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!res.ok) {
        throw new Error('Đăng nhập thất bại. Kiểm tra tài khoản doanh nghiệp.');
      }

      const data = await res.json();
      await setToken(data.access_token);
      router.replace('/(tabs)');
    } catch (err: any) {
      Alert.alert('Không thể đăng nhập', err.message || 'Kiểm tra kết nối máy chủ.');
    } finally {
      setLoading(false);
    }
  };


  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar barStyle="light-content" backgroundColor="#0B0F17" />
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Logo & Header */}
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <Shield size={32} color="#3B82F6" />
          </View>
          <Text style={styles.title}>Smart Traffic AI</Text>
          <Text style={styles.subtitle}>Hệ thống trợ lý & giám sát lái xe an toàn</Text>
        </View>

        {/* Feature Highlights */}
        <View style={styles.featuresCard}>
          <View style={styles.featureRow}>
            <CheckCircle2 size={14} color="#10B981" />
            <Text style={styles.featureText}>12 Module AI giám sát hành trình thời gian thực</Text>
          </View>
          <View style={styles.featureRow}>
            <CheckCircle2 size={14} color="#10B981" />
            <Text style={styles.featureText}>Cảnh báo va chạm, buồn ngủ & khoảng cách an toàn</Text>
          </View>
        </View>

        {/* Form */}
        <View style={styles.formCard}>
          <Text style={styles.formTitle}>Đăng nhập tài xế</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email hoặc Tên đăng nhập</Text>
            <View style={styles.inputWrapper}>
              <Mail size={18} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="driver1@example.com"
                placeholderTextColor="#4B5563"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
              />
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Mật khẩu</Text>
            <View style={styles.inputWrapper}>
              <Lock size={18} color="#6B7280" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor="#4B5563"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
            </View>
          </View>

          {/* Login Button */}
          <TouchableOpacity
            style={[styles.primaryButton, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.85}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <View style={styles.buttonContent}>
                <Text style={styles.primaryButtonText}>Đăng nhập</Text>
                <ArrowRight size={18} color="#FFFFFF" />
              </View>
            )}
          </TouchableOpacity>

        </View>

        <Text style={styles.footerText}>
          Phiên bản 2.0 • Hỗ trợ kết nối AI Engine & Camera HUD
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0B0F17',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
    paddingVertical: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor: 'rgba(59,130,246,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(59,130,246,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 14,
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: '#F9FAFB',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 4,
    textAlign: 'center',
  },
  featuresCard: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 12,
    gap: 8,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  featureText: {
    fontSize: 12,
    color: '#D1D5DB',
  },
  formCard: {
    backgroundColor: '#111827',
    borderRadius: 18,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 8,
  },
  formTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F3F4F6',
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: '#9CA3AF',
    marginBottom: 6,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1F2937',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    paddingHorizontal: 12,
  },
  inputIcon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    height: 46,
    color: '#F9FAFB',
    fontSize: 14,
  },
  primaryButton: {
    backgroundColor: '#2563EB',
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 6,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  demoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'rgba(59,130,246,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(59,130,246,0.25)',
    height: 44,
    borderRadius: 12,
    marginTop: 12,
  },
  demoButtonText: {
    color: '#60A5FA',
    fontSize: 13,
    fontWeight: '600',
  },
  footerText: {
    textAlign: 'center',
    fontSize: 11,
    color: '#6B7280',
    marginTop: 24,
  },
});
