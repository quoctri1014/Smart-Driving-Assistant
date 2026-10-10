import { Tabs } from 'expo-router';
import { LayoutDashboard, Clock, User, Car } from 'lucide-react-native';
import { theme } from '../../lib/theme';
import { View } from 'react-native';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#111827',
          borderTopWidth: 1,
          borderTopColor: 'rgba(255,255,255,0.07)',
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.text.muted,
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '600',
          marginTop: 2,
        },
        tabBarIconStyle: {
          marginTop: 2,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Tổng quan',
          tabBarIcon: ({ color, focused }) => (
            <View style={{
              width: 28, height: 28,
              borderRadius: 8,
              backgroundColor: focused ? theme.colors.primaryBg : 'transparent',
              alignItems: 'center', justifyContent: 'center',
            }}>
              <LayoutDashboard size={17} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="drive"
        options={{
          title: 'Lái xe',
          tabBarIcon: ({ color, focused }) => (
            <View style={{
              width: 44, height: 30,
              borderRadius: 12,
              backgroundColor: focused ? theme.colors.primary : 'rgba(59,127,255,0.15)',
              alignItems: 'center', justifyContent: 'center',
              marginBottom: 2,
            }}>
              <Car size={18} color={focused ? '#fff' : theme.colors.primary} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'Lịch sử',
          tabBarIcon: ({ color, focused }) => (
            <View style={{
              width: 28, height: 28, borderRadius: 8,
              backgroundColor: focused ? theme.colors.primaryBg : 'transparent',
              alignItems: 'center', justifyContent: 'center',
            }}>
              <Clock size={17} color={color} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Tài khoản',
          tabBarIcon: ({ color, focused }) => (
            <View style={{
              width: 28, height: 28, borderRadius: 8,
              backgroundColor: focused ? theme.colors.primaryBg : 'transparent',
              alignItems: 'center', justifyContent: 'center',
            }}>
              <User size={17} color={color} />
            </View>
          ),
        }}
      />
    </Tabs>
  );
}
