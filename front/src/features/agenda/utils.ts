import type { CelulaDia, Evento } from './types';

export const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];

export const DIAS_SEMANA_CURTO = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']; // seg..dom
const DIAS_SEMANA_LONGO = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'];

const dois = (n: number) => String(n).padStart(2, '0');

export function chaveData(ano: number, mes: number, dia: number) {
  return `${ano}-${dois(mes + 1)}-${dois(dia)}`;
}

// 'Quinta, 5 de novembro'
export function rotuloDia(chave: string) {
  const [a, m, d] = chave.split('-').map(Number);
  const diaSemana = DIAS_SEMANA_LONGO[new Date(a, m - 1, d).getDay()];
  return `${diaSemana}, ${d} de ${MESES[m - 1].toLowerCase()}`;
}

// mes: 0-11. Semana começa na segunda.
export function gerarSemanas(ano: number, mes: number): CelulaDia[][] {
  const diasNoMes = new Date(ano, mes + 1, 0).getDate();
  const offset = (new Date(ano, mes, 1).getDay() + 6) % 7;

  const celulas: CelulaDia[] = [
    ...Array<CelulaDia>(offset).fill(null),
    ...Array.from({ length: diasNoMes }, (_, i) => ({
      dia: i + 1,
      data: chaveData(ano, mes, i + 1),
    })),
  ];
  while (celulas.length % 7 !== 0) celulas.push(null);

  const semanas: CelulaDia[][] = [];
  for (let i = 0; i < celulas.length; i += 7) semanas.push(celulas.slice(i, i + 7));
  return semanas;
}

export function agruparPorData(eventos: Evento[]) {
  const mapa: Record<string, Evento[]> = {};
  for (const e of eventos) (mapa[e.data] ??= []).push(e);
  for (const k of Object.keys(mapa)) mapa[k].sort((a, b) => a.inicio.localeCompare(b.inicio));
  return mapa;
}