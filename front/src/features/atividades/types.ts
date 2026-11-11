export type StatusEntrega = 'enviado' | 'entregue_com_atraso';
export type SituacaoEntrega = 'proximas' | 'vencidas' | 'entregues';

export type Resposta<T> = { mensagem: string; dados: T };
export type Pagina<T> = { itens: T[]; total: number };

export type EntregaListaItem = {
  atividade_id: number;
  titulo: string;
  vence_em: string;
  aluno_id: number;
  aluno_nome: string;
  status: StatusEntrega | null;
  enviada_em: string | null;
};

export type AtividadeCriar = {
  titulo: string;
  descricao: string;
  liberar_em: string;
  vence_em: string;
  permite_envio_arquivo?: boolean;
  todos_alunos?: boolean;
  todos_grupos?: boolean;
  aluno_ids?: number[];
  grupo_ids?: number[];
  arquivo_ids?: number[];
};