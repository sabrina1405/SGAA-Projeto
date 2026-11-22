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
import { Fontisto, Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';

import { login, mensagemDeErro } from '@/features/auth/authService';
import { useSessao } from '@/features/auth/SessaoContext';

type Perfil = 'aluno' | 'professor';
type CampoFoco = 'email' | 'senha' | null;

const webNoOutline =
  Platform.OS === 'web'
    ? ({ outlineStyle: 'none', outlineWidth: 0 } as object)
    : undefined;

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [perfil, setPerfil] = useState<Perfil>('professor');
  const [focoCampo, setFocoCampo] = useState<CampoFoco>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const { iniciarSessao, encerrarSessao } = useSessao();

  async function entrar() {
    if (!email.trim() || !senha) {
      setErro('Informe o e-mail e a senha.');
      return;
    }

    setErro('');
    setCarregando(true);
    try {
      const usuario = await login({ email, senha });
      if (usuario.tipo !== perfil) {
        await encerrarSessao();
        setErro(`Esta conta não é de ${perfil}. Selecione o perfil correspondente.`);
        return;
      }
      iniciarSessao(usuario);
      router.replace(usuario.tipo === 'aluno' ? '/aluno/home' : '/professor/inicio');
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
        colors={['#3B0764', '#6B21A8', '#8B5CF6']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.background}
      >
        <View style={styles.content}>
          {/* Logo e Cabeçalho */}
          <View style={styles.header}>
            <View style={styles.logo}>
              <Text style={styles.logoText}>SGAA</Text>
            </View>
            <Text style={styles.title}>Bem-vindo!</Text>
            <Text style={styles.subtitle}>
              Sistema de Gerenciamento de Aulas e Agendamentos
            </Text>
          </View>

          {/* Seletor de Perfil */}
          <View style={styles.roleButtonsContainer}>
            {(['aluno', 'professor'] as const).map((opcao) => {
              const selecionado = perfil === opcao;
              return (
                <Pressable
                  key={opcao}
                  style={[
                    styles.roleButton,
                    selecionado ? styles.roleButtonSelected : styles.roleButtonUnselected,
                    webNoOutline,
                  ]}
                  onPress={() => {
                    setPerfil(opcao);
                    setErro('');
                  }}
                  accessibilityRole="button"
                  accessibilityState={{ selected: selecionado }}
                >
                  <Ionicons
                    name={opcao === 'aluno' ? 'school' : 'person'}
                    size={22}
                    color={selecionado ? '#6B21A8' : '#D8B4FE'}
                  />
                  <Text
                    style={[
                      styles.roleButtonTitle,
                      selecionado ? styles.roleButtonTitleSelected : styles.roleButtonTitleUnselected,
                    ]}
                  >
                    {opcao === 'aluno' ? 'Aluno' : 'Professor'}
                  </Text>
                  <Text
                    style={[
                      styles.roleButtonSubtitle,
                      selecionado ? styles.roleButtonSubtitleSelected : styles.roleButtonSubtitleUnselected,
                    ]}
                  >
                    Acessar minha área
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* Inputs de Credencial */}
          <View style={styles.formContainer}>
            <View
              style={[
                styles.inputContainer,
                focoCampo === 'email' && styles.inputContainerFocused,
              ]}
            >
              <Fontisto
                name="email"
                size={18}
                color={focoCampo === 'email' ? '#6B21A8' : '#9CA3AF'}
              />
              <TextInput
                value={email}
                onChangeText={setEmail}
                onFocus={() => setFocoCampo('email')}
                onBlur={() => setFocoCampo(null)}
                placeholder="E-mail"
                placeholderTextColor="#9CA3AF"
                keyboardType="email-address"
                autoCapitalize="none"
                underlineColorAndroid="transparent"
                style={[styles.input, webNoOutline]}
              />
            </View>

            <View
              style={[
                styles.inputContainer,
                focoCampo === 'senha' && styles.inputContainerFocused,
              ]}
            >
              <Ionicons
                name="lock-closed-outline"
                size={20}
                color={focoCampo === 'senha' ? '#6B21A8' : '#9CA3AF'}
              />
              <TextInput
                value={senha}
                onChangeText={setSenha}
                onFocus={() => setFocoCampo('senha')}
                onBlur={() => setFocoCampo(null)}
                placeholder="Senha"
                placeholderTextColor="#9CA3AF"
                secureTextEntry={!mostrarSenha}
                underlineColorAndroid="transparent"
                style={[styles.input, webNoOutline]}
              />
              <View style={styles.separator} />
              <Pressable
                onPress={() => setMostrarSenha(!mostrarSenha)}
                accessibilityRole="button"
                hitSlop={10}
                style={webNoOutline}
              >
                <Ionicons
                  name={mostrarSenha ? 'eye-outline' : 'eye-off-outline'}
                  size={20}
                  color="#9CA3AF"
                />
              </Pressable>
            </View>

            {erro ? <Text style={styles.erroTexto}>{erro}</Text> : null}

            <Pressable
              style={[styles.recoverContainer, webNoOutline]}
              onPress={() => router.push('/recuperar-senha')}
            >
              <Text style={styles.recover}>Esqueceu a senha?</Text>
            </Pressable>

            {/* Botão Principal */}
            <Pressable
              style={({ pressed }) => [
                styles.loginButtonContainer,
                webNoOutline,
                pressed && { opacity: 0.9, transform: [{ scale: 0.99 }] },
              ]}
              onPress={entrar}
              disabled={carregando}
            >
              <LinearGradient
                colors={['#A855F7', '#7E22CE']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.loginButton}
              >
                {carregando ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.loginText}>Entrar</Text>
                )}
              </LinearGradient>
            </Pressable>
          </View>
        </View>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  background: { flex: 1, justifyContent: 'center', paddingHorizontal: 24 },
  content: { width: '100%', maxWidth: 400, alignSelf: 'center' },
  header: { alignItems: 'center', marginBottom: 24 },
  logo: {
    width: 72,
    height: 72,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 6,
  },
  logoText: { color: '#6B21A8', fontSize: 20, fontWeight: '900', letterSpacing: 1 },
  title: { color: '#FFFFFF', fontSize: 24, fontWeight: '700', marginBottom: 4 },
  subtitle: {
    color: '#E9D5FF',
    fontSize: 13,
    fontWeight: '400',
    textAlign: 'center',
    paddingHorizontal: 12,
  },
  roleButtonsContainer: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  roleButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 8,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  roleButtonSelected: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  roleButtonUnselected: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  roleButtonTitle: { fontSize: 15, fontWeight: '700' },
  roleButtonTitleSelected: { color: '#6B21A8' },
  roleButtonTitleUnselected: { color: '#FFFFFF' },
  roleButtonSubtitle: { fontSize: 11 },
  roleButtonSubtitleSelected: { color: '#7E22CE' },
  roleButtonSubtitleUnselected: { color: '#E9D5FF' },
  formContainer: { width: '100%' },
  inputContainer: {
    height: 52,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: 'transparent',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginTop: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  inputContainerFocused: {
    borderColor: '#C084FC',
  },
  input: { flex: 1, marginLeft: 12, color: '#1F2937', fontSize: 15, fontWeight: '500' },
  separator: { width: 1, height: 20, backgroundColor: '#E5E7EB', marginHorizontal: 8 },
  erroTexto: { color: '#FCA5A5', fontSize: 13, textAlign: 'center', marginTop: 12, fontWeight: '500' },
  recoverContainer: { alignItems: 'flex-end', marginTop: 12, marginBottom: 20 },
  recover: { color: '#E9D5FF', fontSize: 13, fontWeight: '500' },
  loginButtonContainer: { width: '100%' },
  loginButton: {
    height: 52,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#7E22CE',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  loginText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});