import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { palette } from '@/constants/palette';

export default function EditarAulaScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();

  const [titulo, setTitulo] = useState('Aula de Espanhol 03');
  const [data, setData] = useState('00/00/0000');
  const [horario, setHorario] = useState('00:00 ás 00:30');
  const [aluno, setAluno] = useState('Nome do Aluno');

  const handleSalvar = () => {
    // TODO: Lógica para atualizar a aula
    router.back();
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        
        <View style={styles.cardForm}>
          <View style={styles.cardHeaderRow}>
            <Text style={styles.cardHeaderTitle}>Informações de Aula (ID: {id})</Text>
            <Ionicons name="create-outline" size={18} color={palette.header} />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Título</Text>
            <TextInput
              style={styles.input}
              value={titulo}
              onChangeText={setTitulo}
            />
          </View>

          <View style={styles.linhaDupla}>
            <View style={[styles.inputGroup, { flex: 1 }]}>
              <Text style={styles.label}>Data</Text>
              <TextInput
                style={styles.input}
                value={data}
                onChangeText={setData}
              />
            </View>

            <View style={[styles.inputGroup, { flex: 1 }]}>
              <Text style={styles.label}>Horário</Text>
              <TextInput
                style={styles.input}
                value={horario}
                onChangeText={setHorario}
              />
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Aluno</Text>
            <TextInput
              style={styles.input}
              value={aluno}
              onChangeText={setAluno}
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
            onPress={handleSalvar}
          >
            <Text style={styles.btnAcaoTexto}>Salvar</Text>
          </Pressable>
        </View>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 40, gap: 20 },
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
  cardHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  cardHeaderTitle: { fontSize: 14, fontWeight: '700', color: palette.title },
  inputGroup: { gap: 6 },
  linhaDupla: { flexDirection: 'row', gap: 10 },
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
  acoesRow: { flexDirection: 'row', gap: 12, marginTop: 10 },
  btnAcao: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  btnCancelar: { backgroundColor: '#C62828' },
  btnSalvar: { backgroundColor: '#2E7D32' },
  btnAcaoTexto: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
  pressionado: { opacity: 0.8 },
});