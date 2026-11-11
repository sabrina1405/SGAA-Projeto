import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { palette } from '@/constants/palette';
import { listarEntregas } from '@/features/atividades/service';
import type { EntregaListaItem, SituacaoEntrega } from '@/features/atividades/types';

type FiltroAtividade = 'todas' | SituacaoEntrega;
type EstadoItem = 'vencida' | 'aberta' | 'entregue' | 'entregue_atraso';

const TAMANHO_PAGINA = 20;

const ABAS: { id: FiltroAtividade; label: string }[] = [
  { id: 'todas', label: 'Todas' },
  { id: 'vencidas', label: 'Vencidas' },
  { id: 'proximas', label: 'Próximas' },
  { id: 'entregues', label: 'Entregues' },
];

const VISUAL: Record<
  EstadoItem,
  { cor: string; fundo: string; texto: string; icone: keyof typeof Ionicons.glyphMap; badge: string }
> = {
  vencida: { cor: '#EF4444', fundo: '#FEE2E2', texto: '#DC2626', icone: 'alert-circle', badge: 'Vencida' },
  aberta: { cor: '#F59E0B', fundo: '#FEF3C7', texto: '#D97706', icone: 'time', badge: 'Em Aberto' },
  entregue: { cor: '#10B981', fundo: '#D1FAE5', texto: '#059669', icone: 'checkmark-done-circle', badge: 'Entregue' },
  entregue_atraso: { cor: '#10B981', fundo: '#D1FAE5', texto: '#059669', icone: 'checkmark-done-circle', badge: 'Com atraso' },
};

function estadoDoItem(item: EntregaListaItem): EstadoItem {
  if (item.status === 'entregue_com_atraso') return 'entregue_atraso';
  if (item.status) return 'entregue';
  return new Date(item.vence_em) < new Date() ? 'vencida' : 'aberta';
}

function formatarData(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR');
}

