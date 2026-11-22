import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { palette } from '@/constants/palette';

export default function ArquivosScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <View style={styles.headerTop}>
        <Text style={styles.headerTitle}>Biblioteca de Arquivos</Text>
        <Pressable
          style={({ pressed }) => [styles.btnNovo, pressed && styles.pressionado]}
          onPress={() => router.push('/professor/arquivos/novo')}
        >
          <Ionicons name="cloud-upload-outline" size={16} color="#FFFFFF" />
          <Text style={styles.btnNovoTexto}>Enviar Arquivo</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionTitle}>Arquivos Recentes</Text>

        {/* Item de Arquivo 1 (PDF) */}
        <View style={styles.cardArquivo}>
          <View style={[styles.iconBox, { backgroundColor: '#FEE2E2' }]}>
            <Ionicons name="document-text" size={22} color="#DC2626" />
          </View>
          <View style={styles.infoBox}>
            <Text style={styles.fileName}>Lição_04_Gramatica_Avançada.pdf</Text>
            <Text style={styles.fileMeta}>PDF • 2.4 MB • Enviado em 10/10/2026</Text>
          </View>
          <Pressable style={styles.actionBtn}>
            <Ionicons name="download-outline" size={18} color="#4B5563" />
          </Pressable>
        </View>

        {/* Item de Arquivo 2 (Atividade DOCX) */}
        <View style={styles.cardArquivo}>
          <View style={[styles.iconBox, { backgroundColor: '#DBEAFE' }]}>
            <Ionicons name="document" size={22} color="#2563EB" />
          </View>
          <View style={styles.infoBox}>
            <Text style={styles.fileName}>Exercicio_Conversacao_Espanhol.docx</Text>
            <Text style={styles.fileMeta}>Word • 850 KB • Enviado em 05/10/2026</Text>
          </View>
          <Pressable style={styles.actionBtn}>
            <Ionicons name="download-outline" size={18} color="#4B5563" />
          </Pressable>
        </View>

        {/* Item de Arquivo 3 (Material Complementar) */}
        <View style={styles.cardArquivo}>
          <View style={[styles.iconBox, { backgroundColor: '#FEF3C7' }]}>
            <Ionicons name="musical-notes" size={22} color="#D97706" />
          </View>
          <View style={styles.infoBox}>
            <Text style={styles.fileName}>Audio_Listening_Aula03.mp3</Text>
            <Text style={styles.fileMeta}>Áudio • 5.1 MB • Enviado em 01/10/2026</Text>
          </View>
          <Pressable style={styles.actionBtn}>
            <Ionicons name="download-outline" size={18} color="#4B5563" />
          </Pressable>
        </View>
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
  conteudo: { padding: 16, gap: 12, paddingBottom: 40 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: palette.title, marginTop: 4 },
  cardArquivo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 1,
  },
  iconBox: { width: 42, height: 42, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  infoBox: { flex: 1, gap: 2 },
  fileName: { fontSize: 13, fontWeight: '700', color: palette.title },
  fileMeta: { fontSize: 11, color: palette.textMuted },
  actionBtn: { padding: 8, borderRadius: 8, backgroundColor: '#F3F4F6' },
  pressionado: { opacity: 0.8 },
});