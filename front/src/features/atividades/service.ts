import { api } from '@/services/api'; // ajuste para o seu cliente
import type {
  AtividadeCriar, EntregaListaItem, Pagina, Resposta, SituacaoEntrega,
} from './types';

export async function listarEntregas(situacao?: SituacaoEntrega, pagina = 1, tamanho = 20) {
  const { data } = await api.get<Resposta<Pagina<EntregaListaItem>>>(
    '/atividades/entregas',
    { params: { situacao, pagina, tamanho } },
  );
  return data.dados;
}

export async function criarAtividade(payload: AtividadeCriar) {
  const { data } = await api.post<Resposta<{ id: number }>>('/atividades', payload);
  return data.dados;
}