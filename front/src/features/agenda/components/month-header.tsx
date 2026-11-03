import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';

type Props = {
  mes: string;
  ano: number;
  onAnterior: () => void;
  onProximo: () => void;
};

function Seta({ nome, rotulo, onPress }: { nome: 'chevron-back' | 'chevron-forward'; rotulo: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={rotulo}
      onPress={onPress}
      hitSlop={10}
      style={({ pressed }) => [styles.seta, pressed && styles.pressionado]}
    >
      <Ionicons name={nome} size={20} color={palette.title} />
    </Pressable>
  );
}

export function MonthHeader({ mes, ano, onAnterior, onProximo }: Props) {
  return (
    <View style={styles.linha}>
      <Text style={styles.titulo}>
        {mes} <Text style={styles.ano}>{ano}</Text>
      </Text>
      <View style={styles.setas}>
        <Seta nome="chevron-back" rotulo="Mês anterior" onPress={onAnterior} />
        <Seta nome="chevron-forward" rotulo="Próximo mês" onPress={onProximo} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  linha: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  titulo: { fontSize: 22, fontWeight: '700', color: palette.title },
  ano: { fontWeight: '400', color: palette.textMuted },
  setas: { flexDirection: 'row', gap: 8 },
  seta: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F2F2F4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressionado: { opacity: 0.6 },
});