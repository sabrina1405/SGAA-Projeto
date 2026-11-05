import { Ionicons } from '@expo/vector-icons';
import { Pressable } from 'react-native';

import { useMenu } from '../menu-context';

// Botão hambúrguer para o header.
export function MenuButton() {
  const { abrir } = useMenu();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Abrir menu"
      onPress={abrir}
      hitSlop={10}
    >
      <Ionicons name="menu" size={28} color="#fff" />
    </Pressable>
  );
}