import { api } from '@/services/api'; 
import type { Lancamento, StatusPagamento } from './types';

export type ResumoFinanceiro = {
  mes: string;
  recebido_centavos: number;
  pendente_centavos: number;
  vencido_centavos: number;
};

export type SituacaoCobranca = 'pendente' | 'vencida' | 'paga' | 'cancelada';

export type Cobranca = {
  id: number;
  aluno_id: number;
  aluno_nome: string;
  plano_id: number | null;
  descricao: string;
  valor_centavos: number;
  vencimento: string; // AAAA-MM-DD
  situacao: SituacaoCobranca;
  paga_em: string | null; // data e hora em ISO
  criado_em: string;
};

type Pagina<T> = { itens: T[]; total: number };

export type FiltrosCobranca = {
  aluno_id?: number;
  situacao?: SituacaoCobranca;
  de?: string; // AAAA-MM-DD
  ate?: string; // AAAA-MM-DD
  pagina?: number;
  tamanho?: number;
};

// mes no formato AAAA-MM; sem ele, o back usa o mês atual
export async function buscarResumo(mes?: string): Promise<ResumoFinanceiro> {
  const { data } = await api.get('/financeiro/resumo', {
    params: mes ? { mes } : undefined,
  });
  return data.dados; // a resposta vem embrulhada em { mensagem, dados }
}

export async function listarCobrancas(filtros: FiltrosCobranca = {}): Promise<Pagina<Cobranca>> {
  const { data } = await api.get('/financeiro/cobrancas', { params: filtros });
  return data.dados;
}

/* ---------- adaptação para o formato que a LancamentoRow já usa ---------- */

const pad = (n: number) => String(n).padStart(2, '0');

// '2026-10-05' -> '05/10/2026' (sem passar por Date, para não deslocar o dia)
function dataSimples(iso: string) {
  const [ano, mes, dia] = iso.slice(0, 10).split('-');
  return `${dia}/${mes}/${ano}`;
}

// ISO com hora -> dia no horário de Brasília (UTC-3)
function dataBrasilia(iso: string) {
  const d = new Date(new Date(iso).getTime() - 3 * 60 * 60 * 1000);
  return `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()}`;
}

const STATUS_DO_ROW: Record<Exclude<SituacaoCobranca, 'cancelada'>, StatusPagamento> = {
  pendente: 'pendente',
  vencida: 'vencido',
  paga: 'pago',
};

// As canceladas ficam de fora: o StatusPagamento não tem esse status.
export function cobrancasParaLancamentos(lista: Cobranca[]): Lancamento[] {
  return lista.flatMap((c) =>
    c.situacao === 'cancelada'
      ? []
      : [
          {
            id: String(c.id),
            dataAgendada: dataSimples(c.vencimento),
            dataPagamento: c.paga_em ? dataBrasilia(c.paga_em) : '---------',
            alunoNome: c.aluno_nome,
            valor: c.valor_centavos / 100,
            status: STATUS_DO_ROW[c.situacao],
          },
        ],
  );
}