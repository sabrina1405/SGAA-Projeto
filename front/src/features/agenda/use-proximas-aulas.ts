import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';

import { listarAulas } from './api';
import { aulaParaEvento } from './mappers';
import { chaveData } from './utils';

export type ProximaAula = {
  id: string;
  titulo: string;
  aluno: string;
  quando: string; // '25/11 às 10:00'
};

const dois = (n: number) => String(n).padStart(2, '0');

// Próximas aulas agendadas a partir de agora (olha os próximos 45 dias).
// Recarrega sempre que a tela volta ao foco, então uma aula criada na agenda aparece aqui.
export function useProximasAulas(limite = 3) {
  const [aulas, setAulas] = useState<ProximaAula[]>([]);
  const [carregando, setCarregando] = useState(true);

  useFocusEffect(
    useCallback(() => {
      let ativo = true;

      (async () => {
        try {
          const agora = new Date();
          const fim = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate() + 45);
          const lista = await listarAulas(
            chaveData(agora.getFullYear(), agora.getMonth(), agora.getDate()),
            chaveData(fim.getFullYear(), fim.getMonth(), fim.getDate()),
            'agendada',
          );

          const limiteAgora = `${chaveData(agora.getFullYear(), agora.getMonth(), agora.getDate())} ${dois(
            agora.getHours(),
          )}:${dois(agora.getMinutes())}`;

          const proximas = lista
            .map((aula) => ({ aula, evento: aulaParaEvento(aula) }))
            .filter(({ evento }) => `${evento.data} ${evento.inicio}` >= limiteAgora)
            .sort((a, b) =>
              `${a.evento.data} ${a.evento.inicio}`.localeCompare(`${b.evento.data} ${b.evento.inicio}`),
            )
            .slice(0, limite)
            .map(({ aula, evento }) => ({
              id: evento.id,
              titulo: aula.titulo,
              aluno: evento.aluno,
              quando: `${evento.data.slice(8, 10)}/${evento.data.slice(5, 7)} às ${evento.inicio}`,
            }));

          if (ativo) setAulas(proximas);
        } catch {
          if (ativo) setAulas([]);
        } finally {
          if (ativo) setCarregando(false);
        }
      })();

      return () => {
        ativo = false;
      };
    }, [limite]),
  );

  return { aulas, carregando };
}