import { api } from '@/services/api'; // o mesmo cliente das outras telas

export type RecadoGeral = {
  conteudo: string;
  atualizado_em: string;
};

export type RecadoListaItem = {
  id: number;
  conteudo: string;
  data_inicio: string; // AAAA-MM-DD
  data_fim: string | null;
  todos_alunos: boolean;
  todos_grupos: boolean;
  total_alunos: number;
  total_grupos: number;
  criado_em: string;
};

export type NovoRecado = {
  conteudo: string;
  data_inicio?: string; // AAAA-MM-DD; sem isso a API usa a data de hoje
  data_fim?: string | null; // AAAA-MM-DD; sem isso fica no mural até ser excluído
  todos_alunos?: boolean;
  todos_grupos?: boolean;
  aluno_ids?: number[];
  grupo_ids?: number[];
};

type Pagina<T> = { itens: T[]; total: number };

/** Retorna null quando o painel está vazio. */
export async function obterRecadoGeral(): Promise<RecadoGeral | null> {
  const { data } = await api.get('/recados/geral');
  return data.dados ?? null;
}

export async function salvarRecadoGeral(conteudo: string): Promise<RecadoGeral> {
  const { data } = await api.put('/recados/geral', { conteudo });
  return data.dados;
}

export async function limparRecadoGeral(): Promise<void> {
  await api.delete('/recados/geral');
}

export async function listarRecados(pagina = 1, tamanho = 20): Promise<Pagina<RecadoListaItem>> {
  const { data } = await api.get('/recados', { params: { pagina, tamanho } });
  return data.dados;
}

export async function criarRecado(recado: NovoRecado): Promise<void> {
  await api.post('/recados', recado);
}

export async function excluirRecado(id: number): Promise<void> {
  await api.delete(`/recados/${id}`);
}

// Lê a mensagem que o back manda em `detail`; sem ela, usa a padrão.
export function mensagemDeErro(erro: unknown, padrao: string) {
  const detalhe = (erro as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detalhe === 'string') return detalhe;
  if (Array.isArray(detalhe)) {
    const msgs = detalhe.map((d) => (typeof d?.msg === 'string' ? d.msg : null)).filter(Boolean);
    if (msgs.length) return msgs.join('\n');
  }
  return padrao;
}