import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, StatusBar, } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Fontisto, Feather, Ionicons } from '@expo/vector-icons';

export default function PasswordRecover(){
  const [showPassword, setShowPassword] = useState(false);

return(
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
    <View style={styles.logo} />

    <Text style={styles.title}>SGAA</Text>

    <Text style={styles.subtitle}>
      Sistema de gerenciamento de Aulas e Agendamentos
    </Text>

    <TouchableOpacity style={styles.studentButton}>
      <Text style={styles.studentButtonText}>
        Recuperação de Senha
      </Text>
    </TouchableOpacity>


    <View style={styles.inputContainer}>
      <Fontisto name="email" size={20} color="#666" />
      <TextInput
        placeholder="E-mail"
        placeholderTextColor="#666"
        style={styles.input}
      />
    </View>

    <Text style={styles.label}>
      Insira o token recebido via e-mail
    </Text>

    <View style={styles.inputContainer}>
    <Ionicons name="key-outline" size={20} color="#666" />
      <TextInput
        placeholder="Token"
        placeholderTextColor="#666"
        style={styles.input}
      />
    </View>

    <TouchableOpacity style={styles.reenviarContainer}>
      <Text style={styles.reenviar}>Reenviar Token</Text>
    </TouchableOpacity>

    <Text style={styles.label}>
      Insira sua nova senha
    </Text>

    <View style={styles.inputContainer}>
     <Feather name="lock" size={20} color="#666" />

      <TextInput
        placeholder="Senha"
        placeholderTextColor="#666"
        secureTextEntry={!showPassword}
        style={styles.input}
      />

      <View style={styles.separator} />

      <TouchableOpacity
        onPress={() => setShowPassword(!showPassword)}
      >
        <Ionicons
          name={showPassword ? 'eye-outline' : 'eye-off-outline'}
          size={20}
          color="#666"
        />
      </TouchableOpacity>
    </View>

    <View style={styles.progressBar}>
      <View style={styles.progressFill} />
    </View>

    <View style={styles.rules}>
      <Text style={styles.rule}>• Mínimo 6 caracteres</Text>
      <Text style={styles.rule}>• Máximo 100 caracteres</Text>
      <Text style={styles.rule}>• 1 Caractere Maiúsculo</Text>
      <Text style={styles.rule}>• 1 Caractere Minúsculo</Text>
      <Text style={styles.rule}>• 2 Caracteres Especiais</Text>
    </View>

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
      
  </LinearGradient>
</View>


  )
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
  width: 80,
  height: 80,
  backgroundColor: '#D9D9D9',
  marginBottom: 10,
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
  marginTop: 6,
  fontFamily: 'sans-serif',
  fontWeight: 300,
  marginBottom: 28,
},

studentButton: {
  width: '82%',
  height: 40,
  backgroundColor: '#8A007A',
  borderRadius: 6,
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: 20,

  shadowColor: '#000',
  shadowOffset: {
    width: 0,
    height: 3,
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
  height: 20,
  borderRadius: 8,
  padding: 10,
  backgroundColor: '#1B8D33',
  alignItems: 'center',
  justifyContent: 'center',
},

loginText: {
  color: '#fff',
  fontSize: 9,
},
  
label: {
  width: '82%',
  color: '#fff',
  fontSize: 14,
  fontWeight: 100,
  fontFamily: 'sans-serif',
  marginBottom: 8,
},

reenviarContainer: {
  width: '80%',
  alignItems: 'flex-end',
  marginTop: -10,
  marginBottom: 10,
},

reenviar: {
  color: '#fff',
  fontSize: 12,
  fontFamily: 'sans-serif',
  fontWeight: 100,
},

progressBar: {
  width: '58%',
  height: 5,
  backgroundColor: '#C0C0C0',
  borderRadius: 10,
  overflow: 'hidden',
  marginTop: 18,
},

progressFill: {
  width: '45%',
  height: '100%',
  backgroundColor: '#FF0000',
  borderRadius: 10,
},

rules: {
  width: '58%',
  marginTop: 10,
  alignSelf: 'center',
},

rule: {
  color: '#FFFFFF',
  fontSize: 11,
  lineHeight: 15,
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

});