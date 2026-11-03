import { FlatList, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import { ActionButton } from '@/features/financeiro/components/action-button';
import { FilterButton } from '@/features/financeiro/components/filter-button';
import { LineChart, type SerieLinha } from '@/features/financeiro/components/line-chart';
import { RelatorioHeader, RelatorioRow } from '@/features/financeiro/components/relatorio-row';
import { RELATORIO_LINHAS_MOCK, RELATORIO_MENSAL_MOCK } from '@/features/financeiro/relatorio-mock';

const SERIES: SerieLinha[] = [
  { nome: 'Entradas', valores: RELATORIO_MENSAL_MOCK.entradas, cor: '#4f9d5d' },
  { nome: 'Saídas', valores: RELATORIO_MENSAL_MOCK.saidas, cor: '#e0453c' },
];

const REFERENCIA = { valor: RELATORIO_MENSAL_MOCK.referencia, cor: '#f5b800' };

function Separador() {
  return <View style={styles.separador} />;
}




export default function RelatorioFinanceiroScreen() {
  const linhas = RELATORIO_LINHAS_MOCK;

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.conteudo}
      data={linhas}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => <RelatorioRow item={item} />}
      ItemSeparatorComponent={Separador}
      ListEmptyComponent={<Text style={styles.vazio}>Nenhum dado encontrado.</Text>}
      ListHeaderComponent={
        <View>
          <View style={styles.filtros}>
            {/* onPress dos filtros: ligar quando os seletores existirem */}
            <FilterButton rotulo="Filtrar por Ano" texto="Ano" icone="calendar-outline" />
            <FilterButton rotulo="Filtrar por Mês" texto="Mês" icone="calendar-outline" />
            <FilterButton rotulo="Filtrar por Tipo" texto="Tipo" icone="swap-horizontal-outline" />
            {/* TODO: gerar o PDF com expo-print quando o relatório estiver pronto */}
            <ActionButton rotulo="Imprimir" icone="print-outline" acessibilidade="Imprimir relatório" />
          </View>

          <LineChart rotulos={RELATORIO_MENSAL_MOCK.rotulos} series={SERIES} referencia={REFERENCIA} />

          <RelatorioHeader />
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 32 },
  filtros: { flexDirection: 'row', alignItems: 'flex-end', gap: 8, marginBottom: 24 },
  separador: { height: StyleSheet.hairlineWidth, backgroundColor: palette.line },
  vazio: { textAlign: 'center', color: palette.textMuted, marginTop: 24 },
});