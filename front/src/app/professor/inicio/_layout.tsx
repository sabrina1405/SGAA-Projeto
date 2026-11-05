import { Ionicons } from '@expo/vector-icons';
import { Stack } from 'expo-router';
import { Pressable } from 'react-native';
import { headerComMenu } from '@/features/menu/header-options';

import { palette } from '@/constants/palette';

export default function InicioLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: palette.header },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '600' },
        headerShadowVisible: false,
        ...headerComMenu,
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Início' }} />
    </Stack>
  );
}