import { useMemo } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { palette } from '@/constants/palette';
import { FilterButton } from '@/features/financeiro/components/filter-button';
import { LancamentoRow, LancamentosHeader } from '@/features/financeiro/components/lancamento-row';
import { SummaryCard } from '@/features/financeiro/components/summary-card';
import { LANCAMENTOS_MOCK } from '@/features/financeiro/mock';
import { calcularResumo } from '@/features/financeiro/utils';

function Separador() {
  return <View style={styles.separador} />;
}

export default function FinanceiroScreen() {
  const router = useRouter();
  const lancamentos = LANCAMENTOS_MOCK;
  const resumo = useMemo(() => calcularResumo(lancamentos), [lancamentos]);

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
          <Text style={styles.titulo}>Resumo Financeiro</Text>

          <View style={styles.cards}>
            <SummaryCard
              titulo="Saldo"
              valor={resumo.saldo}
              fundo={palette.saldo.fundo}
              corValor={palette.saldo.valor}
            />
            <SummaryCard
              titulo="Previsão de entradas:"
              valor={resumo.previsaoEntradas}
              fundo={palette.previsao.fundo}
              corValor={palette.previsao.valor}
            />
          </View>

          {/* Atalhos para as outras telas do Módulo Financeiro */}
          <View style={styles.atalhosContainer}>
            <Pressable
              style={({ pressed }) => [styles.cardAtalho, pressed && styles.pressionado]}
              onPress={() => router.push('./fluxoDeCaixa')}
            >
              <Ionicons name="bar-chart-outline" size={22} color={palette.header} />
              <View style={styles.textosAtalho}>
                <Text style={styles.tituloAtalho}>Fluxo de Caixa</Text>
                <Text style={styles.subtituloAtalho}>Entradas e saídas mensais</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={palette.textMuted} />
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.cardAtalho, pressed && styles.pressionado]}
              onPress={() => router.push('./relatorioFinanceiro')}
            >
              <Ionicons name="document-text-outline" size={22} color={palette.header} />
              <View style={styles.textosAtalho}>
                <Text style={styles.tituloAtalho}>Relatórios Anuais</Text>
                <Text style={styles.subtituloAtalho}>Balanço de lucros e histórico</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={palette.textMuted} />
            </Pressable>
          </View>

          <View style={styles.filtros}>
            <FilterButton rotulo="Filtrar por Período" texto="Data" icone="calendar-outline" />
            <FilterButton rotulo="Filtrar por Status" texto="Status" icone="filter-outline" />
            <FilterButton rotulo="Filtrar por Aluno" texto="Aluno" icone="people-outline" />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Novo item"
              onPress={() => {}}
              style={({ pressed }) => [styles.novoItem, pressed && styles.pressionado]}
            >
              <Text style={styles.novoItemTexto}>Novo Item</Text>
              <Ionicons name="add" size={18} color="#fff" />
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
  titulo: { fontSize: 16, fontWeight: '700', color: palette.title, marginBottom: 16 },
  cards: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  
  /* Novos Estilos dos Cards de Atalho */
  atalhosContainer: { gap: 10, marginBottom: 20 },
  cardAtalho: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: palette.line,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  textosAtalho: { flex: 1, marginLeft: 12 },
  tituloAtalho: { fontSize: 13, fontWeight: '600', color: palette.title },
  subtituloAtalho: { fontSize: 11, color: palette.textMuted, marginTop: 2 },

  filtros: { flexDirection: 'row', alignItems: 'flex-end', gap: 8, marginBottom: 16 },
  novoItem: {
    flex: 1,
    height: 38,
    borderRadius: 8,
    backgroundColor: palette.button,
    paddingHorizontal: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  novoItemTexto: { color: '#fff', fontSize: 11 },
  pressionado: { opacity: 0.8 },
  separador: { height: StyleSheet.hairlineWidth, backgroundColor: palette.line },
  vazio: { textAlign: 'center', color: palette.textMuted, marginTop: 24 },
});