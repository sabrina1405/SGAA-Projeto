import React, { useState } from 'react';
import {
  ScrollView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { MaterialCommunityIcons, Feather  } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import DateTimePicker from '@react-native-community/datetimepicker';

export default function FirstAcess() {
  const [showPassword, setShowPassword] = useState(false);
  const [birthDate, setBirthDate] = useState<Date | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);

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
            <Text style={styles.title}>Cadastro de Professor</Text>
            <Text style={styles.subtitle}>
              Informe seus dados comerciais e pessoais para criar sua conta.
            </Text>
          </View>

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

          <View style={styles.section}>
            <View style={styles.sectionHeading}>
              <Feather name="user" size={30} color="#84009A" />
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


            <Text style={styles.label}>E-mail</Text>
            <TextInput
              placeholder="voce@exemplo.com"
              placeholderTextColor="#8B8790"
              style={styles.input}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
            />

            <Text style={styles.label}>Telefone</Text>
            <TextInput
              placeholder="(00) 00000-0000"
              placeholderTextColor="#8B8790"
              style={styles.input}
              keyboardType="phone-pad"
              returnKeyType="next"
            />

            <Text style={styles.label}>Senha</Text>
            <View style={styles.passwordField}>
              <TextInput
                placeholder="Crie uma senha"
                placeholderTextColor="#8B8790"
                secureTextEntry={!showPassword}
                style={styles.passwordInput}
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
          </View>

          <TouchableOpacity style={styles.submitButton} activeOpacity={0.85}>
            <Text style={styles.submitText}>Cadastrar</Text>
            <Feather name="arrow-right" size={18} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 18,
    paddingVertical: 28,
  },
  formCard: {
    width: '100%',
    maxWidth: 560,
    alignSelf: 'center',
    backgroundColor: '#FAF9FB',
    borderRadius: 24,
    padding: 22,
    shadowColor: '#26002E',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.18,
    shadowRadius: 18,
    elevation: 8,
  },
  header: {
    marginBottom: 24,
  },
  logo: {
    width: 64,
    height: 64,
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
  },
  title: {
    color: '#28232B',
    fontSize: 25,
    fontWeight: '700',
  },
  subtitle: {
    color: '#706A75',
    fontSize: 14,
    lineHeight: 20,
    marginTop: 6,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    borderBottomWidth: 1,
    borderBottomColor: '#E8E4EA',
    paddingBottom: 11,
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#342C38',
    fontSize: 16,
    fontWeight: '700',
  },
  label: {
    color: '#514A55',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 7,
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
    color: '#28232B',
    fontSize: 15,
    marginBottom: 16,
  },
  dateInput: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
    marginBottom: 16,
  },
  dateValue: {
    color: '#28232B',
    fontSize: 15,
  },
  datePlaceholder: {
    color: '#8B8790',
    fontSize: 15,
  },
  datePickerContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E3DEE6',
    marginBottom: 16,
    overflow: 'hidden',
  },
  datePickerDone: {
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#E8E4EA',
  },
  datePickerDoneText: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: '700',
  },
  photoField: {
    minHeight: 68,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#C9BCCC',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    marginBottom: 16,
  },
  photoIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#F3EAF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoCopy: {
    flex: 1,
    marginLeft: 12,
  },
  photoTitle: {
    color: '#342C38',
    fontSize: 13,
    fontWeight: '600',
  },
  photoHint: {
    color: '#8B8790',
    fontSize: 12,
    marginTop: 3,
  },
  passwordField: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
  },
  passwordInput: {
    flex: 1,
    color: '#28232B',
    fontSize: 15,
    paddingVertical: 12,
  },
  submitButton: {
    minHeight: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    backgroundColor: '#84009A',
    borderRadius: 12,
    marginTop: 2,
  },
  submitText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
});
