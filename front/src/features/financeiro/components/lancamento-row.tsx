import { StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import type { Lancamento } from '../types';
import { formatarData, formatarMoeda } from '../utils';
import { StatusBadge } from './status-badge';

// Mesmas proporções no cabeçalho e nas linhas, para as colunas alinharem.
const COLUNAS = {
  dataAgendada: 1.1,
  dataPagamento: 1.1,
  aluno: 1.3,
  valor: 0.9,
  status: 1.1,
} as const;

export function LancamentosHeader() {
  return (
    <View style={styles.linha}>
      <Text style={[styles.cabecalho, { flex: COLUNAS.dataAgendada }]}>Data Agendada</Text>
      <Text style={[styles.cabecalho, { flex: COLUNAS.dataPagamento }]}>Data Pagamento</Text>
      <Text style={[styles.cabecalho, { flex: COLUNAS.aluno }]}>Aluno</Text>
      <Text style={[styles.cabecalho, { flex: COLUNAS.valor }]}>Valor</Text>
      <Text style={[styles.cabecalho, { flex: COLUNAS.status }]}>Status</Text>
    </View>
  );
}

export function LancamentoRow({ item }: { item: Lancamento }) {
  return (
    <View style={[styles.linha, styles.linhaDados]}>
      <Text style={[styles.celula, { flex: COLUNAS.dataAgendada }]}>{formatarData(item.dataAgendada)}</Text>
      <Text style={[styles.celula, { flex: COLUNAS.dataPagamento }]}>{formatarData(item.dataPagamento)}</Text>
      <Text style={[styles.celula, { flex: COLUNAS.aluno }]} numberOfLines={2}>{item.alunoNome}</Text>
      <Text style={[styles.celula, { flex: COLUNAS.valor, color: palette.valor[item.status] }]}>
        {formatarMoeda(item.valor)}
      </Text>
      <View style={[styles.celulaStatus, { flex: COLUNAS.status }]}>
        <StatusBadge status={item.status} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  linha: { flexDirection: 'row', alignItems: 'center' },
  linhaDados: { paddingVertical: 14 },
  cabecalho: {
    marginHorizontal: 2,
    paddingVertical: 8,
    borderRadius: 6,
    backgroundColor: palette.cellBg,
    textAlign: 'center',
    fontSize: 10,
    fontWeight: '700',
  },
  celula: {
    marginHorizontal: 2,
    textAlign: 'center',
    fontSize: 10,
    fontWeight: '700',
    color: '#111',
  },
  celulaStatus: { marginHorizontal: 2, alignItems: 'center' },
});
