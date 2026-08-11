import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { theme } from '../lib/theme';
import { CheckCircle, Clock, Navigation2 } from 'lucide-react-native';

export default function TripSummary() {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <CheckCircle size={64} color={theme.colors.success} />
        <Text style={styles.title}>Trip Completed</Text>
        <Text style={styles.subtitle}>LOCAL SESSION SUMMARY</Text>
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <View style={styles.iconBox}>
            <Clock size={24} color={theme.colors.text.primary} />
          </View>
          <View>
            <Text style={styles.label}>Duration</Text>
            <Text style={styles.value}>Just now (Demo)</Text>
          </View>
        </View>

        <View style={styles.divider} />

        <View style={styles.row}>
          <View style={styles.iconBox}>
            <Navigation2 size={24} color={theme.colors.text.primary} />
          </View>
          <View>
            <Text style={styles.label}>Distance</Text>
            <Text style={styles.value}>N/A</Text>
          </View>
        </View>
      </View>

      <TouchableOpacity 
        style={styles.button}
        onPress={() => router.replace('/')}
      >
        <Text style={styles.buttonText}>RETURN TO HOME</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.bg,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    color: theme.colors.text.primary,
    fontSize: 28,
    fontWeight: 'bold',
    marginTop: 16,
  },
  subtitle: {
    color: theme.colors.text.muted,
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
    letterSpacing: 1,
  },
  card: {
    backgroundColor: theme.colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 40,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: theme.colors.border,
    marginVertical: 16,
  },
  iconBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: theme.colors.elevated,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  label: {
    color: theme.colors.text.secondary,
    fontSize: 14,
  },
  value: {
    color: theme.colors.text.primary,
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 2,
  },
  button: {
    backgroundColor: theme.colors.primary,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  }
});
