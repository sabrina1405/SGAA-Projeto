import type { Evento } from './types';

export const EVENTOS_MOCK: Evento[] = [
  { id: '1', data: '2026-11-05', aluno: 'Ana Souza', inicio: '10:00', fim: '11:00', status: 'confirmada' },
  { id: '2', data: '2026-11-06', aluno: 'Bruno Lima', inicio: '14:00', fim: '15:00', status: 'pendente' },
  { id: '3', data: '2026-11-08', aluno: 'Carla Dias', inicio: '09:00', fim: '10:00', status: 'reposicao' },
  { id: '4', data: '2026-11-12', aluno: 'Diego Alves', inicio: '16:00', fim: '17:00', status: 'confirmada' },
  { id: '5', data: '2026-11-13', aluno: 'Ana Souza', inicio: '10:00', fim: '11:00', status: 'pendente' },
  { id: '6', data: '2026-11-13', aluno: 'Bruno Lima', inicio: '15:00', fim: '16:00', status: 'pendente' },
  { id: '7', data: '2026-11-20', aluno: 'Carla Dias', inicio: '11:00', fim: '12:00', status: 'confirmada' },
  { id: '8', data: '2026-11-26', aluno: 'Diego Alves', inicio: '08:00', fim: '09:00', status: 'pendente' },
];