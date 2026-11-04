import axios from 'axios';

import { obterToken, removerToken } from './tokenStorage';

// Web: http://localhost:8000
// Emulador Android: http://10.0.2.2:8000
// Celular físico: http://<IP-da-máquina>:8000 (API com --host 0.0.0.0)
const baseURL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/v1';

export const api = axios.create({ baseURL, timeout: 15000 });

// Envia o token em toda requisição, quando existir.
api.interceptors.request.use(async (config) => {
  const token = await obterToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Token expirado ou invalidado: limpa a sessão local.
// O 401 do próprio login (credenciais erradas) não conta.
api.interceptors.response.use(
  (resposta) => resposta,
  async (erro) => {
    if (erro.response?.status === 401 && erro.config?.url !== '/auth/login') {
      await removerToken();
    }
    return Promise.reject(erro);
  },
);