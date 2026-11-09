import { Platform } from 'react-native';
import { fetch as expoFetch } from 'expo/fetch';
import { File as ExpoFile } from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';
import type { DocumentPickerAsset } from 'expo-document-picker';

const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? 'http://10.0.2.2:8000/v1'
).replace(/\/+$/, '');
const ACCESS_TOKEN_KEY = 'sgaa-access-token';
const API_URL = new URL(API_BASE_URL);
let webAccessToken: string | null = null;
let legacyWebTokenRemoved = false;
const unauthorizedListeners = new Set<() => void>();

if (process.env.NODE_ENV === 'production' && API_URL.protocol !== 'https:') {
  throw new Error('EXPO_PUBLIC_API_URL deve usar HTTPS em produção.');
}

export class ApiRequestError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

interface ApiEnvelope<T> {
  mensagem: string;
  dados: T;
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  body?: unknown;
  authenticated?: boolean;
  accessToken?: string;
}

export interface UsuarioApi {
  id: number;
  nome_completo: string;
  email: string;
  tipo: 'aluno' | 'professor';
}

export interface LoginApiResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  usuario: UsuarioApi;
}

export interface PerfilAlunoApi {
  data_nascimento: string;
  possui_responsavel: boolean;
  cpf: string | null;
  telefone: string | null;
  responsavel_nome: string | null;
  responsavel_cpf: string | null;
  responsavel_telefone: string | null;
}

export interface PerfilApiResponse {
  id: number;
  nome_completo: string;
  email: string;
  perfil: PerfilAlunoApi;
}

export interface PerfilAlunoAtualizacao {
  nome_completo?: string;
  telefone?: string;
  responsavel_nome?: string;
  responsavel_cpf?: string;
  responsavel_telefone?: string;
}

export type StatusApi = 'vencida' | 'proxima' | 'realizada';

export interface AulaApi {
  id: number | string;
  titulo: string;
  data_hora: string;
  descricao: string;
  nome_aluno?: string | null;
  status: StatusApi;
  cancelada?: boolean;
  motivo_cancelamento?: string | null;
}

export type StatusAulaBackendApi = 'agendada' | 'realizada' | 'cancelada';

export interface AulaAgendaApi {
  id: number;
  titulo: string;
  inicio: string;
  fim: string;
  descricao: string | null;
  status: StatusAulaBackendApi;
  motivo_cancelamento: string | null;
  participacao?: 'ativa' | 'cancelada';
  professor_nome?: string;
  alunos?: { id: number; nome_completo: string; status: 'ativa' | 'cancelada' }[];
}

interface AulaListaBackendApi {
  id: number;
  titulo: string;
  inicio: string;
  fim: string;
  status: StatusAulaBackendApi;
  alunos: { id: number; nome_completo: string; status: 'ativa' | 'cancelada' }[];
}

interface AgendaBackendApi extends AulaAgendaApi {
  participacao: 'ativa' | 'cancelada';
  professor_nome: string;
}

interface AulaDetalheBackendApi {
  id: number;
  titulo: string;
  descricao: string | null;
  inicio: string;
  fim: string;
  status: StatusAulaBackendApi;
  motivo_cancelamento: string | null;
  alunos: {
    id: number;
    nome_completo: string;
    email: string;
    telefone: string;
    status: 'ativa' | 'cancelada';
    motivo_cancelamento: string | null;
    repor: boolean;
  }[];
}

export interface AtividadeApi {
  id: number | string;
  titulo: string;
  data_hora: string;
  descricao: string;
  nome_aluno?: string | null;
  status: StatusApi;
}

export type StatusEntregaApi = 'enviado' | 'entregue_com_atraso';

export interface ArquivoAtividadeApi {
  id: number;
  nome: string;
  tipo_mime: string;
  tamanho: number;
  url: string | null;
}

export interface EntregaAtividadeApi {
  atividade_id: number;
  aluno_id: number;
  resposta: string;
  status: StatusEntregaApi;
  enviada_em: string;
  anexos: ArquivoAtividadeApi[];
}

