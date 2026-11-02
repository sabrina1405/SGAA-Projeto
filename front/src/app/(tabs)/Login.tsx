import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Pressable } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Fontisto, Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export default function LoginScreen() {
  const [showPassword, setShowPassword] = useState(false);
  const [isStudentLogin, setIsStudentLogin] = useState(false);
    const router = useRouter();

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
        {isStudentLogin ? (
          <>

        <View style={styles.logo}>
          <Text style={styles.logoText}>SGAA</Text>
        </View>

        <Text style={styles.subtitleStudent}>
          Sistema de gerenciamento de Aulas e Agendamentos
        </Text>

            <Pressable 
            style={[styles.studentButton, {marginBottom: 28 }]}
            onPress={() => setIsStudentLogin(false)}
            >
              <Text style={styles.studentButtonText}>Acessar Área do Professor</Text>
            </Pressable>

            <View style={styles.inputContainer}>
              <Fontisto name="email" size={20} color="#666" />
              <TextInput
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
                placeholder="Senha"
                placeholderTextColor="#666"
                secureTextEntry={!showPassword}
                style={styles.input}
              />
              <View style={styles.separator} />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
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

              <Text style={styles.recover}>Recuperar senha</Text>
            </TouchableOpacity>

            <TouchableOpacity>
              <LinearGradient
                start={{ x: 0.65, y: 0 }}
                end={{ x: 0.35, y: 1 }}
                colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
                locations={[0.12, 1.0]}
                style={styles.loginButton}
              >
                <Text style={styles.loginText}>Entrar</Text>
              </LinearGradient>
            </TouchableOpacity>
          </>
        ) : (
          <>

        <View style={styles.logo}>
          <Text style={styles.logoText}>SGAA</Text>
        </View>

            <Text style={styles.subtitle}>
              Sistema de gerenciamento de Aulas e Agendamentos
            </Text>

            <TouchableOpacity
              style={styles.studentButton}
              onPress={() => setIsStudentLogin(true)}
            >
              <Text style={styles.studentButtonText}>Acessar Área do Aluno</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => router.push('/FirstAcess')}>
              <Text style={styles.firstAccess}>Primeiro Acesso - Professores</Text>
            </TouchableOpacity>

            <View style={styles.inputContainer}>
              <Fontisto name="email" size={20} color="#666" />
              <TextInput
                placeholder="E-mail"
                placeholderTextColor="#666"
                style={styles.input}
              />
            </View>

            <View style={styles.inputContainer}>
              <Ionicons name="lock-closed-outline" size={20} color="#666" />
              <TextInput
                placeholder="Senha"
                placeholderTextColor="#666"
                secureTextEntry={!showPassword}
                style={styles.input}
              />
              <View style={styles.separator} />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
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
              <Text style={styles.recover}>Recuperar senha</Text>
            </TouchableOpacity>

            <TouchableOpacity>
              <LinearGradient
                start={{ x: 0.65, y: 0 }}
                end={{ x: 0.35, y: 1 }}
                colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
                locations={[0.12, 1.0]}
                style={styles.loginButton}
              >
                <Text style={styles.loginText}>Entrar</Text>
              </LinearGradient>
            </TouchableOpacity>
          </>
        )}

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
    justifyContent: 'center'
  },

  logo: {
      width: 64,
      height: 64,
      alignSelf: 'center',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#F3EAF5',
      borderRadius: 18,
  },

  logoText: {
    color: '#84009A',
    fontSize: 17,
    fontWeight: '800',
    alignSelf: 'center',
  },

  title: {
    color: '#fff',
    fontSize: 25,
    fontWeight: 400,
    fontFamily: 'sans-serif'
  },

  subtitle: {
    color: '#fff',
    fontSize: 14,
    paddingVertical: 28,
    fontFamily: 'sans-serif',
    fontWeight: 300,
  },

  subtitleStudent: {
    color: '#fff',
    fontSize: 14,
    paddingVertical: 28,
    fontFamily: 'sans-serif',
    fontWeight: 300,
  },

  studentButton: {
    width: '82%',
    margin: 10,
    height: 40,
    backgroundColor: '#8A007A',
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'visible',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 3
    },
    shadowOpacity: 0.4,
    shadowRadius: 4,
    elevation: 6,
  },

  studentButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 18,
  },

  firstAccess: {
    color: '#ffff',
    marginTop: 14,
    marginBottom: 18,
    fontSize: 12,
    fontWeight: 400,
  },

  inputContainer: {
    width: '82%',
    height: 40,
    backgroundColor: '#F2F2F2',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginBottom: 20,

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

  recoverContainer:{
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