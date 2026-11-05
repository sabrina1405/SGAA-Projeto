import { StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import type { StatusPagamento } from '../types';

const ROTULOS: Record<StatusPagamento, string> = {
  pago: 'Pago',
  pendente: 'Pendente',
  vencido: 'Vencido',
};

export function StatusBadge({ status }: { status: StatusPagamento }) {
  const cor = palette.status[status];
  return (
    <View style={[styles.badge, { backgroundColor: cor.fundo, borderColor: cor.borda }]}>
      <Text style={[styles.texto, { color: cor.texto }]}>{ROTULOS[status]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 2,
    paddingHorizontal: 8,
    alignSelf: 'center',
  },
  texto: { fontSize: 10, fontWeight: '700' },
});
