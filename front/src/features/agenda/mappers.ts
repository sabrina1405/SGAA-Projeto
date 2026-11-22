import type { AulaListaItemApi, StatusAulaApi } from './api';
import type { Evento, StatusEvento } from './types';

// O back devolve sempre no horário de Brasília ("2026-11-05T10:00:00-03:00"),
// então basta fatiar a string: nada de new Date() e problema de fuso.
export const dataDeISO = (iso: string) => iso.slice(0, 10);
export const horaDeISO = (iso: string) => iso.slice(11, 16);

// Brasil não tem horário de verão desde 2019, então -03:00 fixo é seguro.
export const paraISO = (data: string, hora: string) => `${data}T${hora}:00-03:00`;


const STATUS: Record<StatusAulaApi, StatusEvento> = {
  agendada: 'pendente',
  realizada: 'confirmada',
  cancelada: 'cancelada',
};

function resumoAlunos(alunos: AulaListaItemApi['alunos']) {
  const ativos = alunos.filter((a) => a.status === 'ativa');
  const lista = ativos.length > 0 ? ativos : alunos;
  if (lista.length === 0) return 'Sem alunos';
  const primeiro = lista[0].nome_completo;
  return lista.length === 1 ? primeiro : `${primeiro} +${lista.length - 1}`;
}

export function aulaParaEvento(aula: AulaListaItemApi): Evento {
  return {
    id: String(aula.id),
    data: dataDeISO(aula.inicio),
    aluno: resumoAlunos(aula.alunos),
    inicio: horaDeISO(aula.inicio),
    fim: horaDeISO(aula.fim),
    status: STATUS[aula.status],
  };
}

// 'DD/MM/AAAA' -> 'AAAA-MM-DD' (null se inválida)
export function dataBRparaChave(texto: string) {
  const m = texto.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : null;
}

// '10:00 ás 11:00' -> { inicio: '10:00', fim: '11:00' } (null se inválido)
export function parseHorario(texto: string) {
  const m = texto.match(/(\d{2}:\d{2}).*?(\d{2}:\d{2})/);
  return m ? { inicio: m[1], fim: m[2] } : null;
}

// 'AAAA-MM-DD' -> 'DD/MM/AAAA'
export const chaveParaDataBR = (chave: string) => chave.split('-').reverse().join('/');