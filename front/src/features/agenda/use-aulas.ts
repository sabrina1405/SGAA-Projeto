import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';

import { listarAulas, mensagemDeErro } from './api';
import { aulaParaEvento } from './mappers';
import type { Evento } from './types';
import { chaveData } from './utils';

// Busca as aulas do mês exibido (mes: 0-11). Recarrega ao trocar de mês e
// sempre que a tela volta ao foco (depois de criar/editar/cancelar).
export function useAulas(ano: number, mes: number) {
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const ultimaBusca = useRef(0);

  const carregar = useCallback(async () => {
    const busca = ++ultimaBusca.current;
    setCarregando(true);
    setErro(null);
    try {
      const ultimoDia = new Date(ano, mes + 1, 0).getDate();
      const aulas = await listarAulas(chaveData(ano, mes, 1), chaveData(ano, mes, ultimoDia));
      if (busca === ultimaBusca.current) setEventos(aulas.map(aulaParaEvento));
    } catch (e) {
      if (busca === ultimaBusca.current) setErro(mensagemDeErro(e, 'Não foi possível carregar a agenda.'));
    } finally {
      if (busca === ultimaBusca.current) setCarregando(false);
    }
  }, [ano, mes]);

  useFocusEffect(
    useCallback(() => {
      carregar();
    }, [carregar]),
  );

  return { eventos, carregando, erro, recarregar: carregar };
}