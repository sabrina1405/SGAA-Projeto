import type { ComponentProps } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { palette } from '@/constants/palette';

interface Props {
  rotulo: string;
  texto: string;
  icone: ComponentProps<typeof Ionicons>['name'];
  onPress?: () => void;
}

export function FilterButton({ rotulo, texto, icone, onPress }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.rotulo} numberOfLines={1}>{rotulo}</Text>
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        accessibilityLabel={rotulo}
        style={({ pressed }) => [styles.botao, pressed && styles.pressionado]}
      >
        <Text style={styles.texto}>{texto}</Text>
        <Ionicons name={icone} size={18} color="#fff" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, gap: 4 },
  rotulo: { fontSize: 9, color: palette.textMuted },
  botao: {
    height: 38,
    borderRadius: 8,
    backgroundColor: palette.button,
    paddingHorizontal: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  pressionado: { opacity: 0.8 },
  texto: { color: '#fff', fontSize: 11 },
});
