import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

import { palette } from '@/constants/palette';
import { STATUS_INFO } from '../status';
import type { FiltroStatus } from '../types';

const OPCOES: { valor: FiltroStatus; rotulo: string }[] = [
  { valor: 'todos', rotulo: 'Todos' },
  { valor: 'confirmada', rotulo: STATUS_INFO.confirmada.rotulo },
  { valor: 'pendente', rotulo: STATUS_INFO.pendente.rotulo },
  { valor: 'reposicao', rotulo: STATUS_INFO.reposicao.rotulo },
];

type Props = {
  valor: FiltroStatus;
  onChange: (valor: FiltroStatus) => void;
};

export function StatusFilter({ valor, onChange }: Props) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.linha}>
      {OPCOES.map((o) => {
        const ativo = o.valor === valor;
        return (
          <Pressable
            key={o.valor}
            accessibilityRole="button"
            accessibilityState={{ selected: ativo }}
            onPress={() => onChange(o.valor)}
            style={[styles.chip, ativo && styles.chipAtivo]}
          >
            <Text style={[styles.texto, ativo && styles.textoAtivo]}>{o.rotulo}</Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  linha: { gap: 8 },
  chip: {
    paddingHorizontal: 14,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#F2F2F4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipAtivo: { backgroundColor: palette.primary },
  texto: { fontSize: 13, color: palette.title },
  textoAtivo: { color: '#fff', fontWeight: '600' },
});