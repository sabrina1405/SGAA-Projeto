import { ScrollView, StyleSheet, Text, View, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams } from 'expo-router';

import { palette } from '@/constants/palette';

export default function InformacoesAlunoScreen() {
  const { id } = useLocalSearchParams(); // Aqui você captura o ID do aluno clicado (ex: "1", "2")

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
      
      {/* Header Hero do Perfil */}
      <View style={styles.heroCard}>
        <View style={styles.avatarWrapper}>
          <View style={styles.avatarCircle}>
            <Ionicons name="person" size={44} color={palette.header} />
          </View>
          <Pressable style={styles.btnEditarFoto} onPress={() => {}}>
            <Ionicons name="camera-outline" size={14} color="#FFFFFF" />
          </Pressable>
        </View>

        <Text style={styles.nomeAluno}>Aluno ID: {id}</Text>
        <Text style={styles.emailAluno}>nomecompleto@gmail.com</Text>

        <View style={styles.badgeAtivoHeader}>
          <View style={styles.dotStatus} />
          <Text style={styles.badgeAtivoTexto}>Aluno Ativo</Text>
        </View>

        <View style={styles.heroAcoesRow}>
          <Pressable style={[styles.btnHero, styles.btnHeroSecundario]} onPress={() => {}}>
            <Ionicons name="create-outline" size={16} color={palette.header} />
            <Text style={styles.btnHeroSecundarioTexto}>Editar Dados</Text>
          </Pressable>

          <Pressable style={[styles.btnHero, styles.btnHeroPrimario]} onPress={() => {}}>
            <Ionicons name="checkmark-circle-outline" size={16} color="#FFFFFF" />
            <Text style={styles.btnHeroPrimarioTexto}>Salvar</Text>
          </Pressable>
        </View>
      </View>

      {/* Resumo Financeiro */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Resumo Financeiro</Text>
        <View style={styles.kpiGrid}>
          <View style={[styles.kpiCard, { backgroundColor: '#FFF8E1', borderColor: '#FFE082' }]}>
            <Text style={[styles.kpiRotulo, { color: '#B7791F' }]}>Previsão</Text>
            <Text style={[styles.kpiValor, { color: '#B7791F' }]}>R$ 4.300</Text>
          </View>

          <View style={[styles.kpiCard, { backgroundColor: '#E8F5E9', borderColor: '#A5D6A7' }]}>
            <Text style={[styles.kpiRotulo, { color: '#2E7D32' }]}>Pago</Text>
            <Text style={[styles.kpiValor, { color: '#1B5E20' }]}>R$ 300,00</Text>
          </View>

          <View style={[styles.kpiCard, { backgroundColor: '#FFEBEE', borderColor: '#EF9A9A' }]}>
            <Text style={[styles.kpiRotulo, { color: '#C62828' }]}>Em Aberto</Text>
            <Text style={[styles.kpiValor, { color: '#B71C1C' }]}>R$ 4.000</Text>
          </View>
        </View>
      </View>

      {/* Informações Pessoais */}
      <View style={styles.secao}>
        <Text style={styles.secaoTitulo}>Informações Pessoais</Text>
        <View style={styles.cardDados}>
          <View style={styles.linhaDado}>
            <Ionicons name="calendar-outline" size={18} color={palette.header} />
            <View style={styles.dadoInfo}>
              <Text style={styles.dadoLabel}>Data de Nascimento</Text>
              <Text style={styles.dadoValor}>15/04/2008</Text>
            </View>
          </View>

          <View style={styles.linhaDado}>
            <Ionicons name="card-outline" size={18} color={palette.header} />
            <View style={styles.dadoInfo}>
              <Text style={styles.dadoLabel}>CPF</Text>
              <Text style={styles.dadoValor}>000.000.000-00</Text>
            </View>
          </View>

          <View style={styles.linhaDado}>
            <Ionicons name="call-outline" size={18} color={palette.header} />
            <View style={styles.dadoInfo}>
              <Text style={styles.dadoLabel}>Telefone</Text>
              <Text style={styles.dadoValor}>(11) 98765-4321</Text>
            </View>
          </View>
        </View>
      </View>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 40, gap: 20 },
  heroCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: palette.line,
  },
  avatarWrapper: { position: 'relative', marginBottom: 12 },
  avatarCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#F3E5F5',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: palette.header,
  },
  btnEditarFoto: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: palette.header,
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  nomeAluno: { fontSize: 18, fontWeight: '700', color: palette.title },
  emailAluno: { fontSize: 12, color: palette.textMuted, marginTop: 2, marginBottom: 10 },
  badgeAtivoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 16,
  },
  dotStatus: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#2E7D32' },
  badgeAtivoTexto: { fontSize: 11, fontWeight: '700', color: '#2E7D32' },
  heroAcoesRow: { flexDirection: 'row', gap: 10, width: '100%' },
  btnHero: {
    flex: 1,
    flexDirection: 'row',
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  btnHeroSecundario: { backgroundColor: '#F3E5F5' },
  btnHeroSecundarioTexto: { fontSize: 12, fontWeight: '600', color: palette.header },
  btnHeroPrimario: { backgroundColor: palette.header },
  btnHeroPrimarioTexto: { fontSize: 12, fontWeight: '600', color: '#FFFFFF' },
  secao: { gap: 10 },
  secaoTitulo: { fontSize: 15, fontWeight: '700', color: palette.title },
  kpiGrid: { flexDirection: 'row', gap: 10 },
  kpiCard: { flex: 1, padding: 12, borderRadius: 14, borderWidth: 1, gap: 4 },
  kpiRotulo: { fontSize: 10, fontWeight: '700', textTransform: 'uppercase' },
  kpiValor: { fontSize: 14, fontWeight: '800' },
  cardDados: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 12,
  },
  linhaDado: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  dadoInfo: { flex: 1 },
  dadoLabel: { fontSize: 10, color: palette.textMuted, fontWeight: '500' },
  dadoValor: { fontSize: 13, color: palette.title, fontWeight: '600', marginTop: 1 },
});