export type StatusPagamento = 'pago' | 'pendente' | 'vencido';

export interface Lancamento {
  id: string;
  dataAgendada: string; 
  dataPagamento: string | null;
  alunoNome: string;
  valor: number;
  status: StatusPagamento;
}

export interface ResumoFinanceiro {
  saldo: number;
  previsaoEntradas: number;
}
