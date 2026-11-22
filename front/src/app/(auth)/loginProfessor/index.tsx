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

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [perfil, setPerfil] = useState<Perfil>('professor');
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
        colors={['#84009A', '#B2006C', '#D4481A', '#9B6A88', '#4B78E3']}
        start={{ x: 0.15, y: 0 }}
        end={{ x: 0.9, y: 1 }}
        style={styles.card}
      >
        <View style={styles.logo}>
          <Text style={styles.logoText}>SGAA</Text>
        </View>
        <Text style={styles.subtitle}>
          Sistema de gerenciamento de Aulas e Agendamentos
        </Text>

        <View style={styles.roleButtonsContainer}>
          {(['aluno', 'professor'] as const).map((opcao) => {
            const selecionado = perfil === opcao;
            return (
              <Pressable
                key={opcao}
                style={[styles.roleButton, selecionado ? styles.roleButtonSelected : styles.roleButtonUnselected]}
                onPress={() => {
                  setPerfil(opcao);
                  setErro('');
                }}
                accessibilityRole="button"
                accessibilityState={{ selected: selecionado }}
              >
                <Ionicons
                  name={opcao === 'aluno' ? 'school-outline' : 'person-outline'}
                  size={23}
                  color={selecionado ? '#FFFFFF' : '#84009A'}
                />
                <Text style={[styles.roleButtonTitle, selecionado && styles.roleButtonTitleSelected]}>
                  {opcao === 'aluno' ? 'Aluno' : 'Professor'}
                </Text>
                <Text style={[styles.roleButtonSubtitle, selecionado && styles.roleButtonSubtitleSelected]}>
                  Acessar minha área
                </Text>
              </Pressable>
            );
          })}
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
            style={styles.input}
          />
        </View>

        <View style={styles.inputContainer}>
          <Ionicons name="lock-closed-outline" size={20} color="#666" />
          <TextInput
            value={senha}
            onChangeText={setSenha}
            placeholder="Senha"
            placeholderTextColor="#666"
            secureTextEntry={!mostrarSenha}
            style={styles.input}
          />
          <View style={styles.separator} />
          <Pressable
            onPress={() => setMostrarSenha(!mostrarSenha)}
            accessibilityRole="button"
          >
            <Ionicons
              name={mostrarSenha ? 'eye-outline' : 'eye-off-outline'}
              size={20}
              color="#666"
            />
          </Pressable>
        </View>

        {erro ? <Text style={styles.erroTexto}>{erro}</Text> : null}

        <Pressable
          style={styles.recoverContainer}
          onPress={() => router.push('/recuperar-senha')}
        >
          <Text style={styles.recover}>Recuperar senha</Text>
        </Pressable>

        <Pressable
          style={styles.loginButtonContainer}
          onPress={entrar}
          disabled={carregando}
        >
          <LinearGradient
            colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
            style={styles.loginButton}
          >
            {carregando ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.loginText}>Entrar</Text>
            )}
          </LinearGradient>
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
  roleButtonsContainer: { width: '82%', maxWidth: 360, flexDirection: 'row', gap: 10 },
  roleButton: {
    flex: 1,
    minHeight: 76,
    paddingVertical: 8,
    paddingHorizontal: 6,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
  },
  roleButtonSelected: { backgroundColor: 'rgba(132, 0, 154, 0.35)', borderColor: 'rgba(255,255,255,0.65)' },
  roleButtonUnselected: { backgroundColor: '#F3EAF5', borderColor: '#FFFFFF' },
  roleButtonTitle: { color: '#84009A', fontSize: 14, fontWeight: '700' },
  roleButtonTitleSelected: { color: '#FFFFFF' },
  roleButtonSubtitle: { color: '#84009A', fontSize: 10, textAlign: 'center' },
  roleButtonSubtitleSelected: { color: '#FFFFFF' },
  inputContainer: {
    width: '82%',
    maxWidth: 360,
    height: 44,
    backgroundColor: '#F2F2F2',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginTop: 16,
  },
  input: { flex: 1, marginLeft: 14, color: '#222', fontWeight: '600' },
  separator: { width: 1, height: 20, backgroundColor: '#D6D6D6', marginRight: 12 },
  erroTexto: { width: '82%', maxWidth: 360, color: '#FFE2E2', fontSize: 12, textAlign: 'center', marginTop: 12 },
  recoverContainer: { width: '82%', maxWidth: 360, alignItems: 'flex-end', marginTop: 10, marginBottom: 16 },
  recover: { color: '#E8DCE8', fontSize: 12 },
  loginButtonContainer: { width: 100 },
  loginButton: { height: 40, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  loginText: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },
});
