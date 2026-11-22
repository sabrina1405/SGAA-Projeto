const API_URL = process.env.EXPO_PUBLIC_API_URL;

export const LIMITE_BYTES = 5 * 1024 * 1024;

type Resposta<T> = { mensagem: string; dados: T };

export type ArquivoSelecionado = {
  uri: string;
  nome: string;
  tipoMime: string;
  tamanho: number;
};

export type ArquivoEnviado = {
  id: number;
  nome: string;
  tipo_mime: string;
  tamanho: number;
  url: string | null;
};

async function chamar<T>(token: string, caminho: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${caminho}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  const corpo = await res.json().catch(() => null);
  if (!res.ok) {
    const detalhe = typeof corpo?.detail === 'string' ? corpo.detail : 'Falha ao enviar o arquivo.';
    throw new Error(detalhe);
  }
  return corpo as T;
}

export async function descartarArquivo(token: string, id: number) {
  await chamar(token, `/arquivos/${id}`, { method: 'DELETE' });
}

export async function enviarArquivo(token: string, arquivo: ArquivoSelecionado): Promise<ArquivoEnviado> {
  // 1) abre a sessão
  const sessao = await chamar<Resposta<{ arquivo_id: number; url_upload: string }>>(
    token,
    '/arquivos/sessao',
    {
      method: 'POST',
      body: JSON.stringify({
        nome: arquivo.nome,
        tipo_mime: arquivo.tipoMime,
        tamanho: arquivo.tamanho,
      }),
    },
  );
  const { arquivo_id, url_upload } = sessao.dados;

  try {
    // 2) envia o arquivo direto ao Drive
    const blob = await (await fetch(arquivo.uri)).blob();
    const upload = await fetch(url_upload, {
      method: 'PUT',
      headers: { 'Content-Type': arquivo.tipoMime },
      body: blob,
    });
    if (!upload.ok) throw new Error('Falha no upload para o Drive.');
    const { id: driveFileId } = await upload.json();

    // 3) confirma na API
    const confirmado = await chamar<Resposta<ArquivoEnviado>>(
      token,
      `/arquivos/${arquivo_id}/confirmar`,
      { method: 'POST', body: JSON.stringify({ drive_file_id: driveFileId }) },
    );
    return confirmado.dados;
  } catch (erro) {
    await descartarArquivo(token, arquivo_id).catch(() => {});
    throw erro;
  }
}