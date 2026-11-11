import { useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
  TextInput,
  Pressable,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import DateTimePicker, { DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { palette } from '@/constants/palette';
import { USAR_MOCK, criarAula, mensagemDeErro } from '@/features/agenda/api';
import { dataBRparaChave, paraISO } from '@/features/agenda/mappers';

// Formatadores visuais
const formatarDataBR = (date: Date) => {
  const dia = String(date.getDate()).padStart(2, '0');
  const mes = String(date.getMonth() + 1).padStart(2, '0');
  const ano = date.getFullYear();
  return `${dia}/${mes}/${ano}`;
};

const formatarHora = (date: Date) => {
  const horas = String(date.getHours()).padStart(2, '0');
  const minutos = String(date.getMinutes()).padStart(2, '0');
  return `${horas}:${minutos}`;
};

// Conversores para HTML na Web (YYYY-MM-DD e HH:MM)
const formatarDataWeb = (date: Date) => {
  const dia = String(date.getDate()).padStart(2, '0');
  const mes = String(date.getMonth() + 1).padStart(2, '0');
  const ano = date.getFullYear();
  return `${ano}-${mes}-${dia}`;
};

const formatarHoraWeb = (date: Date) => {
  return formatarHora(date);
};

const lerIds = (texto: string) =>
  texto
    .split(',')
    .map((s) => parseInt(s.trim(), 10))
    .filter((n) => Number.isInteger(n) && n > 0);

export default function CriarAulaScreen() {
  const router = useRouter();

  const [titulo, setTitulo] = useState('');

  // Estados com Objetos Date
  const [dataObj, setDataObj] = useState(new Date());
  const [horaInicioObj, setHoraInicioObj] = useState(() => {
    const d = new Date();
    d.setHours(10, 0, 0, 0);
    return d;
  });
  const [horaFimObj, setHoraFimObj] = useState(() => {
    const d = new Date();
    d.setHours(11, 0, 0, 0);
    return d;
  });

  // Controle do picker no mobile
  const [tipoPickerAtivo, setTipoPickerAtivo] = useState<'data' | 'inicio' | 'fim' | null>(null);

  const [aluno, setAluno] = useState('');
  const [grupo, setGrupo] = useState('');
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  const handleSalvar = async () => {
    if (salvando) return;

    const dataTexto = formatarDataBR(dataObj);
    const horaInicioTexto = formatarHora(horaInicioObj);
    const horaFimTexto = formatarHora(horaFimObj);

    const dataChave = dataBRparaChave(dataTexto);
    const alunoIds = lerIds(aluno);
    const grupoIds = lerIds(grupo);
    const nomes = aluno.split(',').map((s) => s.trim()).filter(Boolean);

    if (!titulo.trim()) return setErro('Informe o título da aula.');
    if (!dataChave) return setErro('Data inválida.');
    if (horaFimObj <= horaInicioObj) return setErro('O horário de fim deve ser depois do início.');

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
        inicio: paraISO(dataChave, horaInicioTexto),
        fim: paraISO(dataChave, horaFimTexto),
        aluno_ids: alunoIds,
        grupo_ids: grupoIds,
        nomes_mock: nomes,
      });
      router.navigate({ pathname: '/professor/agenda', params: { data: dataChave } });
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setSalvando(false);
    }
  };

  // Tratores de mudança no Mobile
  const onDateChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (Platform.OS === 'android') setTipoPickerAtivo(null);
    if (event.type === 'set' && selectedDate) setDataObj(selectedDate);
  };

  const onInicioChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (Platform.OS === 'android') setTipoPickerAtivo(null);
    if (event.type === 'set' && selectedDate) setHoraInicioObj(selectedDate);
  };

  const onFimChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (Platform.OS === 'android') setTipoPickerAtivo(null);
    if (event.type === 'set' && selectedDate) setHoraFimObj(selectedDate);
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
        <View style={styles.cardForm}>
          <Text style={styles.cardHeaderTitle}>Informações de Aula</Text>

          {/* Título */}
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

          {/* Data da Aula */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Data da Aula</Text>
            {Platform.OS === 'web' ? (
              <input
                type="date"
                style={styles.inputWeb as any}
                value={formatarDataWeb(dataObj)}
                onChange={(e) => {
                  if (e.target.value) {
                    const [ano, mes, dia] = e.target.value.split('-').map(Number);
                    setDataObj(new Date(ano, mes - 1, dia));
                  }
                }}
              />
            ) : (
              <>
                <Pressable
                  style={({ pressed }) => [styles.selectorButton, pressed && styles.pressionado]}
                  onPress={() => setTipoPickerAtivo('data')}
                >
                  <Ionicons name="calendar-outline" size={20} color={palette.title} />
                  <Text style={styles.selectorText}>{formatarDataBR(dataObj)}</Text>
                  <Ionicons name="chevron-down" size={16} color={palette.textMuted} style={{ marginLeft: 'auto' }} />
                </Pressable>

                {tipoPickerAtivo === 'data' && (
                  <DateTimePicker
                    value={dataObj}
                    mode="date"
                    display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                    onChange={onDateChange}
                  />
                )}
                {Platform.OS === 'ios' && tipoPickerAtivo === 'data' && (
                  <Pressable style={styles.btnConfirmarPicker} onPress={() => setTipoPickerAtivo(null)}>
                    <Text style={styles.btnConfirmarTexto}>Concluir Data</Text>
                  </Pressable>
                )}
              </>
            )}
          </View>

          {/* Horários (Início e Fim) */}
          <View style={styles.linhaDupla}>
            {/* Início */}
            <View style={[styles.inputGroup, { flex: 1 }]}>
              <Text style={styles.label}>Início</Text>
              {Platform.OS === 'web' ? (
                <input
                  type="time"
                  style={styles.inputWeb as any}
                  value={formatarHoraWeb(horaInicioObj)}
                  onChange={(e) => {
                    if (e.target.value) {
                      const [h, m] = e.target.value.split(':').map(Number);
                      const d = new Date(horaInicioObj);
                      d.setHours(h, m, 0, 0);
                      setHoraInicioObj(d);
                    }
                  }}
                />
              ) : (
                <>
                  <Pressable
                    style={({ pressed }) => [styles.selectorButton, pressed && styles.pressionado]}
                    onPress={() => setTipoPickerAtivo('inicio')}
                  >
                    <Ionicons name="time-outline" size={18} color={palette.title} />
                    <Text style={styles.selectorText}>{formatarHora(horaInicioObj)}</Text>
                  </Pressable>

                  {tipoPickerAtivo === 'inicio' && (
                    <DateTimePicker
                      value={horaInicioObj}
                      mode="time"
                      is24Hour={true}
                      display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                      onChange={onInicioChange}
                    />
                  )}
                  {Platform.OS === 'ios' && tipoPickerAtivo === 'inicio' && (
                    <Pressable style={styles.btnConfirmarPicker} onPress={() => setTipoPickerAtivo(null)}>
                      <Text style={styles.btnConfirmarTexto}>Concluir Início</Text>
                    </Pressable>
                  )}
                </>
              )}
            </View>

            {/* Fim */}
            <View style={[styles.inputGroup, { flex: 1 }]}>
              <Text style={styles.label}>Fim</Text>
              {Platform.OS === 'web' ? (
                <input
                  type="time"
                  style={styles.inputWeb as any}
                  value={formatarHoraWeb(horaFimObj)}
                  onChange={(e) => {
                    if (e.target.value) {
                      const [h, m] = e.target.value.split(':').map(Number);
                      const d = new Date(horaFimObj);
                      d.setHours(h, m, 0, 0);
                      setHoraFimObj(d);
                    }
                  }}
                />
              ) : (
                <>
                  <Pressable
                    style={({ pressed }) => [styles.selectorButton, pressed && styles.pressionado]}
                    onPress={() => setTipoPickerAtivo('fim')}
                  >
                    <Ionicons name="time-outline" size={18} color={palette.title} />
                    <Text style={styles.selectorText}>{formatarHora(horaFimObj)}</Text>
                  </Pressable>

                  {tipoPickerAtivo === 'fim' && (
                    <DateTimePicker
                      value={horaFimObj}
                      mode="time"
                      is24Hour={true}
                      display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                      onChange={onFimChange}
                    />
                  )}
                  {Platform.OS === 'ios' && tipoPickerAtivo === 'fim' && (
                    <Pressable style={styles.btnConfirmarPicker} onPress={() => setTipoPickerAtivo(null)}>
                      <Text style={styles.btnConfirmarTexto}>Concluir Fim</Text>
                    </Pressable>
                  )}
                </>
              )}
            </View>
          </View>

          {/* Alunos */}
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

          {/* Grupo */}
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

  inputWeb: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: palette.title,
    fontWeight: '500',
    width: '100%',
    boxSizing: 'border-box',
  } as any,
  selectorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  selectorText: {
    fontSize: 13,
    color: palette.title,
    fontWeight: '600',
  },
  btnConfirmarPicker: {
    backgroundColor: palette.button || '#2E7D32',
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 4,
  },
  btnConfirmarTexto: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
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