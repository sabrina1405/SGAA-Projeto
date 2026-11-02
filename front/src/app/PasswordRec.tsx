import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Fontisto, Feather, Ionicons } from '@expo/vector-icons';
import {styles} from '@/screens/Home/login.styles';

export default function PasswordRecover(){
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState('');
  const specialCharacterCount = (password.match(/[^A-Za-z0-9\s]/g) ?? []).length;
  const passwordRules = [
    { label: 'Mínimo 6 caracteres', valid: password.length >= 6 },
    { label: 'Máximo 100 caracteres', valid: password.length > 0 && password.length <= 100 },
    { label: '1 caractere maiúsculo', valid: /[A-Z]/.test(password) },
    { label: '1 caractere minúsculo', valid: /[a-z]/.test(password) },
    { label: '2 caracteres especiais', valid: specialCharacterCount >= 2 },
  ];
  const validRulesCount = passwordRules.filter((rule) => rule.valid).length;
  const progress = (validRulesCount / passwordRules.length) * 100;
  const progressColor = password.length === 0
    ? '#C0C0C0'
    : validRulesCount === passwordRules.length
      ? '#35C46A'
      : validRulesCount >= 3
        ? '#F5B82E'
        : '#FF4D4F';
  const strengthLabel = password.length === 0
    ? 'Sem senha'
    : validRulesCount === passwordRules.length
      ? 'Forte'
      : validRulesCount >= 3
        ? 'Média'
        : 'Fraca';

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
        value={password}
        onChangeText={setPassword}
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

    <View style={styles.passwordStrength}>
      <Text style={styles.strengthLabel}>Força da senha: {strengthLabel}</Text>
      <View
        style={styles.progressBar}
        accessibilityRole="progressbar"
        accessibilityLabel={`Força da senha: ${strengthLabel}`}
        accessibilityValue={{ min: 0, max: 100, now: progress }}
      >
        <View
          style={[
            styles.progressFill,
            { width: `${progress}%`, backgroundColor: progressColor },
          ]}
        />
      </View>
    </View>

    <View style={styles.rules}>
      {passwordRules.map((rule) => (
        <View key={rule.label} style={styles.ruleRow}>
          <Ionicons
            name={
              rule.valid
                ? 'checkmark-circle'
                : password.length > 0
                  ? 'close-circle'
                  : 'ellipse-outline'
            }
            size={14}
            color={rule.valid ? '#35C46A' : password.length > 0 ? '#FF7777' : '#FFFFFF'}
          />
          <Text
            style={[
              styles.rule,
              rule.valid && styles.ruleValid,
              !rule.valid && password.length > 0 && styles.ruleInvalid,
            ]}
          >
            {rule.label}
          </Text>
        </View>
      ))}
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