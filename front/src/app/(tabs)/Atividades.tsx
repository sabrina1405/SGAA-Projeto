import { useRef, useState } from 'react';
import {
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { BlurTargetView, BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { List_item, StatusConfig, type ListItemStatus } from '@/components/list_item';
import styles from '@/screens/Home/home.styles';
import * as DocumentPicker from 'expo-document-picker';

const atividades = [
  {
    id: '2',
    titulo: 'Exercício de Fixação - Flexbox',
    categoria: 'Atividade' as const,
    descricao: 'Criar um layout utilizando alinhamentos.',
    dataHora: '02/11/26 as 10:30',
    nomeAluno: 'Ana Souza',
    status: 'proxima' as const,
  },
];

const statusLabels: Record<ListItemStatus, string> = {
  vencida: 'Vencida',
  proxima: 'Próxima',
  realizada: 'Realizada',
};

type Activity = (typeof atividades)[number];

export default function AtividadesScreen() {
  const blurTargetRef = useRef<View | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [response, setResponse] = useState('');
  const [attachments, setAttachments] = useState<DocumentPicker.DocumentPickerAsset[]>([]);

  const closeActivity = () => {
    setSelectedActivity(null);
    setResponse('');
    setAttachments([]);
  };

  const pickAttachments = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        multiple: true,
        copyToCacheDirectory: true,
      });

      if (!result.canceled) {
        setAttachments((current) => [...current, ...result.assets]);
      }
    } catch (error) {
      console.error('Erro ao selecionar arquivos da atividade:', error);
      Alert.alert('Erro', 'Não foi possível selecionar os arquivos.');
    }
  };

  const submitResponse = () => {
    console.log('Envio da atividade acionado.', {
      activityId: selectedActivity?.id,
      hasResponse: Boolean(response.trim()),
      attachmentCount: attachments.length,
    });

    if (!response.trim() && attachments.length === 0) {
      console.log('Envio interrompido: resposta e anexos estão vazios.');
      Alert.alert('Resposta vazia', 'Escreva uma resposta ou anexe um arquivo antes de enviar.');
      return;
    }

    console.log('Envio não realizado: a tela ainda não está conectada ao serviço de envio.');
    Alert.alert(
      'Envio indisponível',
      'A resposta e os arquivos estão prontos, mas esta tela ainda não está conectada ao serviço de envio.',
    );
  };

  return (
    <View style={styles.root}>
      <BlurTargetView ref={blurTargetRef} style={styles.root}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.container}>
            <LinearGradient
              colors={['#7B0087', '#980070', '#C40E35']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.header}
            >
            <View style={styles.headerContent}>
                <View style={styles.headerText}>
                    <Text style={styles.textPage}>Atividades</Text>
                </View>

                <Pressable
                  onPress={() => router.push('/Menu')}
                  hitSlop={12}
                  accessibilityRole="button"
                  accessibilityLabel="Abrir menu"
                  style={({ pressed }) => [
                    styles.menuButton,
                    pressed && styles.menuButtonPressed,
                  ]}
                >
                  <Feather name="menu" size={34} color="#FFFFFF" 
                  style={{paddingVertical: 14}}/>
                </Pressable>
              </View>
            </LinearGradient>

            <ScrollView
              style={styles.scroll}
              contentContainerStyle={styles.scrollContent}
              showsVerticalScrollIndicator={false}
            >
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>ATIVIDADES</Text>
                <View style={styles.listContainer}>
                  {atividades.map((activity) => (
                    <List_item
                      key={activity.id}
                      titulo={activity.titulo}
                      categoria={activity.categoria}
                      dataHora={activity.dataHora}
                      nomeAluno={activity.nomeAluno}
                      status={activity.status}
                      onPress={() => {
                        setResponse('');
                        setAttachments([]);
                        setSelectedActivity(activity);
                      }}
                    />
                  ))}
                </View>
              </View>
            </ScrollView>
          </View>
        </SafeAreaView>
      </BlurTargetView>

      {selectedActivity && (
        <View style={styles.modalOverlay}>
          <BlurView
            blurTarget={blurTargetRef}
            intensity={70}
            tint="dark"
            blurMethod="dimezisBlurView"
            pointerEvents="none"
            style={StyleSheet.absoluteFill}
          />

          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={closeActivity}
            accessibilityRole="button"
            accessibilityLabel="Fechar detalhes"
          />

          <View style={styles.modalContent} pointerEvents="box-none">
            <ScrollView
              style={activityModalStyles.scroll}
              contentContainerStyle={activityModalStyles.scrollContent}
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
            >
              <View style={styles.detailCard} accessibilityViewIsModal>
                <View style={styles.detailHeader}>
                  <View style={styles.detailHeading}>
                    <Text style={styles.detailEyebrow}>{selectedActivity.categoria}</Text>
                    <Text style={styles.detailTitle}>{selectedActivity.titulo}</Text>
                  </View>

                  <Pressable
                    onPress={closeActivity}
                    accessibilityRole="button"
                    accessibilityLabel="Fechar detalhes"
                    hitSlop={12}
                    style={styles.closeButton}
                  >
                    <Feather name="x" size={22} color="#555" />
                  </Pressable>
                </View>

                <View style={styles.detailDivider} />

                <View style={styles.detailStatus}>
                  <View
                    style={[
                      styles.statusDot,
                      { backgroundColor: StatusConfig[selectedActivity.status].cor },
                    ]}
                  >
                  </View>
                  <Text style={styles.detailStatusText}>
                    {statusLabels[selectedActivity.status]}
                  </Text>
                </View>

                <View style={styles.detailInfoRow}>
                  <Feather name="calendar" size={18} color="#84009A" />
                  <Text style={styles.detailInfoText}>{selectedActivity.dataHora}</Text>
                </View>

                {selectedActivity.nomeAluno && (
                  <View style={styles.detailInfoRow}>
                    <Feather name="user" size={18} color="#84009A" />
                    <Text style={styles.detailInfoText}>{selectedActivity.nomeAluno}</Text>
                  </View>
                )}

                <Text style={styles.descriptionLabel}>Descrição</Text>
                <Text style={styles.descriptionText}>{selectedActivity.descricao}</Text>

                <Text style={activityModalStyles.fieldLabel}>Sua resposta</Text>
                <TextInput
                  value={response}
                  onChangeText={setResponse}
                  placeholder="Escreva sua resposta para a atividade"
                  multiline
                  textAlignVertical="top"
                  accessibilityLabel="Resposta da atividade"
                  style={activityModalStyles.responseInput}
                />

                <Text style={activityModalStyles.fieldLabel}>Arquivos anexados</Text>
                <Pressable
                  onPress={pickAttachments}
                  style={activityModalStyles.attachButton}
                  accessibilityRole="button"
                  accessibilityLabel="Adicionar arquivos"
                >
                  <Feather name="paperclip" size={18} color="#84009A" />
                  <Text style={activityModalStyles.attachButtonText}>Adicionar arquivos</Text>
                </Pressable>

                {attachments.map((file, index) => (
                  <View key={`${file.uri}-${index}`} style={activityModalStyles.fileRow}>
                    <Feather name="file" size={16} color="#666666" />
                    <Text numberOfLines={1} style={activityModalStyles.fileName}>{file.name}</Text>
                    <Pressable
                      onPress={() => setAttachments((current) => current.filter((_, i) => i !== index))}
                      hitSlop={8}
                      accessibilityRole="button"
                      accessibilityLabel={`Remover arquivo ${file.name}`}
                    >
                      <Feather name="x" size={18} color="#B42318" />
                    </Pressable>
                  </View>
                ))}

                <View style={activityModalStyles.actions}>
                  <Pressable
                    onPress={closeActivity}
                    style={activityModalStyles.cancelButton}
                    accessibilityRole="button"
                  >
                    <Text style={activityModalStyles.cancelButtonText}>Cancelar</Text>
                  </Pressable>
                  <Pressable
                    onPress={submitResponse}
                    accessibilityRole="button"
                    accessibilityLabel="Enviar resposta da atividade"
                    style={activityModalStyles.submitButton}
                  >
                    <LinearGradient
                      colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
                      start={{ x: 0.65, y: 0 }}
                      end={{ x: 0.35, y: 1 }}
                      style={activityModalStyles.submitGradient}
                    >
                      <Feather name="send" size={16} color="#FFFFFF" />
                      <Text style={activityModalStyles.submitButtonText}>Enviar</Text>
                    </LinearGradient>
                  </Pressable>
                </View>
              </View>
            </ScrollView>
          </View>
        </View>
      )}
    </View>
  );
}

