import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TextInput, Pressable, Switch, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { palette } from '@/constants/palette';

export default function NovoGrupoScreen() {
  const router = useRouter();

  const [nomeGrupo, setNomeGrupo] = useState('');
  const [selecionarAlunos, setSelecionarAlunos] = useState('');
  const [frequencia, setFrequencia] = useState('');
  const [qtdAulas, setQtdAulas] = useState('');
  const [dataIniciro, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [aulasEmGrupo, setAulasEmGrupo] = useState(false);

  const handleSalvar = () => {
    // TODO: Lógica para salvar o grupo
    router.back();
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        
        {/* Seção 1: Informações Gerais */}
        <View style={styles.secaoContainer}>
          <Text style={styles.secaoTitulo}>Informações Gerais</Text>

          <View style={styles.cardForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Nome do Grupo*</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Turma Espanhol B1"
                placeholderTextColor="#9CA3AF"
                value={nomeGrupo}
                onChangeText={setNomeGrupo}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Selecionar Alunos</Text>
              <TextInput
                style={styles.input}
                placeholder="Adicionar alunos ao grupo"
                placeholderTextColor="#9CA3AF"
                value={selecionarAlunos}
                onChangeText={setSelecionarAlunos}
              />
            </View>
          </View>
        </View>

        {/* Seção 2: Informações de Aulas */}
        <View style={styles.secaoContainer}>
          <Text style={styles.secaoTitulo}>Informações de Aulas</Text>

          <View style={styles.cardForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Frequência</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Semanal / Terças e Quintas"
                placeholderTextColor="#9CA3AF"
                value={frequencia}
                onChangeText={setFrequencia}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Quantidade de Aulas</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: 20"
                placeholderTextColor="#9CA3AF"
                value={qtdAulas}
                onChangeText={setQtdAulas}
                keyboardType="numeric"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Data de Início das Aulas</Text>
              <View style={styles.inputIconWrapper}>
                <TextInput
                  style={[styles.input, { flex: 1, borderWidth: 0, backgroundColor: 'transparent' }]}
                  placeholder="DD/MM/AAAA"
                  placeholderTextColor="#9CA3AF"
                  value={dataIniciro}
                  onChangeText={setDataInicio}
                />
                <Ionicons name="calendar-outline" size={20} color={palette.textMuted} style={{ marginRight: 12 }} />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Data de Fim das Aulas</Text>
              <View style={styles.inputIconWrapper}>
                <TextInput
                  style={[styles.input, { flex: 1, borderWidth: 0, backgroundColor: 'transparent' }]}
                  placeholder="DD/MM/AAAA"
                  placeholderTextColor="#9CA3AF"
                  value={dataFim}
                  onChangeText={setDataFim}
                />
                <Ionicons name="calendar-outline" size={20} color={palette.textMuted} style={{ marginRight: 12 }} />
              </View>
            </View>

            {/* Toggle: Aulas em Grupo */}
            <View style={styles.switchRow}>
              <Text style={styles.label}>Aulas em Grupo</Text>
              <Switch
                trackColor={{ false: '#D1D5DB', true: '#C5CAE9' }}
                thumbColor={aulasEmGrupo ? palette.header : '#F4F3F4'}
                onValueChange={setAulasEmGrupo}
                value={aulasEmGrupo}
              />
            </View>
          </View>
        </View>

        {/* Botões de Ação Inferiores */}
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

  secaoContainer: { gap: 8 },
  secaoTitulo: { fontSize: 14, fontWeight: '700', color: palette.title, paddingHorizontal: 4 },

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
  inputIconWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },

  acoesRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 10,
  },
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