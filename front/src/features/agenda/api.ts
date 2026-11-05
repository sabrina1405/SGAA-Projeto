import { api } from '@/services/api'; 

// ───────────────────────────────────────────────────────────────
// MODO DEMONSTRAÇÃO: true = as aulas ficam só no front (sem back).
// Para ligar de verdade ao back, troque para false.
// ───────────────────────────────────────────────────────────────
export const USAR_MOCK = true;

export type Escopo = 'esta' | 'esta_e_seguintes';
export type StatusAulaApi = 'agendada' | 'realizada' | 'cancelada';
export type StatusParticipacaoApi = 'ativa' | 'cancelada';

type Resposta<T> = { mensagem: string; dados: T };

export type AulaListaItemApi = {
  id: number;
  titulo: string;
  inicio: string; // ISO com -03:00
  fim: string;
  status: StatusAulaApi;
  serie_id: number | null;
  alunos: { id: number; nome_completo: string; status: StatusParticipacaoApi }[];
};

export type AulaDetalheApi = {
  id: number;
  titulo: string;
  descricao: string | null;
  anotacoes: string | null;
  inicio: string;
  fim: string;
  status: StatusAulaApi;
  motivo_cancelamento: string | null;
  serie_id: number | null;
  reposicao_de_aula_id: number | null;
  alunos: {
    id: number;
    nome_completo: string;
    email: string;
    telefone: string;
    status: StatusParticipacaoApi;
    motivo_cancelamento: string | null;
    repor: boolean;
  }[];
  grupos: { id: number; titulo: string }[];
  criado_em: string;
};

export type AulaCriarPayload = {
  titulo: string;
  descricao?: string | null;
  anotacoes?: string | null;
  inicio: string; // ISO com offset
  fim: string;
  aluno_ids: number[];
  grupo_ids: number[];
  repetir_semanalmente?: boolean;
  repetir_ate?: string | null; // 'YYYY-MM-DD'
  nomes_mock?: string[]; // só usado no modo demonstração
};

// Só o que for enviado é alterado. titulo/inicio/fim/status não aceitam null.
export type AulaAtualizarPayload = Partial<{
  titulo: string;
  descricao: string | null;
  anotacoes: string | null;
  inicio: string;
  fim: string;
  status: 'agendada' | 'realizada';
}>;

// ─────────────────────────── MODO DEMONSTRAÇÃO ───────────────────────────

const CHAVE_MOCK = 'agenda-mock-aulas';
const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));

const aulaSemente = (
  id: number,
  titulo: string,
  data: string,
  ini: string,
  fim: string,
  nome: string,
  status: StatusAulaApi = 'agendada',
): AulaListaItemApi => ({
  id,
  titulo,
  inicio: `${data}T${ini}:00-03:00`,
  fim: `${data}T${fim}:00-03:00`,
  status,
  serie_id: null,
  alunos: [{ id, nome_completo: nome, status: 'ativa' }],
});

// Persiste no localStorage quando existir (web); no celular fica só em memória.
function lerSalvas(): AulaListaItemApi[] | null {
  try {
    const t = (globalThis as any).localStorage?.getItem(CHAVE_MOCK);
    return t ? JSON.parse(t) : null;
  } catch {
    return null;
  }
}

function gravar() {
  try {
    (globalThis as any).localStorage?.setItem(CHAVE_MOCK, JSON.stringify(aulasMock));
  } catch {
    /* sem storage: segue só em memória */
  }
}

const aulasMock: AulaListaItemApi[] = lerSalvas() ?? [
  aulaSemente(1, 'Aula de Espanhol 01', '2026-11-12', '10:00', '11:00', 'Ana Souza'),
  aulaSemente(2, 'Aula de Espanhol 02', '2026-11-13', '14:00', '15:00', 'Bruno Lima'),
  aulaSemente(3, 'Revisão', '2026-11-20', '09:00', '10:00', 'Carla Dias', 'realizada'),
];
let proximoId = Math.max(100, ...aulasMock.map((a) => a.id + 1));

