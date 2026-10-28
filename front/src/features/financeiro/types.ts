export type StatusPagamento = 'pago' | 'pendente' | 'vencido';

export interface Lancamento {
  id: string;
  dataAgendada: string; // ISO: AAAA-MM-DD
  dataPagamento: string | null; // null enquanto não foi pago
  alunoNome: string;
  valor: number;
  status: StatusPagamento;
}

export interface ResumoFinanceiro {
  saldo: number;
  previsaoEntradas: number;
}
