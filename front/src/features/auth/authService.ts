import axios from 'axios';

import { api } from '@/services/api';
import { salvarToken } from '@/services/tokenStorage';

import type { LoginEntrada, Resposta, TokenResposta, Usuario } from './types';

export async function login({ email, senha }: LoginEntrada): Promise<Usuario> {
  const { data } = await api.post<Resposta<TokenResposta>>('/auth/login', {
    email: email.trim(),
    senha,
  });
  await salvarToken(data.dados.access_token);
  return data.dados.usuario;
}

// Valida o token salvo e devolve o usuário logado.
export async function usuarioAtual(): Promise<Usuario> {
  const { data } = await api.get<Resposta<Usuario>>('/auth/me');
  return data.dados;
}

// Converte o erro do Axios em uma mensagem para mostrar na tela.
export function mensagemDeErro(erro: unknown): string {
  if (axios.isAxiosError(erro)) {
    if (!erro.response) return 'Não foi possível conectar ao servidor.';
    if (erro.response.status === 422) return 'Confira o e-mail e a senha informados.';
    const detalhe = erro.response.data?.detail;
    if (typeof detalhe === 'string') return detalhe;
  }
  return 'Ocorreu um erro inesperado. Tente novamente.';
}