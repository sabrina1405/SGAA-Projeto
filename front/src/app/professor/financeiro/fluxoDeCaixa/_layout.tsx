import { Ionicons } from '@expo/vector-icons';
import { Stack, useRouter } from 'expo-router';
import { Pressable } from 'react-native';

import { palette } from '@/constants/palette';

// Stack da tela Fluxo de Caixa. Fica em app/professor/financeiro/fluxoDeCaixa/_layout.tsx.
export default function FluxoDeCaixaLayout() {
  const router = useRouter();

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
          // Esta é a primeira tela deste Stack, então a seta de voltar não vem sozinha.
          headerLeft: () => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Voltar"
              hitSlop={8}
              onPress={() => router.back()}
              style={{ marginRight: 16 }}
            >
              <Ionicons name="chevron-back" size={24} color="#ffffff" />
            </Pressable>
          ),
        }}
      />
    </Stack>
  );
}