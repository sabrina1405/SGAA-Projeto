import { Stack } from 'expo-router';

export default function AlunoLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="home" />
      <Stack.Screen name="agenda" />
      <Stack.Screen name="atividades" />
      <Stack.Screen name="financeiro" />
      <Stack.Screen name="perfil" />
      <Stack.Screen name="arquivos" />
      <Stack.Screen name="recados" />
    </Stack>
  );
}
