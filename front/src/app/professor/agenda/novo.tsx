import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { palette } from '@/constants/palette';
import { USAR_MOCK, criarAula, mensagemDeErro } from '@/features/agenda/api';
import { dataBRparaChave, paraISO, parseHorario } from '@/features/agenda/mappers';

// Modo real: aceita IDs separados por vírgula (ex.: "1,2") até existir a seleção de alunos/grupos.
const lerIds = (texto: string) =>
  texto
    .split(',')
    .map((s) => parseInt(s.trim(), 10))
    .filter((n) => Number.isInteger(n) && n > 0);

export default function CriarAulaScreen() {
  const router = useRouter();

  const [titulo, setTitulo] = useState('');
  const [data, setData] = useState('');
  const [horario, setHorario] = useState('');
  const [aluno, setAluno] = useState('');
  const [grupo, setGrupo] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  const handleSalvar = async () => {
    if (salvando) return;

    const dataChave = dataBRparaChave(data);
    const hora = parseHorario(horario);
    const alunoIds = lerIds(aluno);
    const grupoIds = lerIds(grupo);
    // Modo demonstração: o campo de alunos aceita nomes (ex.: "José, Maria")
    const nomes = aluno.split(',').map((s) => s.trim()).filter(Boolean);

    if (!titulo.trim()) return setErro('Informe o título da aula.');
    if (!dataChave) return setErro('Data inválida. Use DD/MM/AAAA.');
    if (!hora) return setErro('Horário inválido. Use o formato 10:00 às 11:00.');
    if (hora.fim <= hora.inicio) return setErro('O fim deve ser depois do início.');
    if (USAR_MOCK) {
      if (nomes.length === 0) return setErro('Informe ao menos um aluno.');
    } else if (alunoIds.length === 0 && grupoIds.length === 0) {
      return setErro('Informe ao menos um aluno ou grupo (IDs separados por vírgula).');
    }

    setErro(null);
    setSalvando(true);
    try {
      await criarAula({
        titulo: titulo.trim(),
        inicio: paraISO(dataChave, hora.inicio),
        fim: paraISO(dataChave, hora.fim),
        aluno_ids: alunoIds,
        grupo_ids: grupoIds,
        nomes_mock: nomes,
      });
      // volta para a agenda já no dia da aula
      router.navigate({ pathname: '/professor/agenda', params: { data: dataChave } });
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setSalvando(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        
        <View style={styles.cardForm}>
          <Text style={styles.cardHeaderTitle}>Informações de Aula</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Título</Text>
            <TextInput
              style={styles.input}
              value={titulo}
              onChangeText={setTitulo}
              maxLength={75}
              placeholder="Aula de Espanhol 03"
              placeholderTextColor="#9CA3AF"
            />
          </View>

          <View style={styles.linhaDupla}>
            <View style={[styles.inputGroup, { flex: 1 }]}>
              <Text style={styles.label}>Data</Text>
              <TextInput
                style={styles.input}
                value={data}
                onChangeText={setData}
                placeholder="10/11/2026"
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <View style={[styles.inputGroup, { flex: 1 }]}>
              <Text style={styles.label}>Horário</Text>
              <TextInput
                style={styles.input}
                value={horario}
                onChangeText={setHorario}
                placeholder="10:00 às 11:00"
                placeholderTextColor="#9CA3AF"
              />
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Selecionar Alunos</Text>
            <TextInput
              style={styles.input}
              placeholder={USAR_MOCK ? 'Nome do aluno (ex.: José)' : 'IDs dos alunos (ex.: 1,2)'}
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

        {erro && <Text style={styles.erro}>{erro}</Text>}

        {/* Botões de Ação */}
        <View style={styles.acoesRow}>
          <Pressable 
            style={({ pressed }) => [styles.btnAcao, styles.btnCancelar, pressed && styles.pressionado]} 
            onPress={() => router.back()}
          >
            <Text style={styles.btnAcaoTexto}>Cancelar</Text>
          </Pressable>

          <Pressable 
            disabled={salvando}
            style={({ pressed }) => [styles.btnAcao, styles.btnSalvar, (pressed || salvando) && styles.pressionado]} 
            onPress={handleSalvar}
          >
            <Text style={styles.btnAcaoTexto}>{salvando ? 'Salvando...' : 'Salvar'}</Text>
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
  cardHeaderTitle: { fontSize: 14, fontWeight: '700', color: palette.title, marginBottom: 4 },
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
  erro: { color: '#C62828', fontSize: 12, fontWeight: '600' },
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