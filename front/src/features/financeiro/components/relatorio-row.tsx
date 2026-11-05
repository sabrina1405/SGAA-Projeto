import { StyleSheet, Text, View } from 'react-native';

export type SituacaoLucro = 'negativo' | 'previsto' | 'realizado';

export type RelatorioLinha = {
  id: string;
  ano: string;
  mes: string;
  entradas: number | null; // null enquanto o período ainda não tem valores
  saidas: number | null;
  lucro: number;
  situacao: SituacaoLucro;
};


const COLUNAS = { ano: 1, mes: 1.2, entradas: 1.4, saidas: 1.4, lucro: 1.6 };

const COR_ENTRADA = '#2e7d32';
const COR_SAIDA = '#d32f2f';
const COR_PREVISTO = '#e0a800';

const BADGE = {
  negativo: { fundo: '#f8a8a8', borda: '#d64545' },
  previsto: { fundo: '#ffd978', borda: '#e0a800' },
  realizado: { fundo: '#b9dcc0', borda: '#3f9a55' },
} as const;

function formatarMoeda(valor: number) {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function RelatorioHeader() {
  return (
    <View style={styles.linha}>
      {(
        [
          ['Ano', COLUNAS.ano],
          ['Mês', COLUNAS.mes],
          ['Entradas', COLUNAS.entradas],
          ['Saídas', COLUNAS.saidas],
          ['Lucro', COLUNAS.lucro],
        ] as const
      ).map(([titulo, flex]) => (
        <View key={titulo} style={[styles.cabecalho, { flex }]}>
          <Text style={styles.cabecalhoTexto}>{titulo}</Text>
        </View>
      ))}
    </View>
  );
}

export function RelatorioRow({ item }: { item: RelatorioLinha }) {
  const badge = BADGE[item.situacao];

  return (
    <View style={[styles.linha, styles.linhaDados]}>
      <Text style={[styles.celula, { flex: COLUNAS.ano }]}>{item.ano}</Text>
      <Text style={[styles.celula, { flex: COLUNAS.mes }]}>{item.mes}</Text>
      <Text
        style={[
          styles.celula,
          { flex: COLUNAS.entradas, color: item.entradas === null ? COR_PREVISTO : COR_ENTRADA },
        ]}
      >
        {item.entradas === null ? '-----' : formatarMoeda(item.entradas)}
      </Text>
      <Text
        style={[
          styles.celula,
          { flex: COLUNAS.saidas, color: item.saidas === null ? COR_PREVISTO : COR_SAIDA },
        ]}
      >
        {item.saidas === null ? '-----' : formatarMoeda(item.saidas)}
      </Text>
      <View style={[styles.celulaBadge, { flex: COLUNAS.lucro }]}>
        <View style={[styles.badge, { backgroundColor: badge.fundo, borderColor: badge.borda }]}>
          <Text style={styles.badgeTexto}>{formatarMoeda(item.lucro)}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  linha: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  linhaDados: { paddingVertical: 14 },
  cabecalho: {
    height: 30,
    borderRadius: 6,
    backgroundColor: '#ebebeb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cabecalhoTexto: { fontSize: 10, fontWeight: '700', color: '#000' },
  celula: { fontSize: 10, fontWeight: '700', color: '#000', textAlign: 'center' },
  celulaBadge: { alignItems: 'center' },
  badge: {
    minWidth: 62,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  badgeTexto: { fontSize: 10, fontWeight: '700', color: '#222' },
});