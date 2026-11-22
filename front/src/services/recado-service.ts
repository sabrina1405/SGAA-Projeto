const API_URL = process.env.EXPO_PUBLIC_API_URL;

type Resposta<T> = { mensagem: string; dados: T };
type Pagina<T> = { itens: T[]; total: number };

export type RecadoGeral = {
  conteudo: string;
  atualizado_em: string;
};

export type RecadoListaItem = {
  id: number;
  conteudo: string;
  data_inicio: string;
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
  data_fim?: string | null; // AAAA-MM-DD
  todos_alunos?: boolean;
  todos_grupos?: boolean;
  aluno_ids?: number[];
  grupo_ids?: number[];
};

// Troque por o seu cliente HTTP (base URL e token) se já tiver um.
async function chamar<T>(token: string, caminho: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${caminho}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  const corpo = await res.json().catch(() => null);
  if (!res.ok) {
    const detalhe = typeof corpo?.detail === 'string' ? corpo.detail : 'Falha na requisição.';
    throw new Error(detalhe);
  }
  return corpo as T;
}

/** Retorna null quando o painel está vazio. */
export async function obterRecadoGeral(token: string): Promise<RecadoGeral | null> {
  const res = await chamar<Resposta<RecadoGeral | null>>(token, '/recados/geral');
  return res.dados ?? null;
}

export async function salvarRecadoGeral(token: string, conteudo: string): Promise<RecadoGeral> {
  const res = await chamar<Resposta<RecadoGeral>>(token, '/recados/geral', {
    method: 'PUT',
    body: JSON.stringify({ conteudo }),
  });
  return res.dados;
}

export async function limparRecadoGeral(token: string): Promise<void> {
  await chamar(token, '/recados/geral', { method: 'DELETE' });
}

export async function listarRecados(
  token: string,
  pagina = 1,
  tamanho = 20,
): Promise<Pagina<RecadoListaItem>> {
  const res = await chamar<Resposta<Pagina<RecadoListaItem>>>(
    token,
    `/recados?pagina=${pagina}&tamanho=${tamanho}`,
  );
  return res.dados;
}

export async function criarRecado(token: string, recado: NovoRecado): Promise<void> {
  await chamar(token, '/recados', {
    method: 'POST',
    body: JSON.stringify(recado),
  });
}

export async function excluirRecado(token: string, id: number): Promise<void> {
  await chamar(token, `/recados/${id}`, { method: 'DELETE' });
}