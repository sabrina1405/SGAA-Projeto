// Espelham os schemas do backend (api/src/schemas/aluno.py e usuario.py).

export type Pagina<T> = {
  itens: T[];
  total: number;
};

export type AlunoListaItem = {
  id: number;
  nome_completo: string;
  email: string;
  // Do responsável, quando o aluno tem um.
  telefone: string;
};

export type PerfilAlunoDados = {
  data_nascimento: string; // AAAA-MM-DD
  possui_responsavel: boolean;
  cpf: string | null;
  telefone: string | null;
  responsavel_nome: string | null;
  responsavel_cpf: string | null;
  responsavel_telefone: string | null;
};

export type AlunoDetalhe = {
  id: number;
  nome_completo: string;
  email: string;
  primeiro_acesso_concluido: boolean;
  // Nulo enquanto o aluno não conclui o primeiro acesso.
  perfil: PerfilAlunoDados | null;
  // Reservados: o backend ainda devolve sempre vazios.
  aulas: unknown[];
  pagamentos: unknown[];
};

export type AlunoCriar = {
  nome_completo: string;
  email: string;
};