interface SessaoArquivoApi {
  arquivo_id: number;
  url_upload: string;
}

interface SalvarEntregaApi {
  resposta: string;
  arquivo_ids: number[];
}

export interface MinhaAtividadeApi {
  id: number;
  titulo: string;
  liberar_em: string;
  vence_em: string;
  permite_envio_arquivo: boolean;
  professor_nome: string;
  status: StatusEntregaApi | null;
  enviada_em: string | null;
}

export interface MinhaAtividadeDetalheApi extends MinhaAtividadeApi {
  descricao: string;
  criado_em: string;
  anexos: ArquivoAtividadeApi[];
  entrega: EntregaAtividadeApi | null;
}

export interface PagamentoApi {
  id: number | string;
  titulo: string;
  descricao?: string | null;
  data_vencimento: string;
  valor: number;
  status: StatusApi;
  nome_aluno?: string | null;
}

type SituacaoCobrancaApi = 'pendente' | 'vencida' | 'paga' | 'cancelada';

interface CobrancaApi {
  id: number;
  descricao: string;
  valor_centavos: number;
  vencimento: string;
  situacao: SituacaoCobrancaApi;
}

interface PaginaApi<T> {
  itens: T[];
  total: number;
}

export interface HomeApiResponse {
  usuario: UsuarioApi;
  aulas: AulaApi[];
  atividades: AtividadeApi[];
  pagamentos: PagamentoApi[];
}

async function getAccessToken(): Promise<string | null> {
  if (Platform.OS === 'web') {
    removeLegacyWebToken();
    return webAccessToken;
  }

  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

async function storeAccessToken(token: string): Promise<void> {
  if (Platform.OS === 'web') {
    removeLegacyWebToken();
    webAccessToken = token;
    return;
  }

  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
}

function removeLegacyWebToken(): void {
  if (legacyWebTokenRemoved) return;
  globalThis.localStorage?.removeItem(ACCESS_TOKEN_KEY);
  legacyWebTokenRemoved = true;
}

export async function clearAccessToken(): Promise<void> {
  if (Platform.OS === 'web') {
    webAccessToken = null;
    removeLegacyWebToken();
    return;
  }

  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
}

export async function hasAccessToken(): Promise<boolean> {
  return Boolean(await getAccessToken());
}

export function subscribeToUnauthorized(listener: () => void): () => void {
  unauthorizedListeners.add(listener);
  return () => unauthorizedListeners.delete(listener);
}

export async function requestApi<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const token = options.accessToken
    ?? (options.authenticated === false ? null : await getAccessToken());
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers: {
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(options.body === undefined ? {} : { body: JSON.stringify(options.body) }),
  });

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiRequestError(
      'A API retornou uma resposta inválida.',
      response.status,
    );
  }

  if (!response.ok) {
    const detail = payload && typeof payload === 'object' && 'detail' in payload
      ? (payload as { detail?: unknown }).detail
      : null;
    const message = typeof detail === 'string'
      ? detail
      : `Não foi possível concluir a solicitação (HTTP ${response.status}).`;

    if (response.status === 401) {
      unauthorizedListeners.forEach((listener) => listener());
      await clearAccessToken();
    }

    throw new ApiRequestError(message, response.status);
  }

  if (!payload || typeof payload !== 'object' || !('dados' in payload)) {
    throw new ApiRequestError('A resposta da API não contém o campo "dados".', response.status);
  }

  return (payload as ApiEnvelope<T>).dados;
}

export async function entrar(
  email: string,
  senha: string,
  perfilEsperado: UsuarioApi['tipo'],
): Promise<UsuarioApi> {
  await clearAccessToken();
  const response = await requestApi<LoginApiResponse>('/auth/login', {
    method: 'POST',
    body: { email, senha },
    authenticated: false,
  });
  if (!response.access_token || response.token_type !== 'bearer') {
    throw new ApiRequestError('A API retornou um token de acesso inválido.', 502);
  }
  if (response.usuario.tipo !== perfilEsperado) {
    throw new ApiRequestError(
      'O perfil selecionado não corresponde a esta conta.',
      403,
    );
  }
  await storeAccessToken(response.access_token);
  return response.usuario;
}

