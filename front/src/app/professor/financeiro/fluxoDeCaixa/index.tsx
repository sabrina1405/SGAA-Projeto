import { useMemo, useState } from 'react';
import { FlatList, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { palette } from '@/constants/palette';
import { CashFlowChart } from '@/features/financeiro/components/cash-flow-chart';
import { FilterButton } from '@/features/financeiro/components/filter-button';
import { LancamentoRow, LancamentosHeader } from '@/features/financeiro/components/lancamento-row';
import { FLUXO_CAIXA_MOCK } from '@/features/financeiro/fluxo-mock';
import { LANCAMENTOS_MOCK } from '@/features/financeiro/mock';

function Separador() {
  return <View style={styles.separador} />;
}

export default function FluxoDeCaixaScreen() {
  const lancamentos = LANCAMENTOS_MOCK;
  const [periodoSelecionado, setPeriodoSelecionado] = useState<'mes' | 'trimestre' | 'ano'>('mes');

  // Cálculo dos totais de entradas e saídas para os cards superiores
  const totais = useMemo(() => {
    return FLUXO_CAIXA_MOCK.reduce(
      (acc, curr) => ({
        entradas: acc.entradas + (curr.entradas || 0),
        saidas: acc.saidas + (curr.saidas || 0),
      }),
      { entradas: 0, saidas: 0 }
    );
  }, []);

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
        <View style={styles.headerWrapper}>
          {/* 1. Seleção Rápida de Período (Pílulas / Segmented Control) */}
          <View style={styles.segmentedContainer}>
            <Pressable
              style={[styles.segmentBtn, periodoSelecionado === 'mes' && styles.segmentBtnActive]}
              onPress={() => setPeriodoSelecionado('mes')}
            >
              <Text style={[styles.segmentText, periodoSelecionado === 'mes' && styles.segmentTextActive]}>
                Mensal
              </Text>
            </Pressable>
            <Pressable
              style={[styles.segmentBtn, periodoSelecionado === 'trimestre' && styles.segmentBtnActive]}
              onPress={() => setPeriodoSelecionado('trimestre')}
            >
              <Text style={[styles.segmentText, periodoSelecionado === 'trimestre' && styles.segmentTextActive]}>
                Trimestral
              </Text>
            </Pressable>
            <Pressable
              style={[styles.segmentBtn, periodoSelecionado === 'ano' && styles.segmentBtnActive]}
              onPress={() => setPeriodoSelecionado('ano')}
            >
              <Text style={[styles.segmentText, periodoSelecionado === 'ano' && styles.segmentTextActive]}>
                Anual
              </Text>
            </Pressable>
          </View>

          {/* 2. Cards de Métricas Principais (Totais) */}
          <View style={styles.kpiContainer}>
            <View style={[styles.kpiCard, { backgroundColor: '#E8F5E9' }]}>
              <View style={styles.kpiHeader}>
                <Ionicons name="arrow-down-circle" size={18} color="#2E7D32" />
                <Text style={[styles.kpiLabel, { color: '#2E7D32' }]}>Entradas</Text>
              </View>
              <Text style={[styles.kpiValor, { color: '#1B5E20' }]}>
                R$ {totais.entradas.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </Text>
            </View>

            <View style={[styles.kpiCard, { backgroundColor: '#FFEBEE' }]}>
              <View style={styles.kpiHeader}>
                <Ionicons name="arrow-up-circle" size={18} color="#C62828" />
                <Text style={[styles.kpiLabel, { color: '#C62828' }]}>Saídas</Text>
              </View>
              <Text style={[styles.kpiValor, { color: '#B71C1C' }]}>
                R$ {totais.saidas.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </Text>
            </View>
          </View>

          {/* 3. Filtros Secundários em Scroll Horizontal */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filtrosScroll}>
            <FilterButton rotulo="Mês" texto="Outubro" icone="calendar-outline" />
            <FilterButton rotulo="Status" texto="Todos" icone="filter-outline" />
            <FilterButton rotulo="Aluno" texto="Todos" icone="people-outline" />
            <FilterButton rotulo="Tipo" texto="Todos" icone="swap-horizontal-outline" />
          </ScrollView>

          {/* 4. Card Estilizado do Gráfico de Fluxo de Caixa */}
          <View style={styles.chartCard}>
            <View style={styles.chartHeader}>
              <View>
                <Text style={styles.chartTitle}>Movimentação de Caixa</Text>
                <Text style={styles.chartSubtitle}>Comparativo diário</Text>
              </View>
              <View style={styles.legendContainer}>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: '#4CAF50' }]} />
                  <Text style={styles.legendText}>Entradas</Text>
                </View>
                <View style={styles.legendItem}>
                  <View style={[styles.legendDot, { backgroundColor: '#EF5350' }]} />
                  <Text style={styles.legendText}>Saídas</Text>
                </View>
              </View>
            </View>

            <CashFlowChart dados={FLUXO_CAIXA_MOCK} />
          </View>

          {/* 5. Ações e Título do Histórico */}
          <View style={styles.historicoHeader}>
            <Text style={styles.historicoTitulo}>Detalhamento dos Lançamentos</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Imprimir relatório"
              onPress={() => {}}
              style={({ pressed }) => [styles.btnImprimir, pressed && styles.pressionado]}
            >
              <Ionicons name="print-outline" size={16} color={palette.header} />
              <Text style={styles.btnImprimirTexto}>Exportar PDF</Text>
            </Pressable>
          </View>

          <LancamentosHeader />
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 32 },
  headerWrapper: { gap: 16 },
  
  /* Segmented Control (Tabs de Período) */
  segmentedContainer: {
    flexDirection: 'row',
    backgroundColor: '#EFEFEF',
    borderRadius: 10,
    padding: 3,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  segmentBtnActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  segmentText: { fontSize: 12, color: palette.textMuted, fontWeight: '500' },
  segmentTextActive: { color: palette.header, fontWeight: '700' },

  /* Cards KPI Totais */
  kpiContainer: { flexDirection: 'row', gap: 12 },
  kpiCard: {
    flex: 1,
    padding: 12,
    borderRadius: 12,
    gap: 6,
  },
  kpiHeader: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  kpiLabel: { fontSize: 12, fontWeight: '600' },
  kpiValor: { fontSize: 16, fontWeight: '700' },

  /* Filtros Scroll */
  filtrosScroll: { flexDirection: 'row', gap: 8, paddingBottom: 4 },

  /* Card do Gráfico */
  chartCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  chartSubtitle: { fontSize: 11, color: palette.textMuted, marginTop: 2 },
  legendContainer: { flexDirection: 'row', gap: 10 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot: { width: 8, height: 8, borderRadius: 4 },
  legendText: { fontSize: 10, color: palette.textMuted, fontWeight: '500' },

  /* Seção de Histórico */
  historicoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  historicoTitulo: { fontSize: 14, fontWeight: '700', color: palette.title },
  btnImprimir: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0F0F0',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  btnImprimirTexto: { fontSize: 11, color: palette.header, fontWeight: '600' },

  pressionado: { opacity: 0.7 },
  separador: { height: StyleSheet.hairlineWidth, backgroundColor: palette.line },
  vazio: { textAlign: 'center', color: palette.textMuted, marginTop: 24 },
});