import { Ionicons } from '@expo/vector-icons';
import { Stack, useRouter } from 'expo-router';
import { Pressable } from 'react-native';

import { palette } from '@/constants/palette';

export default function AlunosLayout() {
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
          title: 'Alunos',
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
          headerRight: () => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Menu"
              onPress={() => {}}
              style={{ marginLeft: 16 }}
            >
              <Ionicons name="menu" size={24} color="#ffffff" />
            </Pressable>
          ),
        }}
      />
    </Stack>
  );
}