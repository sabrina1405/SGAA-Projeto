import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StatusBar, } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Fontisto, Feather, Ionicons } from '@expo/vector-icons';
import {styles} from '@/screens/Home/login.styles';

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
};