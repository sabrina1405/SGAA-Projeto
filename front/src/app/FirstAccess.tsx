import React, { useState } from 'react';
import { ActivityIndicator, Alert, ScrollView, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View, } from 'react-native';
import { MaterialCommunityIcons, Feather, Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';
import { router, useLocalSearchParams } from 'expo-router';
import { ApiRequestError, requestApi } from '@/services/api';
import { getPasswordRules } from '@/utils/passwordRules';
import {styles} from '@/screens/Login/FirstAcess.styles';


function isUnderage(date: Date | null): boolean {
  if (!date) return false;
  const today = new Date();
  let age = today.getFullYear() - date.getFullYear();
  if (
    today.getMonth() < date.getMonth() ||
    (today.getMonth() === date.getMonth() && today.getDate() < date.getDate())
  ) {
    age -= 1;
  }
  return age >= 0 && age < 18;
}

function formatDateForApi(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function FirstAcess() {
  const [showPassword, setShowPassword] = useState(false);
  const [birthDate, setBirthDate] = useState<Date | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [firstAccessToken, setFirstAccessToken] = useState<string | null>(null);
  const [cpf, setCpf] = useState('');
  const [phone, setPhone] = useState('');
  const [guardianName, setGuardianName] = useState('');
  const [password, setPassword] = useState('');
  const [resendAllowed, setResendAllowed] = useState(false);
  const [codeError, setCodeError] = useState(false);
  const [codeMessage, setCodeMessage] = useState('');
  const [requestingCode, setRequestingCode] = useState(false);
  const [validatingCode, setValidatingCode] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { perfil } = useLocalSearchParams<{ perfil?: string }>();
  const isStudent = perfil === 'aluno';
  const studentIsUnderage = isUnderage(birthDate);
  const passwordRules = getPasswordRules(password);
  const validPasswordRules = passwordRules.filter((rule) => rule.valid).length;
  const passwordProgress = (validPasswordRules / passwordRules.length) * 100;
  const passwordStrength = password.length === 0
    ? 'Sem senha'
    : validPasswordRules === passwordRules.length
      ? 'Forte'
      : validPasswordRules >= 3
        ? 'Média'
        : 'Fraca';
  const passwordProgressColor = password.length === 0
    ? '#C0C0C0'
    : validPasswordRules === passwordRules.length
      ? '#35C46A'
      : validPasswordRules >= 3
        ? '#F5B82E'
        : '#FF4D4F';

  const requestVerificationCode = async () => {
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setCodeError(true);
      setCodeMessage('Informe seu e-mail para receber o token.');
      return;
    }

    setRequestingCode(true);
    setCodeError(false);
    try {
      await requestApi<null>('/auth/primeiro-acesso/codigo', {
        method: 'POST',
        body: {
          email: normalizedEmail,
          codigo: verificationCode.trim(),
        },
        authenticated: false,
      });
      setFirstAccessToken(null);
      setVerificationCode('');
      setResendAllowed(false);
      setCodeMessage(
        'Se este e-mail estiver cadastrado e aguardando o primeiro acesso, enviaremos um novo token. Verifique sua caixa de entrada e o spam.',
      );
    } catch (error) {
      console.error('Erro ao solicitar token do primeiro acesso:', error);
      if (error instanceof ApiRequestError && error.status === 409) {
        setResendAllowed(false);
        setCodeError(false);
        setCodeMessage('Este token ainda está válido. Use-o para continuar o cadastro.');
        return;
      }
      setCodeError(true);
      setCodeMessage(
        error instanceof ApiRequestError
          ? error.message
          : 'Não foi possível solicitar o token. Verifique sua conexão e tente novamente.',
      );
    } finally {
      setRequestingCode(false);
    }
  };

  const validateVerificationCode = async () => {
    setValidatingCode(true);
    setCodeError(false);
    try {
      const details = await requestApi<{
        token_primeiro_acesso: string;
        usuario: { tipo: string };
      }>(
        '/auth/primeiro-acesso/validar-codigo',
        {
          method: 'POST',
          body: { email: email.trim(), codigo: verificationCode.trim() },
          authenticated: false,
        },
      );
      if (details.usuario.tipo !== 'aluno') {
        throw new ApiRequestError('Este e-mail não pertence a uma conta de aluno.', 403);
      }
      const token = details.token_primeiro_acesso;
      if (!token) {
        throw new Error('A API não retornou o token de primeiro acesso.');
      }
      setFirstAccessToken(token);
      setCodeMessage('E-mail confirmado. Preencha seus dados e crie uma senha.');
    } catch (error) {
      console.error('Erro ao validar token do primeiro acesso:', error);
      setFirstAccessToken(null);
      setCodeError(true);
      if (error instanceof ApiRequestError && error.status === 410) {
        setResendAllowed(true);
        setCodeMessage('Este token expirou. Você pode solicitar um novo token por e-mail.');
      } else {
        setResendAllowed(false);
        setCodeMessage(
          error instanceof ApiRequestError && error.status === 400
            ? 'Token inválido. Confira o código recebido e tente novamente.'
            : error instanceof Error
              ? error.message
              : 'Não foi possível validar o token. Tente novamente.',
        );
      }
    } finally {
      setValidatingCode(false);
    }
  };

  const completeStudentRegistration = async () => {
    if (!birthDate || !cpf.trim() || !phone.trim() || (studentIsUnderage && !guardianName.trim())) {
      Alert.alert(
        'Dados incompletos',
        'Preencha a data de nascimento, CPF e telefone. Para menores de idade, informe também o nome do responsável.',
      );
      return;
    }

    if (!firstAccessToken || validPasswordRules !== passwordRules.length) return;

    setSubmitting(true);
    try {
      await requestApi(
        '/auth/primeiro-acesso/aluno',
        {
          method: 'POST',
          body: {
            data_nascimento: formatDateForApi(birthDate),
            cpf: cpf.trim(),
            telefone: phone.trim(),
            ...(studentIsUnderage ? { responsavel_nome: guardianName.trim() } : {}),
            nova_senha: password,
          },
          authenticated: false,
          accessToken: firstAccessToken,
        },
      );
      Alert.alert(
        'Cadastro concluído',
        'Seu primeiro acesso foi concluído. Entre usando seu e-mail e a nova senha.',
        [{ text: 'Ir para o login', onPress: () => router.back() }],
      );
    } catch (error) {
      console.error('Erro ao concluir primeiro acesso do aluno:', error);
      if (error instanceof ApiRequestError && error.status === 401) {
        setFirstAccessToken(null);
        setCodeError(true);
        setCodeMessage('O token expirou. Solicite um novo token para continuar.');
      } else {
        Alert.alert(
          'Não foi possível concluir o cadastro',
          error instanceof ApiRequestError
            ? error.message
            : 'Verifique sua conexão e tente novamente.',
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <LinearGradient
      colors={['#84009A', '#B2006C', '#D4481A', '#9B6A88', '#4B78E3']}
      start={{ x: 0.15, y: 0 }}
      end={{ x: 0.9, y: 1 }}
      style={styles.screen}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.formCard}>
          <View style={styles.header}>
            <View style={styles.logo}>
              <Text style={styles.logoText}>SGAA</Text>
            </View>
            <Text style={styles.title}>
              Cadastro de {isStudent ? 'Aluno' : 'Professor'}
            </Text>
            <Text style={styles.subtitle}>
              {isStudent
                ? 'Informe seus dados pessoais para criar sua conta.'
                : 'Informe seus dados comerciais e pessoais para criar sua conta.'}
            </Text>
          </View>

          {!isStudent && (
            <View style={styles.section}>
              <View style={styles.sectionHeading}>
                <MaterialCommunityIcons name="office-building-plus-outline" size={30} color="#84009A" />
                <Text style={styles.sectionTitle}>Dados Comerciais</Text>
              </View>

              <Text style={styles.label}>Nome comercial</Text>
              <TextInput
                placeholder="Ex.: Escola de Música"
                placeholderTextColor="#8B8790"
                style={styles.input}
                returnKeyType="next"
              />

              <Text style={styles.label}>Foto de perfil</Text>
              <TouchableOpacity style={styles.photoField} activeOpacity={0.75}>
                <View style={styles.photoIcon}>
                  <Feather name="camera" size={20} color="#84009A" />
                </View>
                <View style={styles.photoCopy}>
                  <Text style={styles.photoTitle}>Adicionar foto de perfil</Text>
                  <Text style={styles.photoHint}>JPG ou PNG</Text>
                </View>
                <Feather name="upload" size={18} color="#84009A" />
              </TouchableOpacity>

              <Text style={styles.label}>CNPJ</Text>
              <TextInput
                placeholder="00.000.000/0000-00"
                placeholderTextColor="#8B8790"
                keyboardType="numeric"
                style={styles.input}
                returnKeyType="next"
              />
            </View>
          )}

          <View style={styles.section}>
            <View style={styles.sectionHeading}>
              {isStudent ? (
                <MaterialCommunityIcons name="school-outline" size={30} color="#84009A" />
              ) : (
                <Feather name="user" size={30} color="#84009A" />
              )}
              <Text style={styles.sectionTitle}>Dados Pessoais</Text>
            </View>

            <Text style={styles.label}>Nome completo</Text>
            <TextInput
              placeholder="Seu nome completo"
              placeholderTextColor="#8B8790"
              style={styles.input}
              autoCapitalize="words"
              returnKeyType="next"
            />

            <Text style={styles.label}>Data de nascimento</Text>
            <TouchableOpacity
              style={styles.dateInput}
              onPress={() => setShowDatePicker(true)}
              accessibilityRole="button"
              accessibilityLabel="Escolher data de nascimento"
              activeOpacity={0.75}
            >
              <Text style={birthDate ? styles.dateValue : styles.datePlaceholder}>
                {birthDate ? birthDate.toLocaleDateString('pt-BR') : 'DD/MM/AAAA'}
              </Text>
              <Feather name="calendar" size={19} color="#84009A" />
            </TouchableOpacity>

            {showDatePicker && (
              <View style={styles.datePickerContainer}>
                <DateTimePicker
                  value={birthDate ?? new Date(2000, 0, 1)}
                  mode="date"
                  display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                  maximumDate={new Date()}
                  onChange={(event, selectedDate) => {
                    if (selectedDate) {
                      setBirthDate(selectedDate);
                    }
                    if (Platform.OS !== 'ios' || event.type === 'dismissed') {
                      setShowDatePicker(false);
                    }
                  }}
                />
                {Platform.OS === 'ios' && (
                  <TouchableOpacity
                    style={styles.datePickerDone}
                    onPress={() => setShowDatePicker(false)}
                  >
                    <Text style={styles.datePickerDoneText}>Concluir</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}

            {isStudent && (
              <>
                <Text style={styles.label}>
                  {studentIsUnderage ? 'CPF do responsável' : 'CPF'}
                </Text>
                <TextInput
                  value={cpf}
                  onChangeText={setCpf}
                  placeholder="000.000.000-00"
                  placeholderTextColor="#8B8790"
                  keyboardType="numeric"
                  style={styles.input}
                  returnKeyType="next"
                />
                {studentIsUnderage && (
                  <>
                    <Text style={styles.label}>Nome do responsável</Text>
                    <TextInput
                      value={guardianName}
                      onChangeText={setGuardianName}
                      placeholder="Nome completo do responsável"
                      placeholderTextColor="#8B8790"
                      autoCapitalize="words"
                      style={styles.input}
                      returnKeyType="next"
                    />
                  </>
                )}
              </>
            )}

            <Text style={styles.label}>E-mail</Text>
            <TextInput
              value={email}
              editable={!requestingCode && !validatingCode && !firstAccessToken}
              onChangeText={(value) => {
                setEmail(value);
                setVerificationCode('');
                setFirstAccessToken(null);
                setResendAllowed(false);
                setCodeError(false);
                setCodeMessage('');
              }}
              placeholder="voce@exemplo.com"
              placeholderTextColor="#8B8790"
              style={styles.input}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
            />

            {isStudent && (
              <>
                {!!codeMessage && (
                  <Text
                    style={[
                      styles.codeMessage,
                      codeError && styles.codeMessageError,
                    ]}
                    accessibilityLiveRegion="polite"
                  >
                    {codeMessage}
                  </Text>
                )}

                {!firstAccessToken && (
                  <>
                    <Text style={styles.label}>Token recebido por e-mail</Text>
                    <Text style={styles.tokenHint}>
                      Digite o token enviado quando sua conta foi cadastrada.
                    </Text>
                    <TextInput
                      value={verificationCode}
                      editable={!validatingCode && !requestingCode}
                      onChangeText={(value) => {
                        setVerificationCode(value.replace(/\D/g, '').slice(0, 6));
                        setResendAllowed(false);
                        setCodeError(false);
                        setCodeMessage('');
                      }}
                      placeholder="Digite o código de 6 dígitos"
                      placeholderTextColor="#8B8790"
                      keyboardType="number-pad"
                      style={styles.input}
                      maxLength={6}
                      returnKeyType="done"
                    />
                    <TouchableOpacity
                      style={styles.secondaryButton}
                      onPress={validateVerificationCode}
                      disabled={validatingCode || verificationCode.length !== 6}
                      activeOpacity={0.75}
                      accessibilityRole="button"
                    >
                      {validatingCode ? (
                        <ActivityIndicator size="small" color="#84009A" />
                      ) : (
                        <Feather name="check-circle" size={17} color="#84009A" />
                      )}
                      <Text style={styles.secondaryButtonText}>
                        {validatingCode ? 'Validando...' : 'Validar token'}
                      </Text>
                    </TouchableOpacity>
                    {resendAllowed && (
                      <TouchableOpacity
                        style={styles.secondaryButton}
                        onPress={requestVerificationCode}
                        disabled={requestingCode}
                        activeOpacity={0.75}
                        accessibilityRole="button"
                      >
                        {requestingCode ? (
                          <ActivityIndicator size="small" color="#84009A" />
                        ) : (
                          <Feather name="refresh-cw" size={17} color="#84009A" />
                        )}
                        <Text style={styles.secondaryButtonText}>
                          {requestingCode ? 'Enviando token...' : 'Reenviar token expirado'}
                        </Text>
                      </TouchableOpacity>
                    )}
                  </>
                )}
              </>
            )}

            <Text style={styles.label}>
              {isStudent && studentIsUnderage
                ? 'Telefone do responsável'
                : 'Telefone'}
            </Text>
            <TextInput
              value={phone}
              onChangeText={setPhone}
              placeholder="(00) 00000-0000"
              placeholderTextColor="#8B8790"
              style={styles.input}
              keyboardType="phone-pad"
              returnKeyType="next"
            />

            {(!isStudent || firstAccessToken) && (
              <>
                <Text style={styles.label}>Senha</Text>
                <View style={styles.passwordField}>
                  <TextInput
                    value={password}
                    onChangeText={setPassword}
                    placeholder="Crie uma senha"
                    placeholderTextColor="#8B8790"
                    secureTextEntry={!showPassword}
                    style={styles.passwordInput}
                    maxLength={100}
                    returnKeyType="done"
                  />
                  <TouchableOpacity
                    accessibilityRole="button"
                    accessibilityLabel={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                    onPress={() => setShowPassword((visible) => !visible)}
                    hitSlop={8}
                  >
                    <Feather
                      name={showPassword ? 'eye' : 'eye-off'}
                      size={19}
                      color="#706A75"
                    />
                  </TouchableOpacity>
                </View>

                {isStudent && (
                  <View style={styles.passwordStrength}>
                    <Text style={styles.strengthLabel}>
                      Força da senha: {passwordStrength}
                    </Text>
                    <View
                      style={styles.progressBar}
                      accessibilityRole="progressbar"
                      accessibilityLabel={`Força da senha: ${passwordStrength}`}
                      accessibilityValue={{
                        min: 0,
                        max: 100,
                        now: passwordProgress,
                      }}
                    >
                      <View
                        style={[
                          styles.progressFill,
                          {
                            width: `${passwordProgress}%`,
                            backgroundColor: passwordProgressColor,
                          },
                        ]}
                      />
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
                            color={
                              rule.valid
                                ? '#35C46A'
                                : password.length > 0
                                  ? '#FF7777'
                                  : '#8B8790'
                            }
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
                  </View>
                )}
              </>
            )}
          </View>

          <TouchableOpacity
            style={[
              styles.submitButton,
              isStudent &&
                (!firstAccessToken || validPasswordRules !== passwordRules.length) &&
                styles.submitButtonDisabled,
            ]}
            onPress={isStudent ? completeStudentRegistration : undefined}
            disabled={
              isStudent &&
              (!firstAccessToken || validPasswordRules !== passwordRules.length || submitting)
            }
            activeOpacity={0.85}
          >
            {submitting ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <>
                <Text style={styles.submitText}>Cadastrar</Text>
                <Feather name="arrow-right" size={18} color="#FFFFFF" />
              </>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </LinearGradient>
  );
}
