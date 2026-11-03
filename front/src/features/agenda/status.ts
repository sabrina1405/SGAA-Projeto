import type { StatusEvento } from './types';

// Única fonte das cores/rótulos de status da agenda.
export const STATUS_INFO: Record<StatusEvento, { rotulo: string; cor: string }> = {
  confirmada: { rotulo: 'Confirmada', cor: '#2E7D32' },
  pendente: { rotulo: 'Pendente', cor: '#F5A623' },
  reposicao: { rotulo: 'Reposição', cor: '#B65FBF' },
};