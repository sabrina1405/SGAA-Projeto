import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Feather, Fontisto, Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';

import {
  mensagemDeErro,
  redefinirSenha,
  solicitarRecuperacaoSenha,
} from '@/features/auth/authService';

function senhaValida(senha: string) {
  const especiais = senha.replace(/[a-zA-Z0-9\s]/g, '').length;
  return (
    senha.length >= 6 &&
    senha.length <= 100 &&
    /[a-z]/.test(senha) &&
    /[A-Z]/.test(senha) &&
    especiais >= 2
  );
}

export default function RecuperarSenhaScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [codigo, setCodigo] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [codigoSolicitado, setCodigoSolicitado] = useState(false);
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');

  async function solicitarCodigo() {
    if (!email.trim()) {
      setErro('Informe o e-mail.');
      return;
    }
    setErro('');
    setCarregando(true);
    try {
      await solicitarRecuperacaoSenha(email);
      setCodigoSolicitado(true);
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setCarregando(false);
    }
  }

  async function confirmar() {
    if (!codigoSolicitado) {
      await solicitarCodigo();
      return;
    }
    if (!/^[0-9]{6}$/.test(codigo)) {
      setErro('Informe o código de 6 dígitos.');
      return;
    }
    if (!senhaValida(novaSenha)) {
      setErro('A senha deve ter 6 caracteres, letra maiúscula, letra minúscula e 2 caracteres especiais.');
      return;
    }
    if (novaSenha.toLowerCase() === email.trim().toLowerCase()) {
      setErro('A senha não pode ser igual ao e-mail.');
      return;
    }

    setErro('');
    setCarregando(true);
    try {
      await redefinirSenha(email, codigo, novaSenha);
      router.replace('/loginProfessor');
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setCarregando(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <LinearGradient
        colors={['#84009A', '#B2006C', '#D4481A', '#9B6A88', '#4B78E3']}
        start={{ x: 0.15, y: 0 }}
        end={{ x: 0.9, y: 1 }}
        style={styles.card}
      >
        <View style={styles.logo}>
          <Text style={styles.logoText}>SGAA</Text>
        </View>
        <Text style={styles.subtitle}>Sistema de gerenciamento de Aulas e Agendamentos</Text>

        <View style={styles.tituloContainer}>
          <Text style={styles.titulo}>Recuperação de Senha</Text>
        </View>

        <View style={styles.inputContainer}>
          <Fontisto name="email" size={20} color="#666" />
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="E-mail"
            placeholderTextColor="#666"
            keyboardType="email-address"
            autoCapitalize="none"
            editable={!codigoSolicitado}
            style={styles.input}
          />
        </View>

        {codigoSolicitado && (
          <>
            <Text style={styles.label}>Insira o código recebido por e-mail</Text>
            <View style={styles.inputContainer}>
              <Ionicons name="key-outline" size={20} color="#666" />
              <TextInput
                value={codigo}
                onChangeText={(valor) => setCodigo(valor.replace(/[^0-9]/g, '').slice(0, 6))}
                placeholder="Código"
                placeholderTextColor="#666"
                keyboardType="number-pad"
                style={styles.input}
              />
            </View>

            <Pressable style={styles.reenviarContainer} onPress={solicitarCodigo} disabled={carregando}>
              <Text style={styles.reenviar}>Reenviar código</Text>
            </Pressable>

            <Text style={styles.label}>Insira sua nova senha</Text>
            <View style={styles.inputContainer}>
              <Feather name="lock" size={20} color="#666" />
              <TextInput
                value={novaSenha}
                onChangeText={setNovaSenha}
                placeholder="Nova senha"
                placeholderTextColor="#666"
                secureTextEntry={!mostrarSenha}
                style={styles.input}
              />
              <View style={styles.separator} />
              <Pressable onPress={() => setMostrarSenha(!mostrarSenha)}>
                <Ionicons
                  name={mostrarSenha ? 'eye-outline' : 'eye-off-outline'}
                  size={20}
                  color="#666"
                />
              </Pressable>
            </View>
          </>
        )}

        {erro ? <Text style={styles.erroTexto}>{erro}</Text> : null}

        <Pressable style={styles.botaoContainer} onPress={confirmar} disabled={carregando}>
          <LinearGradient colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']} style={styles.botao}>
            {carregando ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.botaoTexto}>
                {codigoSolicitado ? 'Redefinir senha' : 'Enviar código'}
              </Text>
            )}
          </LinearGradient>
        </Pressable>

        <Pressable style={styles.voltar} onPress={() => router.back()}>
          <Text style={styles.voltarTexto}>Voltar para o login</Text>
        </Pressable>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  card: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 24 },
  logo: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3EAF5',
    borderRadius: 18,
    marginBottom: 18,
  },
  logoText: { color: '#84009A', fontSize: 17, fontWeight: '800' },
  subtitle: { color: '#FFFFFF', fontSize: 14, paddingVertical: 20, fontWeight: '300', textAlign: 'center' },
  tituloContainer: {
    width: '82%',
    maxWidth: 360,
    minHeight: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(243, 234, 245, 0.2)',
  },
  titulo: { color: '#FFFFFF', fontSize: 14, fontWeight: '700' },
  inputContainer: {
    width: '82%',
    maxWidth: 360,
    height: 44,
    backgroundColor: '#F2F2F2',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginBottom: 16,
  },
  input: { flex: 1, marginLeft: 14, color: '#222', fontWeight: '600' },
  separator: { width: 1, height: 20, backgroundColor: '#D6D6D6', marginRight: 12 },
  label: { width: '82%', maxWidth: 360, marginBottom: 8, color: '#FFFFFF', fontSize: 12 },
  reenviarContainer: { width: '82%', maxWidth: 360, alignItems: 'flex-end', marginBottom: 16 },
  reenviar: { color: '#FFFFFF', fontSize: 12, textDecorationLine: 'underline' },
  erroTexto: { width: '82%', maxWidth: 360, color: '#FFE2E2', fontSize: 12, textAlign: 'center', marginBottom: 12 },
  botaoContainer: { width: 170 },
  botao: { height: 42, borderRadius: 8, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  botaoTexto: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
  voltar: { marginTop: 16 },
  voltarTexto: { color: '#FFFFFF', fontSize: 12, textDecorationLine: 'underline' },
});
