import { StyleSheet, Text, View } from 'react-native';

import { formatarMoeda } from '../utils';

interface Props {
  titulo: string;
  valor: number;
  fundo: string;
  corValor: string;
}

export function SummaryCard({ titulo, valor, fundo, corValor }: Props) {
  return (
    <View style={[styles.card, { backgroundColor: fundo }]}>
      <Text style={styles.titulo}>{titulo}</Text>
      <Text style={[styles.valor, { color: corValor }]}>{formatarMoeda(valor)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: 14,
    padding: 14,
    gap: 8,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 4,
  },
  titulo: { fontSize: 13, color: '#222' },
  valor: { fontSize: 20, fontWeight: '800' },
});