function formatarHora(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function textoRodape(item: EntregaListaItem, estado: EstadoItem) {
  switch (estado) {
    case 'vencida':
      return `Prazo encerrado em ${formatarData(item.vence_em)}`;
    case 'aberta':
      return `Vence em ${formatarData(item.vence_em)} às ${formatarHora(item.vence_em)}`;
    case 'entregue_atraso':
      return `Entregue com atraso em ${item.enviada_em ? formatarData(item.enviada_em) : '-'}`;
    default:
      return `Enviado em ${item.enviada_em ? formatarData(item.enviada_em) : '-'}`;
  }
}

export default function AtividadesScreen() {
  const router = useRouter();
  const [filtro, setFiltro] = useState<FiltroAtividade>('todas');
  const [itens, setItens] = useState<EntregaListaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [carregando, setCarregando] = useState(true);
  const [carregandoMais, setCarregandoMais] = useState(false);
  const [atualizando, setAtualizando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [contadores, setContadores] = useState<Partial<Record<SituacaoEntrega, number>>>({});

  // Evita que uma resposta antiga sobrescreva a de um filtro mais novo.
  const requisicao = useRef(0);

  const carregarContadores = useCallback(async () => {
    try {
      const [vencidas, proximas, entregues] = await Promise.all([
        listarEntregas('vencidas', 1, 1),
        listarEntregas('proximas', 1, 1),
        listarEntregas('entregues', 1, 1),
      ]);
      setContadores({
        vencidas: vencidas.total,
        proximas: proximas.total,
        entregues: entregues.total,
      });
    } catch {
      // Os contadores são só um complemento visual; falha silenciosa.
    }
  }, []);

  const carregar = useCallback(
    async (filtroAtual: FiltroAtividade, paginaAtual: number, modo: 'inicial' | 'mais' | 'refresh') => {
      const id = ++requisicao.current;
      if (modo === 'inicial') setCarregando(true);
      if (modo === 'mais') setCarregandoMais(true);
      if (modo === 'refresh') setAtualizando(true);
      setErro(null);

      try {
        const situacao = filtroAtual === 'todas' ? undefined : filtroAtual;
        const dados = await listarEntregas(situacao, paginaAtual, TAMANHO_PAGINA);
        if (id !== requisicao.current) return;
        setItens((atuais) => (paginaAtual === 1 ? dados.itens : [...atuais, ...dados.itens]));
        setTotal(dados.total);
        setPagina(paginaAtual);
      } catch {
        if (id !== requisicao.current) return;
        setErro('Não foi possível carregar as atividades.');
      } finally {
        if (id === requisicao.current) {
          setCarregando(false);
          setCarregandoMais(false);
          setAtualizando(false);
        }
      }
    },
    [],
  );

  // Recarrega ao abrir a tela, ao voltar de "Nova Atividade" e ao trocar de filtro.
  useFocusEffect(
    useCallback(() => {
      carregar(filtro, 1, 'inicial');
      carregarContadores();
    }, [filtro, carregar, carregarContadores]),
  );

  function trocarFiltro(novo: FiltroAtividade) {
    if (novo === filtro) return;
    setItens([]);
    setTotal(0);
    setFiltro(novo);
  }

  function rotuloAba(aba: { id: FiltroAtividade; label: string }) {
    if (aba.id === 'todas') return aba.label;
    const qtd = contadores[aba.id];
    return qtd === undefined ? aba.label : `${aba.label} (${qtd})`;
  }

  const temMais = itens.length < total;

  return (
    <View style={styles.container}>
      {/* Header com Filtros em Abas */}
      <View style={styles.headerArea}>
        <View style={styles.headerTop}>
          <Text style={styles.headerTitle}>Mural de Atividades</Text>
          <Pressable
            style={({ pressed }) => [styles.btnCriar, pressed && styles.pressionado]}
            onPress={() => router.push('/professor/atividades/novo')}
          >
            <Ionicons name="add" size={18} color="#FFFFFF" />
            <Text style={styles.btnCriarTexto}>Nova Atividade</Text>
          </Pressable>
        </View>

        {/* Segmented Control / Tabs */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsContainer}>
          {ABAS.map((tab) => (
            <Pressable
              key={tab.id}
              style={[styles.tabChip, filtro === tab.id && styles.tabChipAtivo]}
              onPress={() => trocarFiltro(tab.id)}
            >
              <Text style={[styles.tabChipTexto, filtro === tab.id && styles.tabChipTextoAtivo]}>
                {rotuloAba(tab)}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
      </View>

      <ScrollView
        contentContainerStyle={styles.conteudo}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={atualizando}
            onRefresh={() => {
              carregar(filtro, 1, 'refresh');
              carregarContadores();
            }}
          />
        }
      >
        {carregando && (
          <ActivityIndicator size="large" color={palette.title} style={styles.centralizado} />
        )}

        {!carregando && erro && (
          <View style={styles.estadoVazio}>
            <Ionicons name="cloud-offline-outline" size={32} color={palette.textMuted} />
            <Text style={styles.estadoTexto}>{erro}</Text>
            <Pressable
              style={({ pressed }) => [styles.btnCriar, pressed && styles.pressionado]}
              onPress={() => carregar(filtro, 1, 'inicial')}
            >
              <Text style={styles.btnCriarTexto}>Tentar novamente</Text>
            </Pressable>
          </View>
        )}

        {!carregando && !erro && itens.length === 0 && (
          <View style={styles.estadoVazio}>
            <Ionicons name="document-text-outline" size={32} color={palette.textMuted} />
            <Text style={styles.estadoTexto}>Nenhuma atividade encontrada.</Text>
          </View>
        )}

        {!carregando &&
          itens.map((item) => {
            const estado = estadoDoItem(item);
            const visual = VISUAL[estado];
            const entregue = estado === 'entregue' || estado === 'entregue_atraso';

            return (
              <View
                key={`${item.atividade_id}-${item.aluno_id}`}
                style={[styles.card, { borderLeftColor: visual.cor }]}
              >
                <View style={styles.cardTopRow}>
                  <View style={[styles.iconBox, { backgroundColor: visual.fundo }]}>
                    <Ionicons name={visual.icone} size={20} color={visual.cor} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.cardTitle}>{item.titulo}</Text>
                    <Text style={styles.cardSub}>Aluno: {item.aluno_nome}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: visual.fundo }]}>
                    <Text style={[styles.badgeText, { color: visual.texto }]}>{visual.badge}</Text>
                  </View>
                </View>
                <View style={styles.cardFooter}>
                  <Ionicons
                    name={entregue ? 'checkmark-circle-outline' : 'calendar-outline'}
                    size={14}
                    color={entregue ? '#10B981' : palette.textMuted}
                  />
                  <Text style={styles.cardFooterText}>{textoRodape(item, estado)}</Text>
                </View>
              </View>
            );
          })}

        {!carregando && !erro && temMais && (
          <Pressable
            style={({ pressed }) => [styles.btnMais, pressed && styles.pressionado]}
            onPress={() => carregar(filtro, pagina + 1, 'mais')}
            disabled={carregandoMais}
          >
            {carregandoMais ? (
              <ActivityIndicator size="small" color={palette.title} />
            ) : (
              <Text style={styles.btnMaisTexto}>Carregar mais</Text>
            )}
          </Pressable>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  headerArea: {
    backgroundColor: '#FFFFFF',
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: palette.line,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: palette.title },
  btnCriar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: palette.button || '#2E7D32',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  btnCriarTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  tabsContainer: { paddingHorizontal: 16, gap: 8 },
  tabChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
  },
  tabChipAtivo: { backgroundColor: palette.title },
  tabChipTexto: { fontSize: 12, fontWeight: '600', color: '#6B7280' },
  tabChipTextoAtivo: { color: '#FFFFFF' },
  conteudo: { padding: 16, gap: 12, paddingBottom: 40 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
    gap: 12,
  },
  cardTopRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBox: { width: 38, height: 38, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  cardTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  cardSub: { fontSize: 12, color: palette.textMuted, marginTop: 2 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  badgeText: { fontSize: 11, fontWeight: '700' },
  cardFooter: { flexDirection: 'row', alignItems: 'center', gap: 6, borderTopWidth: 1, borderTopColor: '#F3F4F6', paddingTop: 8 },
  cardFooterText: { fontSize: 11, color: palette.textMuted, fontWeight: '500' },
  pressionado: { opacity: 0.8 },
  centralizado: { marginTop: 32 },
  estadoVazio: { alignItems: 'center', gap: 12, marginTop: 40 },
  estadoTexto: { fontSize: 13, color: palette.textMuted, textAlign: 'center' },
  btnMais: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  btnMaisTexto: { fontSize: 12, fontWeight: '700', color: palette.title },
});

