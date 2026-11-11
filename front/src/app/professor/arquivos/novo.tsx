import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { palette } from '@/constants/palette';

export default function NovoArquivoScreen() {
  const router = useRouter();
  const [titulo, setTitulo] = useState('');
  const [aluno, setAluno] = useState('');
  const [grupo, setGrupo] = useState('');

  return (
    <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
      <View style={styles.cardForm}>
        <Text style={styles.cardHeaderTitle}>Detalhes do Material</Text>

        {/* Título do Arquivo */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Título do Arquivo / Lição*</Text>
          <TextInput
            style={styles.input}
            value={titulo}
            onChangeText={setTitulo}
            placeholder="Ex.: Apostila de Verbos - Módulo 2"
            placeholderTextColor="#9CA3AF"
          />
        </View>

        {/* Zona de Upload / Seleção de Arquivo */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Arquivo (PDF, DOCX, Mídia)</Text>
          <Pressable style={styles.uploadBox}>
            <View style={styles.uploadIconCircle}>
              <Ionicons name="cloud-upload-outline" size={24} color={palette.title} />
            </View>
            <Text style={styles.uploadTextMain}>Toque para selecionar o arquivo</Text>
            <Text style={styles.uploadTextSub}>Suporta PDF, Word e compactados (máx. 25MB)</Text>
          </Pressable>
        </View>

        {/* Destinatários */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Selecionar Alunos</Text>
          <TextInput
            style={styles.input}
            placeholder="Nome ou ID do aluno (opcional)"
            placeholderTextColor="#9CA3AF"
            value={aluno}
            onChangeText={setAluno}
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Selecionar Grupo</Text>
          <TextInput
            style={styles.input}
            placeholder="Opcional"
            placeholderTextColor="#9CA3AF"
            value={grupo}
            onChangeText={setGrupo}
          />
        </View>
      </View>

      {/* Botões de Ação */}
      <View style={styles.acoesRow}>
        <Pressable
          style={({ pressed }) => [styles.btnAcao, styles.btnCancelar, pressed && styles.pressionado]}
          onPress={() => router.back()}
        >
          <Text style={styles.btnAcaoTexto}>Cancelar</Text>
        </Pressable>

        <Pressable
          style={({ pressed }) => [styles.btnAcao, styles.btnSalvar, pressed && styles.pressionado]}
          onPress={() => router.back()}
        >
          <Text style={styles.btnAcaoTexto}>Enviar Arquivo</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  conteudo: { padding: 16, paddingBottom: 40, gap: 20, backgroundColor: palette.background, flexGrow: 1 },
  cardForm: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeaderTitle: { fontSize: 14, fontWeight: '700', color: palette.title, marginBottom: 4 },
  inputGroup: { gap: 6 },
  label: { fontSize: 11, fontWeight: '600', color: palette.title },
  input: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: palette.title,
    fontWeight: '500',
  },
  uploadBox: {
    borderWidth: 2,
    borderColor: palette.line,
    borderStyle: 'dashed',
    borderRadius: 12,
    backgroundColor: '#F9FAFB',
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  uploadIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
  },
  uploadTextMain: { fontSize: 13, fontWeight: '700', color: palette.title },
  uploadTextSub: { fontSize: 11, color: palette.textMuted },
  acoesRow: { flexDirection: 'row', gap: 12, marginTop: 10 },
  btnAcao: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2,
  },
  btnCancelar: { backgroundColor: '#C62828' },
  btnSalvar: { backgroundColor: '#2E7D32' },
  btnAcaoTexto: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
  pressionado: { opacity: 0.8 },
});