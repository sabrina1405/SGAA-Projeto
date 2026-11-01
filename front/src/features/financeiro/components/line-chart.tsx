import { useState } from 'react';
import { LayoutChangeEvent, StyleSheet, View } from 'react-native';
import Svg, { Line, Path, Text as SvgText } from 'react-native-svg';

import { palette } from '@/constants/palette';

export type SerieLinha = {
  nome: string;
  valores: number[]; // um valor para cada rótulo
  cor: string;
};

type Props = {
  rotulos: string[];
  series: SerieLinha[];
  // Linha horizontal tracejada (meta, média...)
  referencia?: { valor: number; cor: string };
  altura?: number;
};

const MARGEM = { esquerda: 40, direita: 12, topo: 12, base: 24 };
const DIVISOES = 4;

// Arredonda o maior valor para cima, para o eixo Y ter números "redondos".
function calcularTeto(maior: number) {
  if (maior <= 0) return 100;
  const passo = 10 ** Math.floor(Math.log10(maior));
  return Math.ceil(maior / passo) * passo;
}

// Curva suave que liga os pontos sem ultrapassar o valor de cada trecho.
function caminhoSuave(pontos: { x: number; y: number }[]) {
  return pontos
    .map((p, i) => {
      if (i === 0) return `M ${p.x} ${p.y}`;
      const anterior = pontos[i - 1];
      const meio = (anterior.x + p.x) / 2;
      return `C ${meio} ${anterior.y}, ${meio} ${p.y}, ${p.x} ${p.y}`;
    })
    .join(' ');
}

export function LineChart({ rotulos, series, referencia, altura = 220 }: Props) {
  const [largura, setLargura] = useState(0);

  const aoMedir = (e: LayoutChangeEvent) => setLargura(e.nativeEvent.layout.width);

  const maior = Math.max(0, referencia?.valor ?? 0, ...series.flatMap((s) => s.valores));
  const teto = calcularTeto(maior);

  const areaLargura = Math.max(largura - MARGEM.esquerda - MARGEM.direita, 0);
  const areaAltura = altura - MARGEM.topo - MARGEM.base;
  const passoX = rotulos.length > 1 ? areaLargura / (rotulos.length - 1) : 0;

  const xDe = (indice: number) => MARGEM.esquerda + indice * passoX;
  const yDe = (valor: number) => MARGEM.topo + areaAltura - (valor / teto) * areaAltura;

  const marcas = Array.from({ length: DIVISOES + 1 }, (_, i) => Math.round((teto / DIVISOES) * i));

  return (
    <View
      onLayout={aoMedir}
      style={styles.container}
      accessible
      accessibilityLabel={`Gráfico de linhas: ${series.map((s) => s.nome).join(', ')}`}
    >
      {largura > 0 && (
        <Svg width={largura} height={altura}>
          {marcas.map((valor) => (
            <SvgText
              key={valor}
              x={MARGEM.esquerda - 6}
              y={yDe(valor) + 3}
              fontSize={10}
              fontWeight="700"
              fill={palette.textMuted}
              textAnchor="end"
            >
              {valor}
            </SvgText>
          ))}

          <Line
            x1={MARGEM.esquerda}
            y1={yDe(0)}
            x2={largura - MARGEM.direita}
            y2={yDe(0)}
            stroke={palette.line}
            strokeWidth={1}
          />
          <Line
            x1={MARGEM.esquerda}
            y1={MARGEM.topo}
            x2={MARGEM.esquerda}
            y2={yDe(0)}
            stroke={palette.line}
            strokeWidth={1}
          />

          {referencia && (
            <Line
              x1={MARGEM.esquerda}
              y1={yDe(referencia.valor)}
              x2={largura - MARGEM.direita}
              y2={yDe(referencia.valor)}
              stroke={referencia.cor}
              strokeWidth={1.5}
              strokeDasharray="6 4"
            />
          )}

          {series.map((serie) => (
            <Path
              key={serie.nome}
              d={caminhoSuave(serie.valores.map((v, i) => ({ x: xDe(i), y: yDe(v) })))}
              stroke={serie.cor}
              strokeWidth={1.5}
              fill="none"
            />
          ))}

          {rotulos.map((rotulo, i) => (
            <SvgText
              key={`${rotulo}-${i}`}
              x={xDe(i)}
              y={altura - 6}
              fontSize={9}
              fontWeight="700"
              fill={palette.title}
              textAnchor="middle"
            >
              {rotulo}
            </SvgText>
          ))}
        </Svg>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: 16 },
});