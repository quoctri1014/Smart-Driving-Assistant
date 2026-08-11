import { Tabs } from 'expo-router';

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: 'blue' }}>
      <Tabs.Screen
        name="live"
        options={{
          title: 'Live AI',
          headerShown: false,
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'Lịch sử',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Cá nhân',
        }}
      />
    </Tabs>
  );
}
