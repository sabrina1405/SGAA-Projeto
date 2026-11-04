// Espelham os schemas do backend (api/src/schemas).

// Toda resposta de sucesso da API vem neste envelope.
export type Resposta<T> = {
  mensagem: string;
  dados: T;
};

export type Usuario = {
  id: number;
  nome_completo: string;
  email: string;
  // Valores de TipoUsuario em api/src/models/usuario.py.
  tipo: string;
};

export type LoginEntrada = {
  email: string;
  senha: string;
};

export type TokenResposta = {
  access_token: string;
  token_type: string;
  expires_in: number;
  usuario: Usuario;
};