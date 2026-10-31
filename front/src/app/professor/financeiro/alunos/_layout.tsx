import { Stack } from 'expo-router';

import { palette } from '@/constants/palette';


export default function FinanceiroLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: palette.header },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Financeiro' }} />
    </Stack>
  );
}