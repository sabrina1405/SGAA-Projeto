import { create } from 'axios';
import { fetch as expoFetch } from 'expo/fetch';
import { File as ExpoFile } from 'expo-file-system';
import type { DocumentPickerAsset } from 'expo-document-picker';

import { obterToken, removerToken } from './tokenStorage';


const baseURL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/v1';

export const api = create({ baseURL, timeout: 15000 });

// Permite que a sessão (SessaoContext) seja avisada quando o token deixa de valer.
let aoExpirar: (() => void) | null = null;
export function aoExpirarSessao(funcao: (() => void) | null) {
  aoExpirar = funcao;
}

// Envia o token em toda requisição, quando existir.
api.interceptors.request.use(async (config) => {
  const token = await obterToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Token expirado ou invalidado: limpa a sessão local e avisa o app.
// O 401 do próprio login (credenciais erradas) não conta.
api.interceptors.response.use(
  (resposta) => resposta,
  async (erro) => {
    if (erro.response?.status === 401 && erro.config?.url !== '/auth/login') {
      await removerToken();
      aoExpirar?.();
    }
    return Promise.reject(erro);
  },
);

export type StatusApi = 'vencida' | 'proxima' | 'realizada';

export interface UsuarioApi {
  id: number;
  nome_completo: string;
  email: string;
  tipo: 'aluno' | 'professor';
}

export interface AulaApi {
  id: number | string;
  titulo: string;
  data_hora: string;
  descricao: string;
  nome_aluno: string | null;
  status: StatusApi;
}

export interface AtividadeApi {
  id: number | string;
  titulo: string;
  data_hora: string;
  descricao: string;
  nome_aluno: string | null;
  status: StatusApi;
}

export interface PagamentoApi {
  id: number | string;
  titulo: string;
  descricao: string | null;
  data_vencimento: string;
  nome_aluno: string | null;
  status: StatusApi;
  valor: number;
}

export type SituacaoCobrancaApi = 'pendente' | 'vencida' | 'paga' | 'cancelada';

export interface MinhaCobrancaApi {
  id: number;
  descricao: string;
  valor_centavos: number;
  vencimento: string;
  situacao: SituacaoCobrancaApi;
  paga_em: string | null;
  professor_nome: string;
  chave_pix: string | null;
}

export interface HomeApiResponse {
  usuario: UsuarioApi;
  aulas: AulaApi[];
  atividades: AtividadeApi[];
  pagamentos: PagamentoApi[];
}

const TAMANHO_PAGINA_COBRANCAS = 100;

export async function obterMinhasCobrancas(): Promise<MinhaCobrancaApi[]> {
  const cobrancas: MinhaCobrancaApi[] = [];
  let total = Number.POSITIVE_INFINITY;
  let pagina = 1;

  while (cobrancas.length < total) {
    const { data } = await api.get<{
      dados: { itens: MinhaCobrancaApi[]; total: number };
    }>('/minhas-cobrancas', {
      params: { pagina, tamanho: TAMANHO_PAGINA_COBRANCAS },
    });

    cobrancas.push(...data.dados.itens);
    total = data.dados.total;
    if (data.dados.itens.length === 0 && cobrancas.length < total) {
      throw new Error('A API retornou uma página vazia antes do fim das cobranças.');
    }
    pagina += 1;
  }

  return cobrancas;
}

function statusPorData(data: string, concluida = false): StatusApi {
  if (concluida) return 'realizada';
  const vencimento = new Date(data);
  return Number.isNaN(vencimento.getTime()) || vencimento < new Date()
    ? 'vencida'
    : 'proxima';
}

export async function obterDadosHome(): Promise<HomeApiResponse> {
  const { data: respostaUsuario } = await api.get<{
    dados: UsuarioApi;
  }>('/auth/me');
  const usuario = respostaUsuario.dados;

  if (usuario.tipo !== 'aluno') {
    return { usuario, aulas: [], atividades: [], pagamentos: [] };
  }

  const hoje = new Date();
  const dataFim = new Date(hoje);
  dataFim.setDate(dataFim.getDate() + 60);
  const formatoData = (valor: Date) => valor.toISOString().slice(0, 10);

  const [{ data: respostaAgenda }, { data: respostaAtividades }, cobrancas] =
    await Promise.all([
      api.get<{ dados: {
        id: number;
        titulo: string;
        descricao: string | null;
        inicio: string;
        status: 'agendada' | 'realizada' | 'cancelada';
        participacao: 'ativa' | 'cancelada';
        professor_nome: string;
      }[] }>(`/agenda?data_inicio=${formatoData(hoje)}&data_fim=${formatoData(dataFim)}`),
      api.get<{ dados: {
        itens: {
          id: number;
          titulo: string;
          vence_em: string;
          professor_nome: string;
          status: string | null;
          enviada_em: string | null;
        }[];
        total: number;
      } }>('/minhas-atividades'),
      obterMinhasCobrancas(),
    ]);

  const aulas: AulaApi[] = respostaAgenda.dados
    .filter((aula) => aula.status !== 'cancelada' && aula.participacao !== 'cancelada')
    .map((aula) => ({
      id: aula.id,
      titulo: aula.titulo,
      data_hora: aula.inicio,
      descricao: aula.descricao ?? '',
      nome_aluno: null,
      status: aula.status === 'realizada'
        ? 'realizada'
        : statusPorData(aula.inicio),
    }));

  const atividades: AtividadeApi[] = respostaAtividades.dados.itens.map((atividade) => ({
    id: atividade.id,
    titulo: atividade.titulo,
    data_hora: atividade.vence_em,
    descricao: `Professor(a): ${atividade.professor_nome}`,
    nome_aluno: null,
    status: atividade.enviada_em
      ? 'realizada'
      : statusPorData(atividade.vence_em),
  }));

  const pagamentos: PagamentoApi[] = cobrancas
    .filter((cobranca) => cobranca.situacao !== 'cancelada')
    .map((cobranca) => ({
      id: cobranca.id,
      titulo: cobranca.descricao,
      descricao: `Professor(a): ${cobranca.professor_nome}`,
      data_vencimento: cobranca.vencimento,
      nome_aluno: null,
      status: cobranca.situacao === 'paga'
        ? 'realizada'
        : cobranca.situacao === 'vencida'
          ? 'vencida'
          : 'proxima',
      valor: cobranca.valor_centavos / 100,
    }));

  return { usuario, aulas, atividades, pagamentos };
}

export type AulaAgendaApi = {
  id: number;
  titulo: string;
  descricao: string | null;
  inicio: string;
  fim: string;
  status: 'agendada' | 'realizada' | 'cancelada';
  participacao: 'ativa' | 'cancelada';
  motivo_cancelamento: string | null;
  professor_nome: string;
  alunos?: { id: number; nome_completo: string; status: 'ativa' | 'cancelada' }[];
};

export async function obterAgenda(
  tipoUsuario: UsuarioApi['tipo'],
  dataInicio: string,
  dataFim: string,
): Promise<AulaAgendaApi[]> {
  if (tipoUsuario !== 'aluno') {
    throw new Error('Esta agenda é exclusiva para alunos.');
  }
  const { data } = await api.get<{ dados: AulaAgendaApi[] }>('/agenda', {
    params: { data_inicio: dataInicio, data_fim: dataFim },
  });
  return data.dados;
}

export type ArquivoAtividadeApi = {
  id: number;
  nome: string;
  tipo_mime: string;
  tamanho: number;
  url: string | null;
};

export type EntregaAtividadeApi = {
  atividade_id: number;
  aluno_id: number;
  resposta: string;
  status: 'enviado' | 'entregue_com_atraso';
  enviada_em: string;
  anexos: ArquivoAtividadeApi[];
};

export type MinhaAtividadeApi = {
  id: number;
  titulo: string;
  liberar_em: string;
  vence_em: string;
  permite_envio_arquivo: boolean;
  professor_nome: string;
  status: 'enviado' | 'entregue_com_atraso' | null;
  enviada_em: string | null;
};

export type MinhaAtividadeDetalheApi = MinhaAtividadeApi & {
  descricao: string;
  criado_em: string;
  anexos: ArquivoAtividadeApi[];
  entrega: EntregaAtividadeApi | null;
};

type PaginaApi<T> = { itens: T[]; total: number };

export async function obterMinhasAtividades(): Promise<MinhaAtividadeApi[]> {
  const tamanho = 100;
  const { data } = await api.get<{ dados: PaginaApi<MinhaAtividadeApi> }>(
    '/minhas-atividades',
    { params: { pagina: 1, tamanho } },
  );
  const atividades = [...data.dados.itens];
  const paginas = Math.ceil(data.dados.total / tamanho);

  for (let pagina = 2; pagina <= paginas; pagina += 1) {
    const { data: resposta } = await api.get<{ dados: PaginaApi<MinhaAtividadeApi> }>(
      '/minhas-atividades',
      { params: { pagina, tamanho } },
    );
    atividades.push(...resposta.dados.itens);
  }
  return atividades;
}

export async function obterMinhaAtividade(
  atividadeId: number,
): Promise<MinhaAtividadeDetalheApi> {
  const { data } = await api.get<{ dados: MinhaAtividadeDetalheApi }>(
    `/minhas-atividades/${atividadeId}`,
  );
  return data.dados;
}

type SessaoArquivoApi = { arquivo_id: number; url_upload: string };

async function enviarArquivoAtividade(
  asset: DocumentPickerAsset,
): Promise<ArquivoAtividadeApi> {
  const nome = asset.name.trim();
  const tipoMime = asset.mimeType?.trim() || 'application/octet-stream';
  const arquivo = asset.file ?? new ExpoFile(asset.uri);
  const tamanho = asset.size ?? arquivo.size;

  if (
    !nome ||
    nome.length > 150 ||
    tipoMime.length > 100 ||
    !Number.isSafeInteger(tamanho) ||
    tamanho <= 0
  ) {
    throw new Error(`O arquivo "${nome || 'sem nome'}" tem dados inválidos.`);
  }

  const { data: respostaSessao } = await api.post<{ dados: SessaoArquivoApi }>(
    '/arquivos/sessao',
    { nome, tipo_mime: tipoMime, tamanho },
  );
  const upload = await expoFetch(respostaSessao.dados.url_upload, {
    method: 'PUT',
    headers: { 'Content-Type': tipoMime },
    body: arquivo,
  });
  if (!upload.ok) {
    throw new Error(`Não foi possível enviar "${nome}" (HTTP ${upload.status}).`);
  }

  const dadosUpload: unknown = await upload.json();
  const driveFileId =
    dadosUpload && typeof dadosUpload === 'object' && 'id' in dadosUpload
      ? dadosUpload.id
      : null;
  if (typeof driveFileId !== 'string' || !driveFileId) {
    throw new Error(`O upload de "${nome}" não retornou o identificador do arquivo.`);
  }

  const { data } = await api.post<{ dados: ArquivoAtividadeApi }>(
    `/arquivos/${respostaSessao.dados.arquivo_id}/confirmar`,
    { drive_file_id: driveFileId },
  );
  return data.dados;
}

export async function enviarEntregaAtividade(
  atividadeId: number,
  resposta: string,
  anexos: DocumentPickerAsset[],
  permiteEnvioArquivo: boolean,
  arquivoIdsExistentes: number[] = [],
): Promise<EntregaAtividadeApi> {
  const respostaNormalizada = resposta.trim();
  if (!respostaNormalizada) throw new Error('Escreva uma resposta antes de enviar.');
  if (respostaNormalizada.length > 5000) throw new Error('A resposta excede 5000 caracteres.');
  if (anexos.length > 0 && !permiteEnvioArquivo) {
    throw new Error('Esta atividade não permite anexar arquivos.');
  }
  if (anexos.length + arquivoIdsExistentes.length > 3) {
    throw new Error('Uma entrega pode conter no máximo 3 arquivos.');
  }

  const arquivosEnviados: ArquivoAtividadeApi[] = [];
  try {
    for (const anexo of anexos) {
      arquivosEnviados.push(await enviarArquivoAtividade(anexo));
    }

    const { data } = await api.put<{ dados: EntregaAtividadeApi }>(
      `/minhas-atividades/${atividadeId}/entrega`,
      {
        resposta: respostaNormalizada,
        arquivo_ids: [
          ...arquivoIdsExistentes,
          ...arquivosEnviados.map((arquivo) => arquivo.id),
        ],
      },
    );
    return data.dados;
  } catch (erro) {
    await Promise.all(
      arquivosEnviados.map(async (arquivo) => {
        try {
          await api.delete(`/arquivos/${arquivo.id}`);
        } catch (erroLimpeza) {
          console.error(`Não foi possível descartar o arquivo ${arquivo.id}:`, erroLimpeza);
        }
      }),
    );
    throw erro;
  }
}

export type PerfilAlunoApi = {
  data_nascimento: string;
  possui_responsavel: boolean;
  cpf: string | null;
  telefone: string | null;
  responsavel_nome: string | null;
  responsavel_cpf: string | null;
  responsavel_telefone: string | null;
};

export type PerfilApiResponse = {
  id: number;
  nome_completo: string;
  email: string;
  perfil: PerfilAlunoApi;
};

export async function obterPerfilAluno(): Promise<PerfilApiResponse> {
  const { data } = await api.get<{ dados: PerfilApiResponse }>('/auth/me/perfil');
  return data.dados;
}

export async function atualizarPerfilAluno(
  payload: Record<string, string>,
): Promise<PerfilApiResponse> {
  const { data } = await api.patch<{ dados: PerfilApiResponse }>(
    '/auth/me/perfil',
    payload,
  );
  return data.dados;
}
