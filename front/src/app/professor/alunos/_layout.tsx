import { Ionicons } from '@expo/vector-icons';
import { Stack, useRouter } from 'expo-router';
import { Pressable } from 'react-native';
import { headerComMenu } from '@/features/menu/header-options';

import { palette } from '@/constants/palette';

export default function InformacoesAlunoLayout() {
  const router = useRouter();

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: palette.header },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '600' },
        ...headerComMenu,
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: 'Informações do Aluno',
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