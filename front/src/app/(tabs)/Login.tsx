
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  Alert,
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';
import { Fontisto, Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { entrar } from '@/services/api';

export default function LoginScreen() {
  const [showPassword, setShowPassword] = useState(false);
  const [isStudentLogin, setIsStudentLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const router = useRouter();

  const selectedProfile = isStudentLogin ? 'aluno' : 'professor';

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      Alert.alert('Dados incompletos', 'Informe seu e-mail e sua senha.');
      return;
    }

    setIsSubmitting(true);
    try {
      await entrar(email.trim(), password, selectedProfile);
      router.replace('/Home');
    } catch (error) {
      console.error('Erro ao entrar:', error);
      Alert.alert(
        'Não foi possível entrar',
        error instanceof Error
          ? error.message
          : 'Verifique sua conexão e tente novamente.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFirstAccess = () => {
    router.push({
      pathname: '/FirstAccess',
      params: { perfil: selectedProfile },
    });
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={[
          '#84009A',
          '#B2006C',
          '#D4481A',
          '#9B6A88',
          '#4B78E3',
        ]}
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

          <Pressable
            style={[
              styles.roleButton,
              isStudentLogin
                ? styles.roleButtonSelected
                : styles.roleButtonUnselected,
            ]}
            onPress={() => setIsStudentLogin(true)}
            accessibilityRole="button"
            accessibilityState={{ selected: isStudentLogin }}
            accessibilityLabel="Acessar como aluno"
          >
            <Ionicons
              name="school-outline"
              size={23}
              color={isStudentLogin ? '#ffff' : '#84009A'}
            />

            <Text
              style={[
                styles.roleButtonTitle,
                isStudentLogin && styles.roleButtonTitleSelected,
              ]}
            >
              Aluno
            </Text>

            <Text
              style={[
                styles.roleButtonSubtitle,
                isStudentLogin && styles.roleButtonSubtitleSelected,
              ]}
            >
              Acessar minha área
            </Text>
          </Pressable>

          <Pressable
            style={[
              styles.roleButton,
              !isStudentLogin
                ? styles.roleButtonSelected
                : styles.roleButtonUnselected,
            ]}
            onPress={() => setIsStudentLogin(false)}
            accessibilityRole="button"
            accessibilityState={{ selected: !isStudentLogin }}
            accessibilityLabel="Acessar como professor"
          >
            <Ionicons
              name="person-outline"
              size={23}
              color={!isStudentLogin ? '#FFF' : '#84009A'}
            />

            <Text
              style={[
                styles.roleButtonTitle,
                !isStudentLogin && styles.roleButtonTitleSelected,
              ]}
            >
              Professor
            </Text>

            <Text
              style={[
                styles.roleButtonSubtitle,
                !isStudentLogin && styles.roleButtonSubtitleSelected,
              ]}
            >
              Acessar minha área
            </Text>
          </Pressable>

        </View>

        <TouchableOpacity
          style={styles.firstAccessContainer}
          onPress={handleFirstAccess}
          accessibilityRole="button"
          accessibilityLabel={`Primeiro acesso como ${selectedProfile}. Cadastre-se.`}
        >
          <Text style={styles.firstAccessText}>
            Primeiro acesso como {selectedProfile}?{' '}
          </Text>

          <Text style={styles.firstAccessLink}>
            Cadastre-se
          </Text>
        </TouchableOpacity>

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
          <Ionicons
            name="lock-closed-outline"
            size={20}
            color="#666"
          />

          <TextInput
            value={password}
            onChangeText={setPassword}
            placeholder="Senha"
            placeholderTextColor="#666"
            secureTextEntry={!showPassword}
            style={styles.input}
          />

          <View style={styles.separator} />

          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            accessibilityRole="button"
            accessibilityLabel={
              showPassword ? 'Ocultar senha' : 'Mostrar senha'
            }
          >
            <Ionicons
              name={showPassword ? 'eye-outline' : 'eye-off-outline'}
              size={20}
              color="#666"
            />
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.recoverContainer}
          onPress={() => router.push('/PasswordRec')}
        >
          <Text style={styles.recover}>
            Recuperar senha
          </Text>
        </TouchableOpacity>

        <TouchableOpacity disabled={isSubmitting} onPress={handleLogin}>
          <LinearGradient
            start={{ x: 0.65, y: 0 }}
            end={{ x: 0.35, y: 1 }}
            colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
            locations={[0.12, 1.0]}
            style={styles.loginButton}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.loginText}>Entrar</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>

      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },

  card: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  logo: {
    width: 64,
    height: 64,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3EAF5',
    borderRadius: 18,
    marginBottom: 18,
  },

  logoText: {
    color: '#84009A',
    fontSize: 17,
    fontWeight: '800',
    alignSelf: 'center',
  },

  subtitle: {
    color: '#fff',
    fontSize: 14,
    paddingVertical: 20,
    fontFamily: 'sans-serif',
    fontWeight: '300',
  },


  roleButtonsContainer: {
    width: '82%',
    flexDirection: 'row',
    gap: 10,
  },

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

  roleButtonSelected: {
    backgroundColor: 'rgba(132, 0, 154, 0.35)',
    borderColor: 'rgba(255, 255, 255, 0.65)',
  },
  
  roleButtonUnselected: {
    backgroundColor: '#F3EAF5',
    borderColor: '#FFFFFF',
  },

  roleButtonTitle: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: '700',
  },

  roleButtonTitleSelected: {
    color: '#FFF',
  },

  roleButtonSubtitle: {
    color: '#84009A',
    fontSize: 10,
    textAlign: 'center',
  },

  roleButtonSubtitleSelected: {
    color: '#ffff',
  },


  firstAccessContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    marginBottom: 16,
    paddingVertical: 4,
  },

  firstAccessText: {
    color: '#FFFFFF',
    fontSize: 12,
  },

  firstAccessLink: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },

  inputContainer: {
    width: '82%',
    height: 40,
    backgroundColor: '#F2F2F2',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginBottom: 16,

    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 3,
    },
    shadowOpacity: 0.35,
    shadowRadius: 4,
    elevation: 5,
  },

  input: {
    flex: 1,
    marginLeft: 14,
    color: '#222',
    fontWeight: '600',
  },

  separator: {
    width: 1,
    height: 20,
    backgroundColor: '#D6D6D6',
    marginRight: 12,
  },

  recoverContainer: {
    display: 'flex',
    width: '80%',
    alignItems: 'flex-end',
    justifyContent: 'flex-end',
  },

  recover: {
    color: '#E8DCE8',
    marginBottom: 16,
    alignSelf: 'flex-end',
    fontSize: 12,
  },

  loginButton: {
    width: 100,
    height: 40,
    borderRadius: 8,
    padding: 10,
    backgroundColor: '#1B8D33',
    alignItems: 'center',
    justifyContent: 'center',
  },

  loginText: {
    color: '#fff',
    fontSize: 12,
  },
});
