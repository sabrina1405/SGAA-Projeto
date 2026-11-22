import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';

import { listarEntregas } from './service';

export type AtividadeResumo = {
  id: string;
  titulo: string;
  aluno: string;
  quando: string; // ex.: 22/09 às 15:00
};

const dois = (n: number) => String(n).padStart(2, '0');

function formatarQuando(iso: string) {
  const d = new Date(iso);
  return `${dois(d.getDate())}/${dois(d.getMonth() + 1)} às ${dois(d.getHours())}:${dois(d.getMinutes())}`;
}

export function useProximasAtividades(limite = 3) {
  const [atividades, setAtividades] = useState<AtividadeResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(false);

  // Recarrega sempre que a Início ganha foco (ex.: ao voltar de "Nova Atividade").
  useFocusEffect(
    useCallback(() => {
      let ativo = true;
      listarEntregas('proximas', 1, limite)
        .then((dados) => {
          if (!ativo) return;
          setAtividades(
            dados.itens.map((item) => ({
              id: `${item.atividade_id}-${item.aluno_id}`,
              titulo: item.titulo,
              aluno: item.aluno_nome,
              quando: formatarQuando(item.vence_em),
            })),
          );
          setErro(false);
        })
        .catch(() => {
          if (ativo) setErro(true);
        })
        .finally(() => {
          if (ativo) setCarregando(false);
        });
      return () => {
        ativo = false;
      };
    }, [limite]),
  );

  return { atividades, carregando, erro };
}