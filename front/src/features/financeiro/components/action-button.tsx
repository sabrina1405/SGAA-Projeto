import { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';

import { palette } from '@/constants/palette';

type Props = {
  rotulo: string;
  icone: ComponentProps<typeof Ionicons>['name'];
  acessibilidade?: string;
  onPress?: () => void;
};

// Botão roxo de ação (Imprimir, Novo Item...). Ocupa o espaço que sobrar na linha.
export function ActionButton({ rotulo, icone, acessibilidade, onPress }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={acessibilidade ?? rotulo}
      onPress={onPress}
      style={({ pressed }) => [styles.botao, pressed && styles.pressionado]}
    >
      <Text style={styles.texto}>{rotulo}</Text>
      <Ionicons name={icone} size={18} color="#fff" />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  botao: {
    flex: 1,
    height: 38,
    borderRadius: 8,
    backgroundColor: palette.button,
    paddingHorizontal: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  texto: { color: '#fff', fontSize: 11 },
  pressionado: { opacity: 0.8 },
});