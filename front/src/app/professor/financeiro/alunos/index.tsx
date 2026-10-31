import { useMemo } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';


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

          <View style={styles.filtros}>
            {/* onPress dos filtros: ligar quando os seletores existirem */}
            <FilterButton rotulo="Filtrar por Período" texto="Data" icone="calendar-outline" />
            <FilterButton rotulo="Filtrar por Status" texto="Status" icone="filter-outline" />
            <FilterButton rotulo="Filtrar por Aluno" texto="Aluno" icone="people-outline" />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Novo item"
              // TODO: router.push('/professor/financeiro/novo') quando a tela existir
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
  cards: { flexDirection: 'row', gap: 12, marginBottom: 20 },
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
