import { Pressable, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';
import { STATUS_INFO } from '../status';
import type { Evento } from '../types';
import { DIAS_SEMANA_CURTO, gerarSemanas } from '../utils';

const MAX_PONTOS = 3;

type Props = {
  ano: number;
  mes: number; // 0-11
  eventosPorData: Record<string, Evento[]>;
  selecionada: string;
  hoje: string;
  onSelecionar: (data: string) => void;
};

export function CalendarGrid({ ano, mes, eventosPorData, selecionada, hoje, onSelecionar }: Props) {
  const semanas = gerarSemanas(ano, mes);

  return (
    <View>
      <View style={styles.linha}>
        {DIAS_SEMANA_CURTO.map((d, i) => (
          <Text key={i} style={styles.diaSemana}>{d}</Text>
        ))}
      </View>

      {semanas.map((semana, i) => (
        <View key={i} style={styles.linha}>
          {semana.map((celula, j) => {
            if (!celula) return <View key={j} style={styles.celula} />;

            const doDia = eventosPorData[celula.data] ?? [];
            const ativo = celula.data === selecionada;
            const ehHoje = celula.data === hoje;

            return (
              <Pressable
                key={j}
                accessibilityRole="button"
                accessibilityState={{ selected: ativo }}
                accessibilityLabel={`Dia ${celula.dia}, ${doDia.length} compromisso(s)`}
                onPress={() => onSelecionar(celula.data)}
                style={styles.celula}
              >
                <View style={[styles.circulo, ehHoje && !ativo && styles.circuloHoje, ativo && styles.circuloAtivo]}>
                  <Text style={[styles.numero, ehHoje && styles.numeroHoje, ativo && styles.numeroAtivo]}>
                    {celula.dia}
                  </Text>
                </View>
                <View style={styles.pontos}>
                  {doDia.slice(0, MAX_PONTOS).map((e) => (
                    <View key={e.id} style={[styles.ponto, { backgroundColor: STATUS_INFO[e.status].cor }]} />
                  ))}
                </View>
              </Pressable>
            );
          })}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  linha: { flexDirection: 'row' },
  diaSemana: {
    flex: 1,
    textAlign: 'center',
    fontSize: 12,
    color: palette.textMuted,
    paddingVertical: 8,
  },
  celula: { flex: 1, height: 52, alignItems: 'center', paddingTop: 2 },
  circulo: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  circuloAtivo: { backgroundColor: palette.primary },
  circuloHoje: { borderWidth: 1.5, borderColor: palette.primary },
  numero: { fontSize: 15, color: palette.title },
  numeroHoje: { fontWeight: '700' },
  numeroAtivo: { color: '#fff', fontWeight: '700' },
  pontos: { flexDirection: 'row', gap: 3, height: 5, marginTop: 3 },
  ponto: { width: 5, height: 5, borderRadius: 2.5 },
});