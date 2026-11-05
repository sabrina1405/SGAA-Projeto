import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

import { MenuLateral } from './components/menu-lateral';

type MenuContextValue = {
  aberto: boolean;
  abrir: () => void;
  fechar: () => void;
};

const MenuContext = createContext<MenuContextValue | null>(null);

export function useMenu() {
  const ctx = useContext(MenuContext);
  if (!ctx) throw new Error('useMenu precisa estar dentro de <MenuProvider>.');
  return ctx;
}

// Coloque em volta do navegador (ex.: professor/_layout.tsx).
export function MenuProvider({ children }: { children: ReactNode }) {
  const [aberto, setAberto] = useState(false);
  const abrir = useCallback(() => setAberto(true), []);
  const fechar = useCallback(() => setAberto(false), []);
  const value = useMemo(() => ({ aberto, abrir, fechar }), [aberto, abrir, fechar]);

  return (
    <MenuContext.Provider value={value}>
      {children}
      <MenuLateral />
    </MenuContext.Provider>
  );
}