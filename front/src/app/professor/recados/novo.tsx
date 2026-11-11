import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TextInput, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { palette } from '@/constants/palette';

export default function NovaRecadoScreen() {
  const router = useRouter();
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');

  return (
    <ScrollView contentContainerStyle={styles.conteudo}>
      <View style={styles.cardForm}>
        <Text style={styles.label}>Título Recado*</Text>
        <TextInput style={styles.input} value={titulo} onChangeText={setTitulo} placeholder="Adicione uma descrição para a Recado" placeholderTextColor="#9CA3AF" />

        <Text style={styles.label}>Descrição*</Text>
        <TextInput style={[styles.input, { height: 80 }]} multiline value={descricao} onChangeText={setDescricao} placeholder="Adicione uma descrição para a recado" placeholderTextColor="#9CA3AF" />
      </View>

      <View style={styles.acoesRow}>
        <Pressable style={[styles.btnAcao, styles.btnCancelar]} onPress={() => router.back()}>
          <Text style={styles.btnTexto}>Cancelar</Text>
        </Pressable>
        <Pressable style={[styles.btnAcao, styles.btnSalvar]} onPress={() => router.back()}>
          <Text style={styles.btnTexto}>Salvar</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  conteudo: { padding: 16, gap: 16, backgroundColor: palette.background, flexGrow: 1 },
  cardForm: { backgroundColor: '#fff', borderRadius: 16, padding: 16, gap: 12, borderWidth: 1, borderColor: palette.line },
  label: { fontSize: 12, fontWeight: '600', color: palette.title },
  input: { backgroundColor: '#F9FAFB', borderWidth: 1, borderColor: palette.line, borderRadius: 10, padding: 10, fontSize: 13 },
  acoesRow: { flexDirection: 'row', gap: 12, marginTop: 'auto' },
  btnAcao: { flex: 1, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  btnCancelar: { backgroundColor: '#C62828' },
  btnSalvar: { backgroundColor: '#2E7D32' },
  btnTexto: { color: '#fff', fontWeight: '700', fontSize: 13 },
});