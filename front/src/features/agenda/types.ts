export type StatusEvento = 'confirmada' | 'pendente' | 'reposicao';
export type FiltroStatus = StatusEvento | 'todos';

export type Evento = {
  id: string;
  data: string; // 'YYYY-MM-DD'
  aluno: string;
  inicio: string; // 'HH:mm'
  fim: string; // 'HH:mm'
  status: StatusEvento;
};

// null = célula vazia (antes do dia 1 / depois do último dia)
export type CelulaDia = { dia: number; data: string } | null;