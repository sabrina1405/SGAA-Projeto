import { Stack } from 'expo-router';

import { palette } from '@/constants/palette';

// Stack da aba Financeiro. Fica em app/professor/financeiro/_layout.tsx.
// As outras telas do módulo entram aqui como novos <Stack.Screen />.
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