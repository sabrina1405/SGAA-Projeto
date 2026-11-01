import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';

export type FluxoPonto = {
  rotulo: string; // ex.: '01' (dia) ou 'Out' (mês)
  entradas: number;
  saidas: number;
};

type Props = {
  dados: FluxoPonto[];
  altura?: number;
};

// Cores das barras, iguais às do protótipo. Se quiser, mova para a palette.
const COR_ENTRADA = '#2fd04b';
const COR_SAIDA = '#f0383a';

const LARGURA_GRUPO = 26;
const LARGURA_BARRA = 7;
const DIVISOES = 4;

// Arredonda o maior valor para cima, para o eixo Y ter números "redondos".
function calcularTeto(maior: number) {
  if (maior <= 0) return 100;
  const passo = 10 ** Math.floor(Math.log10(maior));
  return Math.ceil(maior / passo) * passo;
}

export function CashFlowChart({ dados, altura = 140 }: Props) {
  const maior = Math.max(0, ...dados.map((d) => Math.max(d.entradas, d.saidas)));
  const teto = calcularTeto(maior);

  // De cima para baixo: teto, 3/4, 1/2, 1/4, 0
  const marcas = Array.from({ length: DIVISOES + 1 }, (_, i) =>
    Math.round(teto - (teto / DIVISOES) * i),
  );

  return (
    <View
      style={styles.container}
      accessible
      accessibilityLabel="Gráfico de entradas e saídas do fluxo de caixa"
    >
      <View style={[styles.eixoY, { height: altura }]}>
        {marcas.map((valor) => (
          <Text key={valor} style={styles.marcaY}>
            {valor}
          </Text>
        ))}
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View>
          <View style={[styles.area, { height: altura }]}>
            {dados.map((ponto, i) => (
              <View key={`${ponto.rotulo}-${i}`} style={styles.grupo}>
                <View
                  style={[
                    styles.barra,
                    { height: (ponto.entradas / teto) * altura, backgroundColor: COR_ENTRADA },
                  ]}
                />
                <View
                  style={[
                    styles.barra,
                    { height: (ponto.saidas / teto) * altura, backgroundColor: COR_SAIDA },
                  ]}
                />
              </View>
            ))}
          </View>

          <View style={styles.eixoX}>
            {dados.map((ponto, i) => (
              <Text key={`${ponto.rotulo}-${i}`} style={styles.marcaX}>
                {ponto.rotulo}
              </Text>
            ))}
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexDirection: 'row', marginBottom: 16 },
  eixoY: { width: 34, justifyContent: 'space-between', alignItems: 'flex-end', paddingRight: 6 },
  marcaY: { fontSize: 10, fontWeight: '700', color: palette.textMuted },
  area: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderLeftWidth: 1,
    borderBottomWidth: 1,
    borderColor: palette.line,
  },
  grupo: {
    width: LARGURA_GRUPO,
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'center',
    gap: 2,
  },
  barra: { width: LARGURA_BARRA },
  eixoX: { flexDirection: 'row', marginTop: 4 },
  marcaX: { width: LARGURA_GRUPO, textAlign: 'center', fontSize: 10, fontWeight: '700', color: palette.title },
});