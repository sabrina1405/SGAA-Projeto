import type { RelatorioLinha } from '@/features/financeiro/components/relatorio-row';

// Dados de exemplo do Relatório Financeiro Anual. Troque por dados da API
// quando existirem.
export const RELATORIO_MENSAL_MOCK = {
  rotulos: ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'],
  entradas: [300, 800, 1500, 2100, 1400, 600, 600, 2600, 2800, 1200, 100, 700],
  saidas: [800, 300, 300, 300, 800, 500, 500, 500, 500, 1000, 0, 0],
  referencia: 1000,
};

export const RELATORIO_LINHAS_MOCK: RelatorioLinha[] = [
  { id: '1', ano: '2023', mes: '---------', entradas: 100, saidas: 300, lucro: -200, situacao: 'negativo' },
  { id: '2', ano: '2026', mes: '---------', entradas: null, saidas: null, lucro: 4000, situacao: 'previsto' },
  { id: '3', ano: '2027', mes: '---------', entradas: null, saidas: null, lucro: 4000, situacao: 'previsto' },
  { id: '4', ano: '2025', mes: '---------', entradas: 4000, saidas: 0, lucro: 4000, situacao: 'realizado' },
];