export function obterUsuarioAtual(): Promise<UsuarioApi> {
  return requestApi<UsuarioApi>('/auth/me');
}

export function obterPerfilAluno(): Promise<PerfilApiResponse> {
  return requestApi<PerfilApiResponse>('/auth/me/perfil');
}

export function atualizarPerfilAluno(
  dados: PerfilAlunoAtualizacao,
): Promise<PerfilApiResponse> {
  return requestApi<PerfilApiResponse>('/auth/me/perfil', {
    method: 'PATCH',
    body: dados,
  });
}

export function obterAulas(): Promise<AulaApi[]> {
  return requestApi<AulaApi[]>('/aulas');
}

function formatarAulaAgenda(
  tipoUsuario: UsuarioApi['tipo'],
  aula: AgendaBackendApi | AulaListaBackendApi | AulaDetalheBackendApi,
): AulaAgendaApi {
  if (tipoUsuario === 'aluno') {
    const agenda = aula as AgendaBackendApi;
    return {
      id: agenda.id,
      titulo: agenda.titulo,
      inicio: agenda.inicio,
      fim: agenda.fim,
      descricao: agenda.descricao,
      status: agenda.status,
      motivo_cancelamento: agenda.motivo_cancelamento,
      participacao: agenda.participacao,
      professor_nome: agenda.professor_nome,
    };
  }

  const aulaProfessor = aula as AulaListaBackendApi | AulaDetalheBackendApi;
  return {
    id: aulaProfessor.id,
    titulo: aulaProfessor.titulo,
    inicio: aulaProfessor.inicio,
    fim: aulaProfessor.fim,
    descricao: 'descricao' in aulaProfessor ? aulaProfessor.descricao : null,
    status: aulaProfessor.status,
    motivo_cancelamento: 'motivo_cancelamento' in aulaProfessor
      ? aulaProfessor.motivo_cancelamento
      : null,
    alunos: aulaProfessor.alunos.map((aluno) => ({
      id: aluno.id,
      nome_completo: aluno.nome_completo,
      status: aluno.status,
    })),
  };
}

export async function obterAgenda(
  tipoUsuario: UsuarioApi['tipo'],
  dataInicio: string,
  dataFim: string,
): Promise<AulaAgendaApi[]> {
  const path = tipoUsuario === 'aluno' ? '/agenda' : '/aulas';
  const aulas = await requestApi<(AgendaBackendApi | AulaListaBackendApi)[]>(
    `${path}?data_inicio=${dataInicio}&data_fim=${dataFim}`,
  );
  return aulas.map((aula) => formatarAulaAgenda(tipoUsuario, aula));
}

export async function obterDetalheAgendamento(
  tipoUsuario: UsuarioApi['tipo'],
  aulaId: number,
): Promise<AulaAgendaApi> {
  const path = tipoUsuario === 'aluno' ? '/agenda' : '/aulas';
  const aula = await requestApi<AgendaBackendApi | AulaDetalheBackendApi>(
    `${path}/${aulaId}`,
  );
  return formatarAulaAgenda(tipoUsuario, aula);
}

export async function cancelarAgendamento(
  tipoUsuario: UsuarioApi['tipo'],
  aulaId: number,
  motivo: string,
): Promise<void> {
  if (tipoUsuario === 'aluno') {
    await requestApi<AulaAgendaApi>(`/agenda/${aulaId}/cancelar`, {
      method: 'POST',
      body: { motivo },
    });
    return;
  }

  await requestApi<AulaDetalheBackendApi>(`/aulas/${aulaId}/cancelar?escopo=esta`, {
    method: 'POST',
    body: { motivo, repor: false },
  });
}

