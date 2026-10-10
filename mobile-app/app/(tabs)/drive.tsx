import { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';

export default function DriveTabRedirect() {
  useEffect(() => {
    router.replace('/drive');
  }, []);

  return (
    <View style={{ flex: 1, backgroundColor: '#0B0F17', justifyContent: 'center', alignItems: 'center' }}>
      <ActivityIndicator size="large" color="#3B82F6" />
    </View>
  );
}
