import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { criarAluno, mensagemDeErroAlunos } from '@/features/alunos/alunosService';
import { palette } from '@/constants/palette';

export default function NovoAlunoScreen() {
  const router = useRouter();

  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [qtdPagamentos, setQtdPagamentos] = useState('');
  const [valorCobranca, setValorCobranca] = useState('');
  const [formaPagamento, setFormaPagamento] = useState('');
  const [dataVencimento, setDataVencimento] = useState('');

  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  // Por enquanto a API só recebe nome e e-mail; os campos de cobrança ainda não são enviados.
  const handleSalvar = async () => {
    if (!nome.trim() || !email.trim()) {
      setErro('Informe o nome completo e o e-mail.');
      return;
    }
    setErro('');
    setSalvando(true);
    try {
      await criarAluno({ nome_completo: nome, email });
      router.back();
    } catch (e) {
      setErro(mensagemDeErroAlunos(e));
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
        
        {/* Seção 1: Informações Gerais */}
        <View style={styles.secaoContainer}>
          <View style={styles.secaoTituloRow}>
            <Text style={styles.secaoTitulo}>Informações Gerais - Pré cadastramento</Text>
            <Ionicons name="information-circle-outline" size={18} color={palette.header} />
          </View>

          <View style={styles.cardForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Nome Completo*</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Ana Souza"
                placeholderTextColor="#9CA3AF"
                value={nome}
                onChangeText={setNome}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>E-mail*</Text>
              <TextInput
                style={styles.input}
                placeholder="aluno@email.com"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>
          </View>
        </View>

        {/* Seção 2: Informações de Cobrança */}
        <View style={styles.secaoContainer}>
          <Text style={styles.secaoTitulo}>Informações de Cobranças</Text>

          <View style={styles.cardForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Quantidade de Pagamentos</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: 12"
                placeholderTextColor="#9CA3AF"
                value={qtdPagamentos}
                onChangeText={setQtdPagamentos}
                keyboardType="numeric"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Valor de Cobrança</Text>
              <TextInput
                style={styles.input}
                placeholder="R$ 0,00"
                placeholderTextColor="#9CA3AF"
                value={valorCobranca}
                onChangeText={setValorCobranca}
                keyboardType="numeric"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Forma de Pagamento</Text>
              <TextInput
                style={styles.input}
                placeholder="Ex: Pix / Cartão / Boleto"
                placeholderTextColor="#9CA3AF"
                value={formaPagamento}
                onChangeText={setFormaPagamento}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Data de Vencimento</Text>
              <View style={styles.inputIconWrapper}>
                <TextInput
                  style={[styles.input, { flex: 1, borderWidth: 0, backgroundColor: 'transparent' }]}
                  placeholder="DD/MM/AAAA"
                  placeholderTextColor="#9CA3AF"
                  value={dataVencimento}
                  onChangeText={setDataVencimento}
                />
                <Ionicons name="calendar-outline" size={20} color={palette.textMuted} style={{ marginRight: 12 }} />
              </View>
            </View>
          </View>
        </View>

        {erro ? <Text style={styles.erroTexto}>{erro}</Text> : null}

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
            disabled={salvando}
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

  secaoContainer: { gap: 8 },
  secaoTituloRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 4,
  },
  secaoTitulo: { fontSize: 14, fontWeight: '700', color: palette.title },

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

  erroTexto: { color: '#C62828', fontSize: 12, fontWeight: '600', textAlign: 'center' },

  pressionado: { opacity: 0.8 },
});