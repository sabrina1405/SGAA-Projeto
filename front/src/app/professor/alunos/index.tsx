import { useState } from 'react';
import { FlatList, Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { palette } from '@/constants/palette';

type AlunoItem = {
  id: string;
  nome: string;
  telefone?: string;
  email?: string;
  ativo: boolean;
  tipo: 'aluno' | 'grupo';
};

const ALUNOS_MOCK: AlunoItem[] = [
  { id: '1', nome: 'Ana Souza', telefone: '(11) 98888-1111', email: 'anasouza@gmail.com', ativo: true, tipo: 'aluno' },
  { id: '2', nome: 'Bruno Lima', telefone: '(11) 97777-2222', email: 'brunolima@gmail.com', ativo: true, tipo: 'aluno' },
  { id: '3', nome: 'Carla Dias', telefone: '(11) 96666-3333', email: 'carladias@gmail.com', ativo: true, tipo: 'aluno' },
  { id: '4', nome: 'Diego Alves', telefone: '(11) 95555-4444', email: 'diegoalves@gmail.com', ativo: true, tipo: 'aluno' },
  { id: '5', nome: 'Helena Rocha', telefone: '(11) 94444-5555', email: 'helenarocha@gmail.com', ativo: false, tipo: 'aluno' },
  { id: '6', nome: 'Nome do Grupo', ativo: true, tipo: 'grupo' },
];

function Separador() {
  return <View style={styles.separador} />;
}

export default function AlunosScreen() {
  const router = useRouter();
  const [mostrarInativos, setMostrarInativos] = useState(false);

  const dadosFiltrados = ALUNOS_MOCK.filter(item => (mostrarInativos ? true : item.ativo));

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.conteudo}
      data={dadosFiltrados}
      keyExtractor={(item) => item.id}
      ItemSeparatorComponent={Separador}
      ListEmptyComponent={<Text style={styles.vazio}>Nenhum aluno encontrado.</Text>}
      ListHeaderComponent={
        <View style={styles.headerWrapper}>
          {/* Barra de Ações Superiores */}
          <View style={styles.acoesContainer}>
            <Pressable style={({ pressed }) => [styles.botaoAcao, pressed && styles.pressionado]} onPress={() => {}}>
              <Ionicons name="person-outline" size={16} color="#ffffff" />
              <Text style={styles.botaoTexto}>Filtrar Aluno</Text>
            </Pressable>

            <Pressable style={({ pressed }) => [styles.botaoAcao, pressed && styles.pressionado]} onPress={() => {}}>
              <Ionicons name="people-outline" size={16} color="#ffffff" />
              <Text style={styles.botaoTexto}>Novo Grupo</Text>
            </Pressable>

            <Pressable style={({ pressed }) => [styles.botaoAcao, pressed && styles.pressionado]} onPress={() => {}}>
              <Ionicons name="person-add-outline" size={16} color="#ffffff" />
              <Text style={styles.botaoTexto}>Novo Aluno</Text>
            </Pressable>
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

          {/* Botão para navegar especificamente para os detalhes do ID clicado */}
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
  headerWrapper: { gap: 14, marginBottom: 12 },

  acoesContainer: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
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
    minWidth: 95,
  },
  botaoTexto: { color: '#ffffff', fontSize: 11, fontWeight: '600' },

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