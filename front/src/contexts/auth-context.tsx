import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from 'react';
import {
  ApiRequestError,
  clearAccessToken,
  hasAccessToken,
  obterUsuarioAtual,
  subscribeToUnauthorized,
  type UsuarioApi,
} from '@/services/api';

type AuthStatus = 'checking' | 'authenticated' | 'unauthenticated' | 'error';

interface AuthContextValue {
  user: UsuarioApi | null;
  status: AuthStatus;
  signIn: (user: UsuarioApi) => void;
  signOut: () => Promise<void>;
  retry: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthSessionProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<UsuarioApi | null>(null);
  const [status, setStatus] = useState<AuthStatus>('checking');

  const checkSession = useCallback(async () => {
    try {
      if (!await hasAccessToken()) {
        setUser(null);
        setStatus('unauthenticated');
        return;
      }

      const currentUser = await obterUsuarioAtual();
      setUser(currentUser);
      setStatus('authenticated');
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        setUser(null);
        setStatus('unauthenticated');
        return;
      }

      console.error('Não foi possível validar a sessão:', error);
      setStatus('error');
    }
  }, []);

  const retry = useCallback(async () => {
    setStatus('checking');
    await checkSession();
  }, [checkSession]);

  useEffect(() => {
    const unsubscribe = subscribeToUnauthorized(() => {
      setUser(null);
      setStatus('unauthenticated');
    });
    void Promise.resolve().then(checkSession);
    return unsubscribe;
  }, [checkSession]);

  const signIn = useCallback((signedInUser: UsuarioApi) => {
    setUser(signedInUser);
    setStatus('authenticated');
  }, []);

  const signOut = useCallback(async () => {
    setUser(null);
    setStatus('unauthenticated');
    await clearAccessToken();
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, status, signIn, signOut, retry }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthSession(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthSession deve ser usado dentro de AuthSessionProvider.');
  }
  return context;
}