function paraDetalhe(a: AulaListaItemApi): AulaDetalheApi {
  return {
    id: a.id,
    titulo: a.titulo,
    descricao: null,
    anotacoes: null,
    inicio: a.inicio,
    fim: a.fim,
    status: a.status,
    motivo_cancelamento: null,
    serie_id: a.serie_id,
    reposicao_de_aula_id: null,
    alunos: a.alunos.map((x) => ({
      ...x,
      email: '',
      telefone: '',
      motivo_cancelamento: null,
      repor: false,
    })),
    grupos: [],
    criado_em: new Date().toISOString(),
  };
}

// ─────────────────────────────── CHAMADAS ───────────────────────────────

export async function listarAulas(dataInicio: string, dataFim: string, status?: StatusAulaApi) {
  if (USAR_MOCK) {
    await espera(250);
    return aulasMock
      .filter((a) => {
        const dia = a.inicio.slice(0, 10);
        return dia >= dataInicio && dia <= dataFim && (!status || a.status === status);
      })
      .sort((x, y) => x.inicio.localeCompare(y.inicio));
  }
  const { data } = await api.get<Resposta<AulaListaItemApi[]>>('/aulas', {
    params: { data_inicio: dataInicio, data_fim: dataFim, ...(status && { status }) },
  });
  return data.dados;
}

export async function obterAula(id: number | string) {
  if (USAR_MOCK) {
    await espera(150);
    const aula = aulasMock.find((a) => a.id === Number(id));
    if (!aula) throw { response: { data: { detail: 'Aula não encontrada' } } };
    return paraDetalhe(aula);
  }
  const { data } = await api.get<Resposta<AulaDetalheApi>>(`/aulas/${id}`);
  return data.dados;
}

export async function criarAula(payload: AulaCriarPayload) {
  if (USAR_MOCK) {
    await espera(400);
    const nova: AulaListaItemApi = {
      id: proximoId++,
      titulo: payload.titulo,
      inicio: payload.inicio,
      fim: payload.fim,
      status: 'agendada',
      serie_id: null,
      alunos: (payload.nomes_mock?.length ? payload.nomes_mock : ['Aluno']).map((nome, i) => ({
        id: i + 1,
        nome_completo: nome,
        status: 'ativa' as const,
      })),
    };
    aulasMock.push(nova);
    gravar();
    return paraDetalhe(nova);
  }
  const { nomes_mock, ...corpo } = payload;
  const { data } = await api.post<Resposta<AulaDetalheApi>>('/aulas', corpo);
  return data.dados;
}

export async function atualizarAula(
  id: number | string,
  payload: AulaAtualizarPayload,
  escopo: Escopo = 'esta',
) {
  const { data } = await api.patch<Resposta<AulaDetalheApi>>(`/aulas/${id}`, payload, {
    params: { escopo },
  });
  return data.dados;
}

export async function cancelarAula(
  id: number | string,
  payload: { motivo?: string | null; repor?: boolean },
  escopo: Escopo = 'esta',
) {
  const { data } = await api.post<Resposta<AulaDetalheApi>>(`/aulas/${id}/cancelar`, payload, {
    params: { escopo },
  });
  return data.dados;
}

// Mensagem legível a partir do erro do Axios.
export function mensagemDeErro(erro: unknown, padrao = 'Não foi possível concluir a operação.') {
  const dados = (erro as any)?.response?.data;
  if (!dados) return padrao;

  // 422: { erros: [{ local, tipo, mensagem }] }
  if (Array.isArray(dados.erros) && dados.erros.length > 0) {
    const msgs = dados.erros.map((e: any) => e?.mensagem).filter(Boolean);
    if (msgs.length) return msgs.join(' | ');
  }

  // 404/409: { detail: '...' }
  if (typeof dados.detail === 'string') return dados.detail;

  return typeof dados.mensagem === 'string' ? dados.mensagem : padrao;
}