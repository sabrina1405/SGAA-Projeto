import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/v1'
).replace(/\/+$/, '');
const ACCESS_TOKEN_KEY = 'sgaa-access-token';

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

export interface AtividadeApi {
  id: number | string;
  titulo: string;
  data_hora: string;
  descricao: string;
  nome_aluno?: string | null;
  status: StatusApi;
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

export interface HomeApiResponse {
  usuario: UsuarioApi;
  aulas: AulaApi[];
  atividades: AtividadeApi[];
  pagamentos: PagamentoApi[];
}

async function getAccessToken(): Promise<string | null> {
  if (Platform.OS === 'web') {
    return globalThis.localStorage?.getItem(ACCESS_TOKEN_KEY) ?? null;
  }

  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

async function storeAccessToken(token: string): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.setItem(ACCESS_TOKEN_KEY, token);
    return;
  }

  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
}

export async function clearAccessToken(): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.removeItem(ACCESS_TOKEN_KEY);
    return;
  }

  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
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

export function obterAtividades(): Promise<AtividadeApi[]> {
  return requestApi<AtividadeApi[]>('/atividades');
}

export function obterPagamentos(): Promise<PagamentoApi[]> {
  return requestApi<PagamentoApi[]>('/financeiro/transacoes');
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
