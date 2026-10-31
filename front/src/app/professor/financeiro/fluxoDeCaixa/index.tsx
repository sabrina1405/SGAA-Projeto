import { Ionicons } from '@expo/vector-icons';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import { CashFlowChart } from '@/features/financeiro/components/cash-flow-chart';
import { FilterButton } from '@/features/financeiro/components/filter-button';
import { LancamentoRow, LancamentosHeader } from '@/features/financeiro/components/lancamento-row';
import { FLUXO_CAIXA_MOCK } from '@/features/financeiro/fluxo-mock';
import { LANCAMENTOS_MOCK } from '@/features/financeiro/mock';

function Separador() {
  return <View style={styles.separador} />;
}

// Título e seta de voltar ficam no _layout.tsx desta pasta.
export default function FluxoDeCaixaScreen() {
  const lancamentos = LANCAMENTOS_MOCK;

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.conteudo}
      data={lancamentos}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => <LancamentoRow item={item} />}
      ItemSeparatorComponent={Separador}
      ListEmptyComponent={<Text style={styles.vazio}>Nenhum lançamento encontrado.</Text>}
      ListHeaderComponent={
        <View>
          <View style={styles.filtros}>
            {/* onPress dos filtros: ligar quando os seletores existirem */}
            <FilterButton rotulo="Filtrar por Mês" texto="Mês" icone="calendar-outline" />
            <FilterButton rotulo="Filtrar por Status" texto="Status" icone="filter-outline" />
            <FilterButton rotulo="Filtrar por Aluno" texto="Aluno" icone="people-outline" />
            <FilterButton rotulo="Filtrar por Tipo" texto="Tipo" icone="swap-horizontal-outline" />
          </View>

          <CashFlowChart dados={FLUXO_CAIXA_MOCK} />

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Imprimir relatório"
            // TODO: gerar o PDF com expo-print quando o relatório estiver pronto
            onPress={() => {}}
            style={({ pressed }) => [styles.imprimir, pressed && styles.pressionado]}
          >
            <Text style={styles.imprimirTexto}>Imprimir</Text>
            <Ionicons name="print-outline" size={20} color="#fff" />
          </Pressable>

          <LancamentosHeader />
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 32 },
  filtros: { flexDirection: 'row', alignItems: 'flex-end', gap: 8, marginBottom: 16 },
  imprimir: {
    alignSelf: 'center',
    height: 38,
    minWidth: 112,
    borderRadius: 8,
    backgroundColor: palette.button,
    paddingHorizontal: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  imprimirTexto: { color: '#fff', fontSize: 11 },
  pressionado: { opacity: 0.8 },
  separador: { height: StyleSheet.hairlineWidth, backgroundColor: palette.line },
  vazio: { textAlign: 'center', color: palette.textMuted, marginTop: 24 },
});