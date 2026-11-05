import { Ionicons } from '@expo/vector-icons';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import { AgendaItem } from '@/features/agenda/components/agenda-item';
import { CalendarGrid } from '@/features/agenda/components/calendar-grid';
import { MonthHeader } from '@/features/agenda/components/month-header';
import { StatusFilter } from '@/features/agenda/components/status-filter';
import { useAulas } from '@/features/agenda/use-aulas';
import type { FiltroStatus } from '@/features/agenda/types';
import { MESES, agruparPorData, chaveData, rotuloDia } from '@/features/agenda/utils';

import { useLocalSearchParams, useRouter } from 'expo-router';

export default function AgendaScreen() {
  const router = useRouter();
  const agora = new Date();
  const hoje = chaveData(agora.getFullYear(), agora.getMonth(), agora.getDate());

  // 'YYYY-MM-DD' enviado pela tela "novo" para abrir a agenda no dia da aula criada
  const { data } = useLocalSearchParams<{ data?: string }>();

  const [ano, setAno] = useState(agora.getFullYear());
  const [mes, setMes] = useState(agora.getMonth());
  const [selecionada, setSelecionada] = useState(hoje);
  const [filtro, setFiltro] = useState<FiltroStatus>('todos');

  const { eventos, carregando, erro } = useAulas(ano, mes);

  useEffect(() => {
    if (!data) return;
    const [a, m] = data.split('-').map(Number);
    setAno(a);
    setMes(m - 1);
    setSelecionada(data);
  }, [data]);

  const eventosPorData = useMemo(() => {
    const filtrados = filtro === 'todos' ? eventos : eventos.filter((e) => e.status === filtro);
    return agruparPorData(filtrados);
  }, [eventos, filtro]);

  const doDia = eventosPorData[selecionada] ?? [];

  function mudarMes(delta: number) {
    const d = new Date(ano, mes + delta, 1);
    setAno(d.getFullYear());
    setMes(d.getMonth());
    // seleciona hoje se o mês for o atual; senão, o dia 1
    const ehMesAtual = d.getFullYear() === agora.getFullYear() && d.getMonth() === agora.getMonth();
    setSelecionada(ehMesAtual ? hoje : chaveData(d.getFullYear(), d.getMonth(), 1));
  }

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.conteudo}>
        <MonthHeader mes={MESES[mes]} ano={ano} onAnterior={() => mudarMes(-1)} onProximo={() => mudarMes(1)} />

        <View style={styles.bloco}>
          <StatusFilter valor={filtro} onChange={setFiltro} />
        </View>

        <View style={styles.bloco}>
          <CalendarGrid
            ano={ano}
            mes={mes}
            eventosPorData={eventosPorData}
            selecionada={selecionada}
            hoje={hoje}
            onSelecionar={setSelecionada}
          />
        </View>

        <View style={styles.divisor} />

        <Text style={styles.tituloDia}>{rotuloDia(selecionada)}</Text>

        {doDia.length === 0 ? (
          <Text style={styles.vazio}>Nenhum compromisso neste dia.</Text>
        ) : (
          doDia.map((e) => <AgendaItem key={e.id} evento={e} />)
        )}
      </ScrollView>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Novo item"
        onPress={() => router.push('/professor/agenda/novo')}
        style={({ pressed }) => [styles.fab, pressed && styles.pressionado]}
      >
        <Ionicons name="add" size={28} color="#fff" />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 20, paddingBottom: 100 },
  bloco: { marginTop: 16 },
  divisor: { height: StyleSheet.hairlineWidth, backgroundColor: palette.line, marginVertical: 16 },
  tituloDia: { fontSize: 16, fontWeight: '700', color: palette.title, marginBottom: 4 },
  vazio: { color: palette.textMuted, marginTop: 12 },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: palette.button,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
  },
  pressionado: { opacity: 0.85 },
});