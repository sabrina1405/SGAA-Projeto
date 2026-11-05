import { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';

import { listarAlunos, mensagemDeErroAlunos } from '@/features/alunos/alunosService';
import { formatarTelefone } from '@/features/alunos/formatadores';
import type { AlunoListaItem } from '@/features/alunos/types';
import { palette } from '@/constants/palette';

type AlunoItem = {
  id: string;
  nome: string;
  telefone?: string;
  email?: string;
  ativo: boolean;
  tipo: 'aluno' | 'grupo';
};

function paraItem(aluno: AlunoListaItem): AlunoItem {
  return {
    id: String(aluno.id),
    nome: aluno.nome_completo,
    telefone: formatarTelefone(aluno.telefone),
    email: aluno.email,
    ativo: true,
    tipo: 'aluno',
  };
}

function Separador() {
  return <View style={styles.separador} />;
}

export default function AlunosScreen() {
  const router = useRouter();
  const [mostrarInativos, setMostrarInativos] = useState(false);
  const [busca, setBusca] = useState(''); // Estado para a barra de pesquisa
  const [alunos, setAlunos] = useState<AlunoItem[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [carregandoMais, setCarregandoMais] = useState(false);
  const [erro, setErro] = useState('');
  const paginaAtual = useRef(1);

  const carregarPagina = useCallback(async (pagina: number): Promise<boolean> => {
    try {
      const dados = await listarAlunos({ pagina });
      const novos = dados.itens.map(paraItem);
      setAlunos((atual) => (pagina === 1 ? novos : [...atual, ...novos]));
      setTotal(dados.total);
      setErro('');
      return true;
    } catch (e) {
      setErro(mensagemDeErroAlunos(e));
      return false;
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      paginaAtual.current = 1;
      carregarPagina(1).finally(() => setCarregando(false));
    }, [carregarPagina]),
  );

  async function carregarMais() {
    if (carregando || carregandoMais || alunos.length >= total) return;
    setCarregandoMais(true);
    paginaAtual.current += 1;
    const ok = await carregarPagina(paginaAtual.current);
    if (!ok) paginaAtual.current -= 1;
    setCarregandoMais(false);
  }

  // Filtragem combinada por Status (Ativo/Inativo) e Texto da Barra de Pesquisa
  const dadosFiltrados = alunos.filter((item) => {
    const matchStatus = mostrarInativos ? true : item.ativo;
    const matchBusca = item.nome.toLowerCase().includes(busca.toLowerCase()) || 
                       (item.email && item.email.toLowerCase().includes(busca.toLowerCase()));
    return matchStatus && matchBusca;
  });

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.conteudo}
      data={dadosFiltrados}
      keyExtractor={(item) => item.id}
      ItemSeparatorComponent={Separador}
      ListEmptyComponent={
        carregando ? (
          <ActivityIndicator color={palette.header} style={{ marginTop: 24 }} />
        ) : erro ? (
          <Text style={styles.vazio}>{erro}</Text>
        ) : (
          <Text style={styles.vazio}>Nenhum aluno encontrado.</Text>
        )
      }
      ListFooterComponent={
        carregandoMais ? <ActivityIndicator color={palette.header} style={{ marginTop: 12 }} /> : null
      }
      onEndReached={carregarMais}
      onEndReachedThreshold={0.4}
      ListHeaderComponent={
        <View style={styles.headerWrapper}>
          {/* Barra de Ações Superiores */}
          <View style={styles.acoesContainer}>
            <Pressable 
              style={({ pressed }) => [styles.botaoAcao, pressed && styles.pressionado]} 
              onPress={() => {}}
            >
              <Ionicons name="person-outline" size={16} color="#ffffff" />
              <Text style={styles.botaoTexto}>Filtrar</Text>
            </Pressable>

            <Pressable 
              style={({ pressed }) => [styles.botaoAcao, pressed && styles.pressionado]} 
              onPress={() => router.push('/professor/alunos/novo-grupo')}
            >
              <Ionicons name="people-outline" size={16} color="#ffffff" />
              <Text style={styles.botaoTexto}>Novo Grupo</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.botaoAcao, pressed && styles.pressionado]}
              onPress={() => router.push('/professor/alunos/novo')}
            >
              <Ionicons name="person-add-outline" size={16} color="#ffffff" />
              <Text style={styles.botaoTexto}>Novo Aluno</Text>
            </Pressable>
          </View>

          {/* Barra de Pesquisa */}
          <View style={styles.searchContainer}>
            <Ionicons name="search-outline" size={18} color={palette.textMuted} style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Pesquisar aluno por nome ou e-mail..."
              placeholderTextColor="#9CA3AF"
              value={busca}
              onChangeText={setBusca}
            />
            {busca.length > 0 && (
              <Pressable onPress={() => setBusca('')}>
                <Ionicons name="close-circle" size={18} color={palette.textMuted} />
              </Pressable>
            )}
          </View>

          {/* Toggle de Mostrar Inativos */}
          <View style={styles.switchContainer}>
            <Text style={styles.switchLabel}>Mostrar Inativos</Text>
            <Switch
              trackColor={{ false: '#D1D5DB', true: '#C5CAE9' }}
              thumbColor={mostrarInativos ? palette.header : '#F4F3F4'}
              onValueChange={setMostrarInativos}
              value={mostrarInativos}
            />
          </View>
        </View>
      }
      renderItem={({ item }) => (
        <View style={styles.cardItem}>
          <View style={styles.indicatorBar} />
          
          <View style={styles.iconBox}>
            <Ionicons 
              name={item.tipo === 'grupo' ? 'people' : 'person'} 
              size={20} 
              color={palette.header} 
            />
          </View>

          <View style={styles.itemInfo}>
            <Text style={styles.itemTitle}>{item.nome}</Text>
            {item.tipo === 'aluno' && (
              <>
                <Text style={styles.itemSubtitle}>{item.telefone}</Text>
                <Text style={styles.itemEmail}>{item.email}</Text>
              </>
            )}
          </View>

          <View style={[styles.badgeStatus, item.ativo ? styles.badgeAtivo : styles.badgeInativo]}>
            <Text style={[styles.badgeText, item.ativo ? styles.badgeTextAtivo : styles.badgeTextInativo]}>
              {item.ativo ? 'Ativa' : 'Inativa'}
            </Text>
          </View>

          <Pressable 
            style={({ pressed }) => [styles.viewButton, pressed && styles.pressionado]}
            onPress={() => router.push(`/professor/alunos/${item.id}`)}
          >
            <Ionicons name="eye-outline" size={18} color={palette.title} />
          </Pressable>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 32 },
  headerWrapper: { gap: 12, marginBottom: 12 },

  acoesContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  botaoAcao: {
    backgroundColor: palette.header,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 8,
    flex: 1,
    justifyContent: 'center',
  },
  botaoTexto: { color: '#ffffff', fontSize: 11, fontWeight: '600' },

  /* Estilo da Barra de Pesquisa */
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 44,
  },
  searchIcon: { marginRight: 8 },
  searchInput: { flex: 1, fontSize: 13, color: palette.title },

  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: palette.line,
  },
  switchLabel: { fontSize: 12, fontWeight: '600', color: palette.title },

  cardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 12,
    marginVertical: 6,
    borderWidth: 1,
    borderColor: palette.line,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 2,
  },
  indicatorBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 5,
    backgroundColor: palette.header,
  },
  iconBox: {
    width: 42,
    height: 42,
    borderRadius: 10,
    backgroundColor: '#F3E5F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
    marginRight: 12,
  },
  itemInfo: { flex: 1, gap: 2 },
  itemTitle: { fontSize: 13, fontWeight: '700', color: palette.title },
  itemSubtitle: { fontSize: 11, color: palette.textMuted },
  itemEmail: { fontSize: 11, color: palette.textMuted },

  badgeStatus: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 10,
  },
  badgeAtivo: { backgroundColor: '#E8F5E9' },
  badgeInativo: { backgroundColor: '#FFEBEE' },
  badgeText: { fontSize: 10, fontWeight: '700' },
  badgeTextAtivo: { color: '#2E7D32' },
  badgeTextInativo: { color: '#C62828' },

  viewButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
  },

  pressionado: { opacity: 0.8 },
  separador: { height: 4 },
  vazio: { textAlign: 'center', color: palette.textMuted, marginTop: 24 },
});