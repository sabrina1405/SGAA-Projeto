import { StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import { STATUS_INFO } from '../status';
import type { Evento } from '../types';

export function AgendaItem({ evento }: { evento: Evento }) {
  const { cor, rotulo } = STATUS_INFO[evento.status];

  return (
    <View style={styles.linha}>
      <View style={styles.horario}>
        <Text style={styles.inicio}>{evento.inicio}</Text>
        <Text style={styles.fim}>{evento.fim}</Text>
      </View>
      <View style={[styles.barra, { backgroundColor: cor }]} />
      <View style={styles.info}>
        <Text style={styles.aluno} numberOfLines={1}>{evento.aluno}</Text>
        <Text style={[styles.status, { color: cor }]}>{rotulo}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  linha: { flexDirection: 'row', alignItems: 'stretch', gap: 12, paddingVertical: 10 },
  horario: { width: 44, alignItems: 'flex-end' },
  inicio: { fontSize: 15, fontWeight: '600', color: palette.title },
  fim: { fontSize: 12, color: palette.textMuted, marginTop: 2 },
  barra: { width: 4, borderRadius: 2 },
  info: { flex: 1, justifyContent: 'center' },
  aluno: { fontSize: 16, color: palette.title },
  status: { fontSize: 13, marginTop: 2 },
});