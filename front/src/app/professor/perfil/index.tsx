import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, Pressable, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { logout } from '@/features/auth/authService';

import { palette } from '@/constants/palette';

import { useSessao } from '@/features/auth/SessaoContext';

export default function PerfilScreen() {
  const router = useRouter();
  const [idiomaApp, setIdiomaApp] = useState('Português');
  const [ingles, setIngles] = useState(false);
  const [espanhol, setEspanhol] = useState(true);
  const { encerrarSessao } = useSessao();

const handleLogout = async () => {
  await encerrarSessao();
  router.replace('/loginProfessor');
};


  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.conteudo} showsVerticalScrollIndicator={false}>
      
      {/* 1. Header Hero do Perfil (Avatar e Nome) */}
      <View style={styles.heroContainer}>
        <View style={styles.avatarCircle}>
          <Ionicons name="person" size={48} color="#FFFFFF" />
        </View>
        <Text style={styles.userName}>Fernanda Alves</Text>
      </View>

      {/* 2. Card de Informações Cadastrais */}
      <View style={styles.cardSecao}>
        <Text style={styles.labelCampo}>Nome de Usuário</Text>
        <TextInput style={styles.inputCampo} defaultValue="El Camino Idiomas" />

        <Text style={styles.labelCampo}>CNPJ</Text>
        <TextInput style={styles.inputCampo} defaultValue="00.000.000/0001-00" keyboardType="numeric" />

        <Text style={styles.labelCampo}>E-mail</Text>
        <TextInput style={styles.inputCampo} defaultValue="ElCaminoIdiomas@email.com" keyboardType="email-address" />

        <Text style={styles.labelCampo}>Telefone</Text>
        <TextInput style={styles.inputCampo} defaultValue="(11) 99999-9999" keyboardType="phone-pad" />
      </View>

      {/* 3. Preferências e Idiomas Ensinados */}
      <View style={styles.cardSecao}>
        <Text style={styles.labelCampo}>Idioma de Preferência do App</Text>
        <Pressable style={styles.dropdownContainer} onPress={() => {}}>
          <Text style={styles.dropdownTexto}>{idiomaApp}</Text>
          <Ionicons name="chevron-down" size={18} color={palette.textMuted} />
        </Pressable>

        <Text style={styles.subTituloSecao}>Idiomas Ensinados</Text>
        
        <View style={styles.checkboxContainer}>
          <Pressable style={styles.checkboxRow} onPress={() => setIngles(!ingles)}>
            <View style={[styles.checkboxBox, ingles && styles.checkboxBoxChecked]}>
              {ingles && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
            </View>
            <Text style={styles.checkboxLabel}>Inglês</Text>
          </Pressable>

          <Pressable style={styles.checkboxRow} onPress={() => setEspanhol(!espanhol)}>
            <View style={[styles.checkboxBox, espanhol && styles.checkboxBoxChecked]}>
              {espanhol && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
            </View>
            <Text style={styles.checkboxLabel}>Espanhol</Text>
          </Pressable>

          <Pressable style={styles.checkboxRow} onPress={() => {}}>
            <View style={styles.checkboxAddBox}>
              <Ionicons name="add" size={14} color={palette.header} />
            </View>
            <Text style={[styles.checkboxLabel, { color: palette.header, fontWeight: '700' }]}>Adicionar Novo</Text>
          </Pressable>
        </View>
      </View>

      {/* 4. Botões de Ação (Cancelar / Salvar) */}
      <View style={styles.acoesRow}>
        <Pressable style={({ pressed }) => [styles.btnAcao, styles.btnCancelar, pressed && styles.pressionado]} onPress={() => {}}>
          <Text style={styles.btnAcaoTexto}>Cancelar</Text>
        </Pressable>

        <Pressable style={({ pressed }) => [styles.btnAcao, styles.btnSalvar, pressed && styles.pressionado]} onPress={() => {}}>
          <Text style={styles.btnAcaoTexto}>Salvar</Text>
        </Pressable>
      </View>

      {/* 5. Botão de Terminar Sessão (Logout) */}
      <Pressable 
        style={({ pressed }) => [styles.btnLogout, pressed && styles.pressionado]} 
        onPress={handleLogout}
      >
        <Ionicons name="log-out-outline" size={18} color="#D32F2F" />
        <Text style={styles.btnLogoutTexto}>Terminar Sessão</Text>
      </Pressable>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  conteudo: { padding: 16, paddingBottom: 40, gap: 16 },

  /* Hero Avatar */
  heroContainer: {
    alignItems: 'center',
    paddingVertical: 10,
    gap: 10,
  },
  avatarCircle: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: '#BA68C8',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  userName: { fontSize: 16, fontWeight: '700', color: palette.title },

  /* Cards de Seção */
  cardSecao: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 3,
    elevation: 2,
  },
  labelCampo: { fontSize: 11, fontWeight: '600', color: palette.textMuted },
  inputCampo: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 13,
    color: palette.title,
    fontWeight: '600',
    marginBottom: 4,
  },

  /* Dropdown e Idiomas */
  dropdownContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 12,
    marginBottom: 8,
  },
  dropdownTexto: { fontSize: 13, fontWeight: '600', color: palette.title },
  subTituloSecao: { fontSize: 13, fontWeight: '700', color: palette.title, marginTop: 4, marginBottom: 4 },

  checkboxContainer: { gap: 10 },
  checkboxRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  checkboxBox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: palette.textMuted,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxBoxChecked: {
    backgroundColor: palette.header,
    borderColor: palette.header,
  },
  checkboxAddBox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: palette.header,
    justifyContent: 'center',
    alignItems: 'center',
    borderStyle: 'dashed',
  },
  checkboxLabel: { fontSize: 13, fontWeight: '600', color: palette.title },

  /* Botões Inferiores */
  acoesRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  btnAcao: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  btnCancelar: { backgroundColor: '#C62828' },
  btnSalvar: { backgroundColor: '#2E7D32' },
  btnAcaoTexto: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },

  /* Botão Logout Estilizado */
  btnLogout: {
    flexDirection: 'row',
    height: 46,
    borderRadius: 12,
    backgroundColor: '#FFEBEE',
    borderWidth: 1,
    borderColor: '#FFCDD2',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  btnLogoutTexto: {
    color: '#D32F2F',
    fontSize: 13,
    fontWeight: '700',
  },

  pressionado: { opacity: 0.8 },
});