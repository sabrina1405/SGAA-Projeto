import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, View, TextInput, Pressable } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { palette } from '@/constants/palette';
import {
  criarRecado,
  mensagemDeErro,
  obterRecadoGeral,
  salvarRecadoGeral,
} from '@/services/recado-service';

export default function NovaRecadoScreen() {
  const router = useRouter();
  const { geral } = useLocalSearchParams<{ geral?: string }>();
  const modoGeral = geral === '1';

  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [salvando, setSalvando] = useState(false);

  // Ao editar o recado geral, já abre com o texto atual.
  useEffect(() => {
    if (!modoGeral) return;
    obterRecadoGeral()
      .then((recado) => {
        if (recado) setDescricao(recado.conteudo);
      })
      .catch(() => {});
  }, [modoGeral]);

  async function salvar() {
    if (!descricao.trim()) {
      Alert.alert('Preencha a descrição');
      return;
    }

    setSalvando(true);
    try {
      if (modoGeral) {
        await salvarRecadoGeral(descricao.trim());
      } else {
        await criarRecado({ conteudo: descricao.trim(), todos_alunos: true });
      }
      router.back();
    } catch (erro) {
      Alert.alert('Erro', mensagemDeErro(erro, 'Falha ao salvar o recado.'));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.conteudo}>
      <View style={styles.cardForm}>
        <Text style={styles.label}>Título Recado*</Text>
        <TextInput style={styles.input} value={titulo} onChangeText={setTitulo} placeholder="Adicione uma descrição para a Recado" placeholderTextColor="#9CA3AF" />

        <Text style={styles.label}>Descrição*</Text>
        <TextInput style={[styles.input, { height: 80 }]} multiline value={descricao} onChangeText={setDescricao} placeholder="Adicione uma descrição para a recado" placeholderTextColor="#9CA3AF" />
      </View>

      <View style={styles.acoesRow}>
        <Pressable style={[styles.btnAcao, styles.btnCancelar]} onPress={() => router.back()} disabled={salvando}>
          <Text style={styles.btnTexto}>Cancelar</Text>
        </Pressable>
        <Pressable style={[styles.btnAcao, styles.btnSalvar, salvando && { opacity: 0.8 }]} onPress={salvar} disabled={salvando}>
          <Text style={styles.btnTexto}>{salvando ? 'Salvando...' : 'Salvar'}</Text>
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