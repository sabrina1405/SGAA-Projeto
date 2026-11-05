import axios from 'axios';

import type { Resposta, Usuario } from '@/features/auth/types';
import { api } from '@/services/api';

import type { AlunoCriar, AlunoDetalhe, AlunoListaItem, Pagina } from './types';

type ParamsListagem = {
  pagina?: number;
  tamanho?: number;
  busca?: string;
};

// Só aparecem os alunos que já concluíram o primeiro acesso.
export async function listarAlunos(params: ParamsListagem = {}): Promise<Pagina<AlunoListaItem>> {
  const { data } = await api.get<Resposta<Pagina<AlunoListaItem>>>('/usuarios/alunos', { params });
  return data.dados;
}

export async function obterAluno(id: number | string): Promise<AlunoDetalhe> {
  const { data } = await api.get<Resposta<AlunoDetalhe>>(`/usuarios/alunos/${id}`);
  return data.dados;
}

// Cria o aluno e a API envia a ele o e-mail com o código de primeiro acesso.
export async function criarAluno({ nome_completo, email }: AlunoCriar): Promise<Usuario> {
  const { data } = await api.post<Resposta<Usuario>>('/usuarios/alunos', {
    nome_completo: nome_completo.trim(),
    email: email.trim(),
  });
  return data.dados;
}

// Converte o erro do Axios em uma mensagem para mostrar na tela.
export function mensagemDeErroAlunos(erro: unknown): string {
  if (axios.isAxiosError(erro)) {
    if (!erro.response) return 'Não foi possível conectar ao servidor.';
    if (erro.response.status === 422) return 'Confira os dados informados.';
    const detalhe = erro.response.data?.detail;
    if (typeof detalhe === 'string') return detalhe;
  }
  return 'Ocorreu um erro inesperado. Tente novamente.';
}