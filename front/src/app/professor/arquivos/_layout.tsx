import { Stack } from 'expo-router';
import { palette } from '@/constants/palette';
import { headerComMenu } from '@/features/menu/header-options';

export default function ArquivosLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: palette.header },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '600' },
        ...headerComMenu,
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Materiais e Arquivos' }} />
      <Stack.Screen name="novo" options={{ title: 'Enviar Novo Arquivo' }} />
    </Stack>
  );
}