const activityModalStyles = StyleSheet.create({
  scroll: {
    width: '100%',
    maxHeight: '90%',
  },
  
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingVertical: 12,
  },

  fieldLabel: {
    marginTop: 18,
    marginBottom: 8,
    color: '#292929',
    fontSize: 14,
    fontWeight: '700',
  },

  responseInput: {
    minHeight: 100,
    padding: 12,
    borderWidth: 1,
    borderColor: '#D8C8DC',
    borderRadius: 10,
    color: '#333333',
    fontSize: 14,
  },

  attachButton: {
    minHeight: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#84009A',
    borderStyle: 'dashed',
    borderRadius: 10,
    backgroundColor: '#FAF6FB',
  },

  attachButtonText: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: '600',
  },
  
  fileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 8,
    padding: 10,
    borderRadius: 8,
    backgroundColor: '#F3F0F4',
  },

  fileName: {
    flex: 1,
    color: '#444444',
    fontSize: 13,
  },

  actions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 20,
  },

  cancelButton: {
    minHeight: 48,
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    backgroundColor: '#B42318',
    borderColor: '#B42318',
    borderRadius: 10,
  },

  cancelButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },

  submitButton: {
    flex: 1,
    overflow: 'hidden',
    borderRadius: 10,
  },
  submitGradient: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 12,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});