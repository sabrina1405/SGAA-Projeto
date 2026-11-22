import { useState } from 'react';
import { Alert, Platform, ScrollView, StyleSheet, Text, View, TextInput, Pressable } from 'react-native';
import DateTimePicker, { DateTimePickerAndroid } from '@react-native-community/datetimepicker';
import { useRouter } from 'expo-router';
import { palette } from '@/constants/palette';
import { criarAtividade } from '@/features/atividades/service';

function dois(n: number) {
  return String(n).padStart(2, '0');
}

// DD/MM/AAAA HH:mm
function formatar(data: Date) {
  return `${dois(data.getDate())}/${dois(data.getMonth() + 1)}/${data.getFullYear()} ${dois(data.getHours())}:${dois(data.getMinutes())}`;
}

function mensagemDeErro(erro: unknown) {
  const detalhe = (erro as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detalhe === 'string') return detalhe;
  if (Array.isArray(detalhe)) {
    const msgs = detalhe.map((d) => (typeof d?.msg === 'string' ? d.msg : null)).filter(Boolean);
    if (msgs.length) return msgs.join('\n');
  }
  return 'Falha ao salvar a atividade.';
}

type CampoDataHoraProps = { valor: Date; onChange: (data: Date) => void; desabilitado?: boolean };

function CampoDataHora({ valor, onChange, desabilitado }: CampoDataHoraProps) {
  const [aberto, setAberto] = useState(false);

  function abrir() {
    if (Platform.OS === 'android') {
      // No Android a data e a hora são escolhidas em duas etapas.
      DateTimePickerAndroid.open({
        value: valor,
        mode: 'date',
        onChange: (evento, data) => {
          if (evento.type !== 'set' || !data) return;
          DateTimePickerAndroid.open({
            value: data,
            mode: 'time',
            is24Hour: true,
            onChange: (eventoHora, dataHora) => {
              if (eventoHora.type === 'set' && dataHora) onChange(dataHora);
            },
          });
        },
      });
    } else {
      setAberto((atual) => !atual);
    }
  }

  return (
    <View style={{ gap: 8 }}>
      <Pressable style={styles.input} onPress={abrir} disabled={desabilitado}>
        <Text style={styles.campoDataTexto}>{formatar(valor)}</Text>
      </Pressable>
      {Platform.OS === 'ios' && aberto && (
        <DateTimePicker
          value={valor}
          mode="datetime"
          display="spinner"
          onChange={(_, data) => data && onChange(data)}
        />
      )}
    </View>
  );
}

export default function NovaAtividadeScreen() {
  const router = useRouter();
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [liberarEm, setLiberarEm] = useState(() => new Date());
  const [venceEm, setVenceEm] = useState(() => new Date(Date.now() + 7 * 24 * 60 * 60 * 1000));
  const [salvando, setSalvando] = useState(false);

  async function salvar() {
    if (!titulo.trim() || !descricao.trim()) {
      Alert.alert('Preencha o título e a descrição');
      return;
    }
    if (venceEm <= liberarEm) {
      Alert.alert('Datas inválidas', 'O vencimento precisa ser depois da liberação.');
      return;
    }

    setSalvando(true);
    try {
      await criarAtividade({
        titulo: titulo.trim(),
        descricao: descricao.trim(),
        liberar_em: liberarEm.toISOString(),
        vence_em: venceEm.toISOString(),
        todos_alunos: true,
      });
      router.back();
    } catch (erro) {
      Alert.alert('Erro', mensagemDeErro(erro));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.conteudo}>
      <View style={styles.cardForm}>
        <Text style={styles.label}>Título Atividade*</Text>
        <TextInput style={styles.input} value={titulo} onChangeText={setTitulo} maxLength={75} placeholder="Adicione uma descrição para a atividade" placeholderTextColor="#9CA3AF" />

        <Text style={styles.label}>Descrição*</Text>
        <TextInput style={[styles.input, { height: 80 }]} multiline value={descricao} onChangeText={setDescricao} placeholder="Adicione uma descrição para a atividade" placeholderTextColor="#9CA3AF" />

        <Text style={styles.label}>Liberar em*</Text>
        <CampoDataHora valor={liberarEm} onChange={setLiberarEm} desabilitado={salvando} />

        <Text style={styles.label}>Vence em*</Text>
        <CampoDataHora valor={venceEm} onChange={setVenceEm} desabilitado={salvando} />
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
  campoDataTexto: { fontSize: 13, color: palette.title },
  acoesRow: { flexDirection: 'row', gap: 12, marginTop: 'auto' },
  btnAcao: { flex: 1, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  btnCancelar: { backgroundColor: '#C62828' },
  btnSalvar: { backgroundColor: '#2E7D32' },
  btnTexto: { color: '#fff', fontWeight: '700', fontSize: 13 },
});