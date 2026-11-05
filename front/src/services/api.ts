import axios from 'axios';

import { obterToken, removerToken } from './tokenStorage';


const baseURL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/v1';

export const api = axios.create({ baseURL, timeout: 15000 });

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