import type { Lancamento } from './types';

// Dados de exemplo. Quando a API (FastAPI) estiver pronta, troque por uma chamada em services.
export const LANCAMENTOS_MOCK: Lancamento[] = [
  { id: '1', dataAgendada: '2026-10-05', dataPagamento: null, alunoNome: 'Ana Souza', valor: 350, status: 'vencido' },
  { id: '2', dataAgendada: '2026-11-05', dataPagamento: null, alunoNome: 'Bruno Lima', valor: 350, status: 'pendente' },
  { id: '3', dataAgendada: '2026-10-10', dataPagamento: '2026-10-09', alunoNome: 'Carla Dias', valor: 250, status: 'pago' },
  { id: '4', dataAgendada: '2026-10-15', dataPagamento: '2026-10-15', alunoNome: 'Diego Alves', valor: 350, status: 'pago' },
];
