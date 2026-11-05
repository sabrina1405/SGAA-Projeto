import { Pressable, StyleSheet, Text } from 'react-native';

import { palette } from '@/constants/palette';

type Props = {
  rotulo: string;
  ativo?: boolean;
  onPress: () => void;
};

// Botão "Mês / Semana / Dia": o ativo fica mais escuro.
export function ViewToggle({ rotulo, ativo = false, onPress }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: ativo }}
      onPress={onPress}
      style={({ pressed }) => [styles.botao, ativo && styles.ativo, pressed && styles.pressionado]}
    >
      <Text style={styles.texto}>{rotulo}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  botao: {
    flex: 1,
    height: 32,
    borderRadius: 8,
    backgroundColor: palette.button,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ativo: { backgroundColor: palette.primary },
  pressionado: { opacity: 0.8 },
  texto: { color: '#fff', fontSize: 10 },
});