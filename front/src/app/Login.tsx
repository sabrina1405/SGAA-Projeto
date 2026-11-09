
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Pressable, ActivityIndicator, Alert, } from 'react-native';
import {styles} from '@/screens/Login/login.styles';
import { LinearGradient } from 'expo-linear-gradient';
import { Fontisto, Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { entrar } from '@/services/api';
import { useAuthSession } from '@/contexts/auth-context';

export default function LoginScreen() {
  const [showPassword, setShowPassword] = useState(false);
  const [isStudentLogin, setIsStudentLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const router = useRouter();
  const { signIn } = useAuthSession();

  const selectedProfile = isStudentLogin ? 'aluno' : 'professor';

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      Alert.alert('Dados incompletos', 'Informe seu e-mail e sua senha.');
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await entrar(email.trim(), password, selectedProfile);
      signIn(user);
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
