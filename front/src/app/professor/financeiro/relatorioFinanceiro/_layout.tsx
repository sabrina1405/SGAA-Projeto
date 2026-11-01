import { Stack } from 'expo-router';

import { palette } from '@/constants/palette';
import { HeaderBackButton } from '@/features/financeiro/components/header-back-button';


export default function FluxoDeCaixaLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: palette.header },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: 'Relatório - Fluxo de Caixa',
          headerLeft: () => <HeaderBackButton />,
        }}
      />
    </Stack>
  );
}