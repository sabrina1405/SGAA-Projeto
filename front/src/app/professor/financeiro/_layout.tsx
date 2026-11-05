import { Stack } from 'expo-router';
import { palette } from '@/constants/palette';
import { headerComMenu } from '@/features/menu/header-options';

export default function FinanceiroLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: palette.header },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '600' },
         ...headerComMenu,
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Financeiro' }} />
      {/* Rotas das telas secundárias com botão de voltar nativo */}
      <Stack.Screen 
        name="fluxo-de-caixa" 
        options={{ title: 'Fluxo de Caixa' }} 
      />
      <Stack.Screen 
        name="relatorio-financeiro" 
        options={{ title: 'Relatório Financeiro' }} 
      />
    </Stack>
  );
}