export async function remarcarAula(
  aulaId: number,
  inicio: string,
  fim: string,
): Promise<AulaAgendaApi> {
  const aula = await requestApi<AulaDetalheBackendApi>(
    `/aulas/${aulaId}?escopo=esta`,
    {
      method: 'PATCH',
      body: { inicio, fim },
    },
  );
  return formatarAulaAgenda('professor', aula);
}

export function obterAtividades(): Promise<AtividadeApi[]> {
  return requestApi<AtividadeApi[]>('/atividades');
}

export async function obterMinhasAtividades(): Promise<MinhaAtividadeApi[]> {
  const tamanhoPagina = 100;
  const maximoPaginas = 500;
  const primeiraPagina = await requestApi<PaginaApi<MinhaAtividadeApi>>(
    `/minhas-atividades?pagina=1&tamanho=${tamanhoPagina}`,
  );
  const totalPaginas = Math.ceil(primeiraPagina.total / tamanhoPagina);

  if (totalPaginas > maximoPaginas) {
    throw new ApiRequestError('A API retornou mais atividades do que é possível carregar.', 502);
  }

  const atividades = [...primeiraPagina.itens];
  for (let pagina = 2; pagina <= totalPaginas; pagina += 1) {
    const resultado = await requestApi<PaginaApi<MinhaAtividadeApi>>(
      `/minhas-atividades?pagina=${pagina}&tamanho=${tamanhoPagina}`,
    );
    atividades.push(...resultado.itens);
  }

  return atividades;
}

export function obterMinhaAtividade(
  atividadeId: number,
): Promise<MinhaAtividadeDetalheApi> {
  return requestApi<MinhaAtividadeDetalheApi>(`/minhas-atividades/${atividadeId}`);
}

async function descartarArquivoAtividade(arquivoId: number): Promise<void> {
  await requestApi<null>(`/arquivos/${arquivoId}`, { method: 'DELETE' });
}

async function enviarArquivoAtividade(
  asset: DocumentPickerAsset,
): Promise<ArquivoAtividadeApi> {
  const nome = asset.name.trim();
  const tipoMime = asset.mimeType?.trim() || 'application/octet-stream';
  const arquivo = asset.file ?? new ExpoFile(asset.uri);
  const tamanho = asset.size ?? arquivo.size;

  if (!nome || nome.length > 150) {
    throw new ApiRequestError('O nome de um arquivo excede o limite aceito pela API.', 400);
  }
  if (tipoMime.length > 100) {
    throw new ApiRequestError('O tipo de um arquivo excede o limite aceito pela API.', 400);
  }
  if (!Number.isSafeInteger(tamanho) || tamanho <= 0) {
    throw new ApiRequestError(`O arquivo "${nome}" está vazio ou tem tamanho inválido.`, 400);
  }

  const sessao = await requestApi<SessaoArquivoApi>('/arquivos/sessao', {
    method: 'POST',
    body: { nome, tipo_mime: tipoMime, tamanho },
  });

  try {
    const upload = await expoFetch(sessao.url_upload, {
      method: 'PUT',
      headers: { 'Content-Type': tipoMime },
      body: arquivo,
    });

    if (!upload.ok) {
      throw new ApiRequestError(
        `Não foi possível enviar "${nome}" (HTTP ${upload.status}).`,
        upload.status,
      );
    }

    let dadosUpload: unknown;
    try {
      dadosUpload = await upload.json();
    } catch {
      throw new ApiRequestError(
        `A resposta de upload de "${nome}" é inválida.`,
        upload.status,
      );
    }

    const driveFileId = dadosUpload && typeof dadosUpload === 'object'
      && 'id' in dadosUpload && typeof dadosUpload.id === 'string'
      ? dadosUpload.id
      : null;
    if (!driveFileId) {
      throw new ApiRequestError(
        `A resposta de upload de "${nome}" não contém o identificador do arquivo.`,
        upload.status,
      );
    }

    return requestApi<ArquivoAtividadeApi>(
      `/arquivos/${sessao.arquivo_id}/confirmar`,
      { method: 'POST', body: { drive_file_id: driveFileId } },
    );
  } catch (error) {
    try {
      await descartarArquivoAtividade(sessao.arquivo_id);
    } catch (cleanupError) {
      console.error(`Não foi possível descartar o arquivo "${nome}" após falha no upload:`, cleanupError);
    }
    throw error;
  }
}

