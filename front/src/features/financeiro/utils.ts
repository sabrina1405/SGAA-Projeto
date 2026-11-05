import type { Lancamento, ResumoFinanceiro } from './types';

const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

export function formatarMoeda(valor: number): string {
  return brl.format(valor);
}

// Recebe AAAA-MM-DD e devolve DD/MM/AAAA sem passar por Date (evita problema de fuso).
export function formatarData(iso: string | null): string {
  if (!iso) return '---------';
  const [ano, mes, dia] = iso.split('-');
  return `${dia}/${mes}/${ano}`;
}

// Saldo = o que já foi pago. Previsão = o que ainda falta receber (pendente + vencido).
export function calcularResumo(lancamentos: Lancamento[]): ResumoFinanceiro {
  return lancamentos.reduce<ResumoFinanceiro>(
    (acc, l) => {
      if (l.status === 'pago') acc.saldo += l.valor;
      else acc.previsaoEntradas += l.valor;
      return acc;
    },
    { saldo: 0, previsaoEntradas: 0 },
  );
}
