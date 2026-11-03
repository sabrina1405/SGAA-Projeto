import type { FluxoPonto } from '@/features/financeiro/components/cash-flow-chart';


export const FLUXO_CAIXA_MOCK: FluxoPonto[] = [
  { rotulo: '01', entradas: 100, saidas: 300 },
  { rotulo: '05', entradas: 300, saidas: 100 },
  { rotulo: '10', entradas: 0, saidas: 0 },
  { rotulo: '15', entradas: 300, saidas: 100 },
  { rotulo: '20', entradas: 0, saidas: 0 },
  { rotulo: '25', entradas: 200, saidas: 50 },
  { rotulo: '30', entradas: 300, saidas: 100 },
];