export async function enviarEntregaAtividade(
  atividadeId: number,
  resposta: string,
  anexos: DocumentPickerAsset[],
  permiteEnvioArquivo: boolean,
  arquivoIdsExistentes: number[] = [],
): Promise<EntregaAtividadeApi> {
  const respostaNormalizada = resposta.trim();
  if (!respostaNormalizada) {
    throw new ApiRequestError('Escreva uma resposta antes de enviar a atividade.', 400);
  }
  if (respostaNormalizada.length > 5000) {
    throw new ApiRequestError('A resposta não pode ultrapassar 5000 caracteres.', 400);
  }
  if (anexos.length > 0 && !permiteEnvioArquivo) {
    throw new ApiRequestError('Esta atividade não permite anexar arquivos.', 400);
  }

  const arquivosEnviados: ArquivoAtividadeApi[] = [];
  try {
    for (const anexo of anexos) {
      arquivosEnviados.push(await enviarArquivoAtividade(anexo));
    }
  } catch (error) {
    await Promise.all(
      arquivosEnviados.map(async (arquivo) => {
        try {
          await descartarArquivoAtividade(arquivo.id);
        } catch (cleanupError) {
          console.error(`Não foi possível descartar o arquivo ${arquivo.id}:`, cleanupError);
        }
      }),
    );
    throw error;
  }

  const body: SalvarEntregaApi = {
    resposta: respostaNormalizada,
    arquivo_ids: [
      ...arquivoIdsExistentes,
      ...arquivosEnviados.map((arquivo) => arquivo.id),
    ],
  };
  return requestApi<EntregaAtividadeApi>(
    `/minhas-atividades/${atividadeId}/entrega`,
    { method: 'PUT', body },
  );
}

export async function obterPagamentos(): Promise<PagamentoApi[]> {
  const tamanhoPagina = 100;
  const maximoPaginas = 500;
  const primeiraPagina = await requestApi<PaginaApi<CobrancaApi>>(
    `/minhas-cobrancas?pagina=1&tamanho=${tamanhoPagina}`,
  );
  const totalPaginas = Math.ceil(primeiraPagina.total / tamanhoPagina);

  if (totalPaginas > maximoPaginas) {
    throw new ApiRequestError('A API retornou mais cobranças do que é possível carregar.', 502);
  }

  const cobrancas = [...primeiraPagina.itens];
  for (let pagina = 2; pagina <= totalPaginas; pagina += 1) {
    const resultado = await requestApi<PaginaApi<CobrancaApi>>(
      `/minhas-cobrancas?pagina=${pagina}&tamanho=${tamanhoPagina}`,
    );
    cobrancas.push(...resultado.itens);
  }

  return cobrancas.flatMap((cobranca): PagamentoApi[] => {
    if (cobranca.situacao === 'cancelada') {
      return [];
    }

    return [{
      id: cobranca.id,
      titulo: cobranca.descricao,
      data_vencimento: cobranca.vencimento,
      valor: cobranca.valor_centavos / 100,
      status: cobranca.situacao === 'paga'
        ? 'realizada'
        : cobranca.situacao === 'pendente'
          ? 'proxima'
          : 'vencida',
    }];
  });
}

export async function obterDadosHome(): Promise<HomeApiResponse> {
  const [usuario, aulas, atividades, pagamentos] = await Promise.all([
    obterUsuarioAtual(),
    obterAulas(),
    obterAtividades(),
    obterPagamentos(),
  ]);

  return { usuario, aulas, atividades, pagamentos };
}
