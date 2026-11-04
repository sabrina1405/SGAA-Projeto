import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { aoExpirarSessao } from '@/services/api';
import { obterToken } from '@/services/tokenStorage';

import { logout, usuarioAtual } from './authService';
import type { Usuario } from './types';

type Estado = 'carregando' | 'autenticado' | 'anonimo';

type Sessao = {
  estado: Estado;
  usuario: Usuario | null;
  // Chame depois de um login bem-sucedido.
  iniciarSessao: (usuario: Usuario) => void;
  // Apaga o token e volta ao estado anônimo.
  encerrarSessao: () => Promise<void>;
};

const SessaoContext = createContext<Sessao | null>(null);

export function SessaoProvider({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<Estado>('carregando');
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  // Ao abrir o app: se há token salvo, confere com o servidor (GET /auth/me).
  useEffect(() => {
    let ativo = true;

    async function restaurar() {
      try {
        const token = await obterToken();
        if (!token) throw new Error('sem token');
        const atual = await usuarioAtual();
        if (!ativo) return;
        setUsuario(atual);
        setEstado('autenticado');
      } catch {
        if (!ativo) return;
        setUsuario(null);
        setEstado('anonimo');
      }
    }

    restaurar();
    return () => {
      ativo = false;
    };
  }, []);

  // Token expirado durante o uso: volta ao estado anônimo.
  useEffect(() => {
    aoExpirarSessao(() => {
      setUsuario(null);
      setEstado('anonimo');
    });
    return () => aoExpirarSessao(null);
  }, []);

  const iniciarSessao = useCallback((novo: Usuario) => {
    setUsuario(novo);
    setEstado('autenticado');
  }, []);

  const encerrarSessao = useCallback(async () => {
    await logout();
    setUsuario(null);
    setEstado('anonimo');
  }, []);

  const valor = useMemo(
    () => ({ estado, usuario, iniciarSessao, encerrarSessao }),
    [estado, usuario, iniciarSessao, encerrarSessao],
  );

  return <SessaoContext.Provider value={valor}>{children}</SessaoContext.Provider>;
}

export function useSessao(): Sessao {
  const contexto = useContext(SessaoContext);
  if (!contexto) throw new Error('useSessao deve ser usado dentro de SessaoProvider');
  return contexto;
}