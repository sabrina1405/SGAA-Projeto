import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Pressable } from 'react-native';




export function HeaderBackButton() {
  const router = useRouter();

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Voltar"
      hitSlop={8}
      onPress={() => router.back()}
      style={{ marginRight: 16 }}
    >
      <Ionicons name="chevron-back" size={24} color="#ffffff" />
    </Pressable>
  );
}