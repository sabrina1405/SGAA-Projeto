// Cores do protótipo do Figma. Fica separado do theme.ts do template.
export const palette = {
  header: '#6B1F99',
  primary: '#8E24AA',
  button: '#B565BA',
  background: '#FFFFFF',
  title: '#555555',
  textMuted: '#888888',
  cellBg: '#E9E9E9',
  line: '#C9C9C9',
  saldo: { fundo: '#B8D8BE', valor: '#1B5E20' },
  previsao: { fundo: '#FFD97D', valor: '#F59E0B' },
  status: {
    pago: { fundo: '#B8D8BE', borda: '#2E7D32', texto: '#1B5E20' },
    pendente: { fundo: '#FFD97D', borda: '#E0A800', texto: '#7A5A00' },
    vencido: { fundo: '#F5A3A3', borda: '#C62828', texto: '#B71C1C' },
  },
  valor: { pago: '#2E7D32', pendente: '#F59E0B', vencido: '#D32F2F' },
} as const;
