import React, { useState, useEffect } from 'react';
import { Text, View, SafeAreaView, ScrollView, TextInput, Pressable, Image, StatusBar, ActivityIndicator, Alert, StyleSheet, } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { atualizarPerfilAluno, obterPerfilAluno } from '@/services/api';
import {styles} from '@/screens/Login/perfil.styles';

export default function PerfilScreen() {
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [foto, setFoto] = useState<string | null>(null);
  const [nomeCompleto, setNomeCompleto] = useState('');
  const [dataNascimento, setDataNascimento] = useState('');
  const [cpf, setCpf] = useState('');
  const [email, setEmail] = useState('');
  const [telefone, setTelefone] = useState('');
  const [responsaveis, setResponsaveis] = useState('');
  const [cpfResponsaveis, setCpfResponsaveis] = useState('');
  const [telefoneResponsaveis, setTelefoneResponsaveis] = useState('');
  const [menorDeIdade, setMenorDeIdade] = useState(false);
  const idioma = 'Português';

  useEffect(() => {
    let active = true;

    async function fetchPerfil() {
      try {
        const data = await obterPerfilAluno();
        if (!active) return;

        setNomeCompleto(data.nome_completo);
        setDataNascimento(data.perfil.data_nascimento);
        setMenorDeIdade(data.perfil.possui_responsavel);
        setCpf(data.perfil.cpf ?? '');
        setEmail(data.email);
        setTelefone(data.perfil.telefone ?? '');
        setResponsaveis(data.perfil.responsavel_nome ?? '');
        setCpfResponsaveis(data.perfil.responsavel_cpf ?? '');
        setTelefoneResponsaveis(data.perfil.responsavel_telefone ?? '');
      } catch (error) {
        console.error(error);
        if (active) {
          Alert.alert(
            'Erro',
            error instanceof Error
              ? error.message
              : 'Não foi possível carregar os dados do usuário.',
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void fetchPerfil();
    return () => {
      active = false;
    };
  }, []);

  // Função para selecionar/fazer upload da foto
  const handleSelecionarFoto = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (!permissionResult.granted) {
      Alert.alert('Permissão negada', 'Precisamos de permissão para acessar sua galeria de fotos.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setFoto(result.assets[0].uri);
    }
  };

  const handleSalvar = async () => {
    setSalvando(true);
    try {
      const nome = nomeCompleto.trim();
      if (!nome) {
        throw new Error('Informe o nome completo antes de salvar.');
      }

      const payload: Record<string, string> = {
        nome_completo: nome,
      };

      if (menorDeIdade) {
        const responsavelNome = responsaveis.trim();
        const responsavelCpf = cpfResponsaveis.trim();
        const responsavelTelefone = telefoneResponsaveis.trim();

        if (responsavelNome) payload.responsavel_nome = responsavelNome;
        if (responsavelCpf) payload.responsavel_cpf = responsavelCpf;
        if (responsavelTelefone) payload.responsavel_telefone = responsavelTelefone;
      } else {
        const telefoneFormatado = telefone.trim();
        if (telefoneFormatado) payload.telefone = telefoneFormatado;
      }

      const data = await atualizarPerfilAluno(payload);

      setNomeCompleto(data.nome_completo);
      setEmail(data.email);
      setDataNascimento(data.perfil.data_nascimento);
      setMenorDeIdade(data.perfil.possui_responsavel);
      setCpf(data.perfil.cpf ?? '');
      setTelefone(data.perfil.telefone ?? '');
      setResponsaveis(data.perfil.responsavel_nome ?? '');
      setCpfResponsaveis(data.perfil.responsavel_cpf ?? '');
      setTelefoneResponsaveis(data.perfil.responsavel_telefone ?? '');

      Alert.alert(
        'Sucesso',
        'Dados do perfil atualizados. Foto e idioma ainda não são suportados pela API.',
      );
      router.back();
    } catch (error) {
      console.error(error);
      Alert.alert(
        'Erro',
        error instanceof Error ? error.message : 'Não foi possível salvar as alterações.',
      );
    } finally {
      setSalvando(false);
    }
  };

  const handleCancelar = () => {
    router.back();
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" color="#980070" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#7B0087" />

      {/* Header padrão */}
      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >        
      <View style={styles.headerContent}>
        <View style={styles.headerText}>
          <Text style={styles.textPage}>Perfil</Text>
        </View>
          <Pressable onPress={() => router.push('/Menu')} hitSlop={12}>
            <Feather name="menu" size={28} color="#FFFFFF" />
          </Pressable>
        </View>
      </LinearGradient>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        
        {/* Upload de Imagem no lugar do Círculo */}
        <View style={styles.uploadContainer}>
          <Pressable onPress={handleSelecionarFoto} style={styles.avatarWrapper}>
            {foto ? (
              <Image source={{ uri: foto }} style={styles.avatarImage} />
            ) : (
              <View style={styles.avatarPlaceholder}>
                <Ionicons name="camera-outline" size={32} color="#FFFFFF" />
              </View>
            )}
            <View style={styles.cameraIconBadge}>
              <Feather name="edit-2" size={14} color="#FFFFFF" />
            </View>
          </Pressable>
          <Text style={styles.profileNameText}>{nomeCompleto || 'Nome do Usuário'}</Text>
        </View>            
        <View style={styles.sectionHeading}>
          <Feather name="user" size={30} color="#84009A" />
          <Text style={styles.sectionTitle}>Dados Pessoais</Text>
        </View>
        <View style={styles.formGroup}>
          <Text style={styles.label}>Nome Completo</Text>
          <TextInput
            style={styles.input}
            value={nomeCompleto}
            onChangeText={setNomeCompleto}
            placeholder="Digite seu nome completo"
            placeholderTextColor="#8B8790"
            />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>Data de nascimento</Text>
          <View style={styles.inputWithIcon}>
            <TextInput
              style={styles.dateInput}
              value={dataNascimento}
              editable={false}
              placeholder="DD/MM/AAAA"
              placeholderTextColor="#8B8790"
            />
            <Feather name="calendar" size={20} color="#84009A" style={styles.calendarIcon} />
          </View>
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>E-mail</Text>
          <TextInput
            style={styles.input}
            value={email}
            editable={false}
            placeholder="seu@email.com"
            keyboardType="email-address"
          />
        </View>

        {!menorDeIdade && (
          <>
            <View style={styles.formGroup}>
              <Text style={styles.label}>CPF</Text>
              <TextInput
                style={styles.input}
                value={cpf}
                editable={false}
                placeholder="000.000.000-00"
                keyboardType="numeric"
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Telefone</Text>
              <TextInput
                style={styles.input}
                value={telefone}
                onChangeText={setTelefone}
                placeholder="(00) 00000-0000"
                keyboardType="phone-pad"
              />
            </View>
          </>
        )}

        {menorDeIdade && (
          <>
            <View style={styles.formGroup}>
              <Text style={styles.label}>Responsáveis</Text>
              <TextInput
                style={styles.input}
                value={responsaveis}
                onChangeText={setResponsaveis}
                placeholder="Nome dos responsáveis"
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>CPF Responsáveis</Text>
              <TextInput
                style={styles.input}
                value={cpfResponsaveis}
                onChangeText={setCpfResponsaveis}
                placeholder="000.000.000-00"
                keyboardType="numeric"
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.label}>Telefone Responsáveis</Text>
              <TextInput
                style={styles.input}
                value={telefoneResponsaveis}
                onChangeText={setTelefoneResponsaveis}
                placeholder="(00) 00000-0000"
                keyboardType="phone-pad"
              />
            </View>
          </>
        )}

        <View style={styles.formGroup}>
          <Text style={styles.label}>Idioma de Preferência do App</Text>
          <View style={styles.selectBox}>
            <Text style={styles.selectText}>{idioma}</Text>
            <Feather name="chevron-down" size={20} color="#333" />
          </View>
        </View>

        <View style={styles.actionButtonsContainer}>
          <Pressable 
            style={[styles.button, styles.cancelButton]} 
            onPress={handleCancelar}
            disabled={salvando}
          >
            <Text style={styles.cancelButtonText}>Cancelar</Text>
          </Pressable>

          <Pressable 
            style={[styles.button, styles.saveButton]} 
            onPress={handleSalvar}
            disabled={salvando}
          >
            <LinearGradient 
              start={{ x: 0.65, y: 0 }}
              end={{ x: 0.35, y: 1 }}
              colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
              locations={[0.12, 1.0]}
              pointerEvents="none"
              style={styles.saveGradient}
            />
            {salvando ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.saveButtonText}>Salvar</Text>
            )}
          </Pressable>

        </View>

      </ScrollView>
    </SafeAreaView>
  );
}
