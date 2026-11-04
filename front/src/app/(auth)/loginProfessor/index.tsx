import { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';

import { palette } from '@/constants/palette';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      {/* Fundo com Gradiente Moderno */}
      <LinearGradient
        colors={['#4A148C', '#3F2B96', '#1A237E']}
        style={styles.gradientBackground}
      >
        <View style={styles.conteudo}>
          
          {/* Logo e Título */}
          <View style={styles.logoContainer}>
            <View style={styles.logoBox}>
              <Ionicons name="school" size={32} color={palette.header} />
            </View>
            <Text style={styles.appTitle}>SGAA</Text>
            <Text style={styles.appSubtitle}>Sistema de Gerenciamento de Aulas e Agendamentos</Text>
          </View>

          {/* Botão de Atalho: Acessar Área do Aluno */}
          <Pressable 
            style={({ pressed }) => [styles.btnAreaAluno, pressed && styles.pressionado]}
            onPress={() => {}}
          >
            <Ionicons name="person-outline" size={18} color="#FFFFFF" />
            <Text style={styles.btnAreaAlunoTexto}>Acessar Área do Aluno</Text>
          </Pressable>

          <View style={styles.divisorContainer}>
            <View style={styles.linhaDivisora} />
            <Text style={styles.divisorTexto}>ou entre como professor</Text>
            <View style={styles.linhaDivisora} />
          </View>

          {/* Formulário de Login (E-mail e Senha) */}
          <View style={styles.formContainer}>
            
            {/* Input de E-mail */}
            <View style={styles.inputWrapper}>
              <Ionicons name="mail-outline" size={20} color={palette.textMuted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="E-mail profissional"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            {/* Input de Senha */}
            <View style={styles.inputWrapper}>
              <Ionicons name="lock-closed-outline" size={20} color={palette.textMuted} style={styles.inputIcon} />
              <TextInput
                style={[styles.input, { flex: 1 }]}
                placeholder="Sua senha"
                placeholderTextColor="#9CA3AF"
                value={senha}
                onChangeText={setSenha}
                secureTextEntry={!mostrarSenha}
              />
              <Pressable onPress={() => setMostrarSenha(!mostrarSenha)} style={styles.eyeIcon}>
                <Ionicons 
                  name={mostrarSenha ? "eye-off-outline" : "eye-outline"} 
                  size={20} 
                  color={palette.textMuted} 
                />
              </Pressable>
            </View>

            {/* Link Recuperar Senha */}
            <Pressable onPress={() => {}} style={styles.recuperarSenhaContainer}>
              <Text style={styles.recuperarSenhaTexto}>Esqueceu sua senha?</Text>
            </Pressable>

            {/* Botão Entrar */}
            <Pressable 
              style={({ pressed }) => [styles.btnEntrar, pressed && styles.pressionado]}
              onPress={() => router.push('../professor')}
            >
              <Text style={styles.btnEntrarTexto}>Entrar no Sistema</Text>
              <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
            </Pressable>

          </View>

        </View>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradientBackground: { flex: 1 },
  conteudo: { 
    flex: 1, 
    padding: 24, 
    justifyContent: 'center', 
    alignItems: 'center',
    maxWidth: 400,
    width: '100%',
    alignSelf: 'center',
  },

  /* Logo e Título */
  logoContainer: { 
    alignItems: 'center', 
    marginBottom: 24,
  },
  logoBox: {
    width: 68,
    height: 68,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  appTitle: { 
    fontSize: 28, 
    fontWeight: '800', 
    color: '#FFFFFF',
    letterSpacing: 1.5,
  },
  appSubtitle: { 
    fontSize: 12, 
    color: 'rgba(255, 255, 255, 0.75)', 
    textAlign: 'center',
    marginTop: 4,
  },

  /* Botão Grande Área do Aluno */
  btnAreaAluno: {
    width: '100%',
    height: 52,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
    marginBottom: 20,
  },
  btnAreaAlunoTexto: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },

  /* Divisor */
  divisorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: 20,
    gap: 10,
  },
  linhaDivisora: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  divisorTexto: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 11,
    fontWeight: '500',
  },

  /* Formulário */
  formContainer: {
    width: '100%',
    gap: 14,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    paddingHorizontal: 16,
    height: 52,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    fontSize: 14,
    color: '#1F2937',
  },
  eyeIcon: {
    padding: 4,
  },
  recuperarSenhaContainer: {
    alignItems: 'flex-end',
    marginTop: 2,
    marginBottom: 6,
  },
  recuperarSenhaTexto: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 12,
    fontWeight: '500',
  },

  /* Botão Entrar */
  btnEntrar: {
    width: '100%',
    height: 52,
    backgroundColor: '#10B981', // Verde moderno e vibrante
    borderRadius: 14,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  btnEntrarTexto: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },

  pressionado: { opacity: 0.85, transform: [{ scale: 0.99 }] },
});