import { StyleSheet, Text, View } from 'react-native';

import type { Evento, StatusEvento } from '../types';

// Cores da barra lateral por status (iguais às do protótipo).
const COR_STATUS: Record<StatusEvento, string> = {
  confirmada: '#2E7D32',
  pendente: '#F5A623',
  reposicao: '#B65FBF',
};

export function EventChip({ evento }: { evento: Evento }) {
  return (
    <View style={styles.chip}>
      <View style={[styles.barra, { backgroundColor: COR_STATUS[evento.status] }]} />
      <View style={styles.textos}>
        <Text style={styles.aluno} numberOfLines={1}>{evento.aluno}</Text>
        <Text style={styles.hora} numberOfLines={1}>{evento.inicio} às {evento.fim}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: { flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 3 },
  barra: { width: 3, alignSelf: 'stretch', borderRadius: 2 },
  textos: { flex: 1 },
  aluno: { fontSize: 6, fontWeight: '700', color: '#000' },
  hora: { fontSize: 5, color: '#555' },
});