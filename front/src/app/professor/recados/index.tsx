import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';

export default function RecadosScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <View style={styles.headerTop}>
        <Text style={styles.headerTitle}>Central de Recados</Text>
        <Pressable
          style={({ pressed }) => [styles.btnNovo, pressed && styles.pressionado]}
          onPress={() => router.push('/professor/recados/novo')}
        >
          <Ionicons name="megaphone-outline" size={16} color="#FFFFFF" />
          <Text style={styles.btnNovoTexto}>Novo Recado</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        {/* Recado Ativo Principal */}
        <Text style={styles.sectionTitle}>Recado Geral Ativo</Text>
        <View style={styles.cardDestaque}>
          <View style={styles.cardHeaderRow}>
            <Ionicons name="pin" size={18} color="#D81B60" />
            <Text style={styles.cardDestaqueTitle}>Aviso da Semana</Text>
          </View>
          <Text style={styles.cardTexto}>
            Queridos alunos, sejam bem-vindos à nossa plataforma de estudos. Aqui vocês poderão consultar a agenda, pagamentos e eventos!
          </Text>
          <Pressable style={styles.linkBox}>
            <Ionicons name="link-outline" size={16} color="#2563EB" />
            <Text style={styles.linkTexto}>meet.jit.si/ElCaminoIdiomas</Text>
          </Pressable>
          <View style={styles.acoesRow}>
            <Pressable style={styles.btnSecundario}>
              <Text style={styles.btnSecundarioTexto}>Limpar Painel</Text>
            </Pressable>
            <Pressable style={styles.btnPrimario}>
              <Text style={styles.btnPrimarioTexto}>Editar Recado</Text>
            </Pressable>
          </View>
        </View>

        {/* Histórico */}
        <Text style={styles.sectionTitle}>Histórico de Recados</Text>
        {[
          { id: 1, data: '01/10/2026', texto: 'Lembrete: Próxima semana teremos avaliação oral individual.' },
          { id: 2, data: '20/09/2026', texto: 'Material complementar enviado na aba de arquivos.' },
        ].map((recado) => (
          <View key={recado.id} style={styles.cardHistorico}>
            <View style={styles.cardHeaderRow}>
              <Ionicons name="calendar-outline" size={14} color={palette.textMuted} />
              <Text style={styles.historicoData}>{recado.data}</Text>
            </View>
            <Text style={styles.cardTextoHistorico}>{recado.texto}</Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: palette.line,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: palette.title },
  btnNovo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: palette.button || '#2E7D32',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  btnNovoTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  conteudo: { padding: 16, gap: 14, paddingBottom: 40 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: palette.title, marginTop: 4 },
  cardDestaque: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  cardHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  cardDestaqueTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  cardTexto: { fontSize: 13, color: '#374151', lineHeight: 18 },
  linkBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#EFF6FF',
    padding: 10,
    borderRadius: 10,
  },
  linkTexto: { fontSize: 12, color: '#2563EB', fontWeight: '600' },
  acoesRow: { flexDirection: 'row', gap: 10, marginTop: 4 },
  btnSecundario: {
    flex: 1,
    height: 38,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnSecundarioTexto: { color: '#4B5563', fontSize: 12, fontWeight: '600' },
  btnPrimario: {
    flex: 1,
    height: 38,
    borderRadius: 10,
    backgroundColor: palette.title,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnPrimarioTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '600' },
  cardHistorico: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 6,
  },
  historicoData: { fontSize: 11, fontWeight: '600', color: palette.textMuted },
  cardTextoHistorico: { fontSize: 12, color: palette.title },
  pressionado: { opacity: 0.8 },
});