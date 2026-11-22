import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View, } from 'react-native';
import { BlurTargetView, BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { List_item, StatusConfig, type ListItemStatus } from '@/components/list_item';
import { styles } from '@/screens/Home/home.styles';
import { activityModalStyles } from '@/screens/Atividades/atividades.styles';
import { enviarEntregaAtividade, obterMinhaAtividade, obterMinhasAtividades, type MinhaAtividadeApi, type MinhaAtividadeDetalheApi } from '@/services/api';
import * as DocumentPicker from 'expo-document-picker';

const statusLabels: Record<ListItemStatus, string> = {
  vencida: 'Vencida',
  proxima: 'Próxima',
  realizada: 'Realizada',
};

interface Activity {
  id: number;
  titulo: string;
  categoria: 'Atividade';
  dataHora: string;
  status: ListItemStatus;
}

function prazoEncerrado(venceEm: string): boolean {
  return new Date(venceEm).getTime() < Date.now();
}

function mapearAtividade(atividade: MinhaAtividadeApi): Activity {
  const entregue = atividade.status !== null;
  const vencida = prazoEncerrado(atividade.vence_em);

  return {
    id: atividade.id,
    titulo: atividade.titulo,
    categoria: 'Atividade',
    dataHora: new Date(atividade.vence_em).toLocaleString('pt-BR'),
    status: entregue ? 'realizada' : vencida ? 'vencida' : 'proxima',
  };
}

export default function AtividadesScreen() {
  const blurTargetRef = useRef<View | null>(null);
  const detailRequestRef = useRef(0);
  const submissionInProgressRef = useRef(false);
  const [atividades, setAtividades] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [activityDetail, setActivityDetail] = useState<MinhaAtividadeDetalheApi | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [envioBloqueado, setEnvioBloqueado] = useState(false);
  const [response, setResponse] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [attachments, setAttachments] = useState<DocumentPicker.DocumentPickerAsset[]>([]);

  const loadActivities = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const resultado = await obterMinhasAtividades();
      setAtividades(resultado.map(mapearAtividade));
    } catch (error) {
      console.error('Erro ao carregar atividades:', error);
      setLoadError(
        error instanceof Error ? error.message : 'Não foi possível carregar as atividades.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const fetchActivities = async () => {
      try {
        const resultado = await obterMinhasAtividades();
        if (active) {
          setAtividades(resultado.map(mapearAtividade));
        }
      } catch (error) {
        console.error('Erro ao carregar atividades:', error);
        if (active) {
          setLoadError(
            error instanceof Error ? error.message : 'Não foi possível carregar as atividades.',
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void fetchActivities();
    return () => {
      active = false;
    };
  }, []);

  const openActivity = async (activity: Activity) => {
    const requestId = detailRequestRef.current + 1;
    detailRequestRef.current = requestId;
    setSelectedActivity(activity);
    setActivityDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    setResponse('');
    setAttachments([]);

    try {
      const detail = await obterMinhaAtividade(activity.id);
      if (detailRequestRef.current === requestId) {
        setActivityDetail(detail);
        setResponse(detail.entrega?.resposta ?? '');
        setEnvioBloqueado(Boolean(detail.entrega && prazoEncerrado(detail.vence_em)));
      }
    } catch (error) {
      console.error('Erro ao carregar detalhes da atividade:', error);
      if (detailRequestRef.current === requestId) {
        setDetailError(
          error instanceof Error ? error.message : 'Não foi possível carregar a atividade.',
        );
      }
    } finally {
      if (detailRequestRef.current === requestId) {
        setDetailLoading(false);
      }
    }
  };

  const closeActivity = () => {
    detailRequestRef.current += 1;
    setSelectedActivity(null);
    setActivityDetail(null);
    setDetailError(null);
    setEnvioBloqueado(false);
    setResponse('');
    setAttachments([]);
  };

  const pickAttachments = async () => {
    if (!activityDetail?.permite_envio_arquivo || submitting) return;

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

  const submitResponse = async () => {
    if (!selectedActivity || !activityDetail || submissionInProgressRef.current) return;

    if (activityDetail.entrega
      && prazoEncerrado(activityDetail.vence_em)) {
      setEnvioBloqueado(true);
      Alert.alert('Prazo encerrado', 'Uma atividade já entregue não pode ser editada após o prazo.');
      return;
    }

    submissionInProgressRef.current = true;
    setSubmitting(true);
    try {
      const entrega = await enviarEntregaAtividade(
        selectedActivity.id,
        response,
        attachments,
        activityDetail.permite_envio_arquivo,
        activityDetail.entrega?.anexos.map((arquivo) => arquivo.id) ?? [],
      );
      setActivityDetail((current) => current
        ? { ...current, status: entrega.status, enviada_em: entrega.enviada_em, entrega }
        : current);
      setEnvioBloqueado(
        prazoEncerrado(activityDetail.vence_em),
      );
      setAtividades((current) => current.map((activity) => (
        activity.id === selectedActivity.id
          ? { ...activity, status: 'realizada' }
          : activity
      )));
      setAttachments([]);
      Alert.alert('Atividade enviada', 'Sua resposta foi enviada com sucesso.');
    } catch (error) {
      console.error('Erro ao enviar atividade:', error);
      Alert.alert(
        'Erro ao enviar',
        error instanceof Error ? error.message : 'Não foi possível enviar a atividade.',
      );
    } finally {
      submissionInProgressRef.current = false;
      setSubmitting(false);
    }
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
                      status={activity.status}
                      onPress={() => void openActivity(activity)}
                    />
                  ))}
                  {loading && <ActivityIndicator size="large" color="#84009A" />}
                  {!loading && loadError && (
                    <View>
                      <Text>{loadError}</Text>
                      <Pressable onPress={() => void loadActivities()} accessibilityRole="button">
                        <Text style={{ color: '#84009A', marginTop: 8 }}>Tentar novamente</Text>
                      </Pressable>
                    </View>
                  )}
                  {!loading && !loadError && atividades.length === 0 && (
                    <Text>Você ainda não tem atividades.</Text>
                  )}
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

                {activityDetail && (
                  <View style={styles.detailInfoRow}>
                    <Feather name="user" size={18} color="#84009A" />
                    <Text style={styles.detailInfoText}>
                      Professor: {activityDetail.professor_nome}
                    </Text>
                  </View>
                )}

                <Text style={styles.descriptionLabel}>Descrição</Text>
                {detailLoading ? (
                  <ActivityIndicator size="small" color="#84009A" />
                ) : detailError ? (
                  <View>
                    <Text style={styles.descriptionText}>{detailError}</Text>
                    <Pressable onPress={() => void openActivity(selectedActivity)} accessibilityRole="button">
                      <Text style={{ color: '#84009A', marginTop: 8 }}>Tentar novamente</Text>
                    </Pressable>
                  </View>
                ) : (
                  <Text style={styles.descriptionText}>{activityDetail?.descricao}</Text>
                )}

                <Text style={activityModalStyles.fieldLabel}>Sua resposta</Text>
                <TextInput
                  value={response}
                  onChangeText={setResponse}
                  placeholder="Escreva sua resposta para a atividade"
                  multiline
                  maxLength={5000}
                  editable={!envioBloqueado && !submitting && !detailLoading}
                  textAlignVertical="top"
                  accessibilityLabel="Resposta da atividade"
                  style={activityModalStyles.responseInput}
                />

                {activityDetail?.permite_envio_arquivo && (
                  <>
                    <Text style={activityModalStyles.fieldLabel}>Arquivos anexados</Text>
                    {!envioBloqueado && (
                      <Pressable
                        onPress={pickAttachments}
                        style={activityModalStyles.attachButton}
                        accessibilityRole="button"
                        accessibilityLabel="Adicionar arquivos"
                        disabled={submitting}
                      >
                        <Feather name="paperclip" size={18} color="#84009A" />
                        <Text style={activityModalStyles.attachButtonText}>Adicionar arquivos</Text>
                      </Pressable>
                    )}
                  </>
                )}

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

                {activityDetail?.entrega?.anexos.map((arquivo) => (
                  <View key={`entrega-${arquivo.id}`} style={activityModalStyles.fileRow}>
                    <Feather name="file" size={16} color="#666666" />
                    <Text numberOfLines={1} style={activityModalStyles.fileName}>{arquivo.nome}</Text>
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
                    accessibilityState={{ disabled: submitting || detailLoading || envioBloqueado || !activityDetail }}
                    disabled={submitting || detailLoading || envioBloqueado || !activityDetail}
                    style={({ pressed }) => [
                      activityModalStyles.submitButton,
                      (submitting || detailLoading || envioBloqueado || !activityDetail) && { opacity: 0.6 },
                      pressed && !submitting && { opacity: 0.8 },
                    ]}
                  >
                    <LinearGradient
                      colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
                      start={{ x: 0.65, y: 0 }}
                      end={{ x: 0.35, y: 1 }}
                      style={activityModalStyles.submitGradient}
                    >
                      {submitting
                        ? <ActivityIndicator size="small" color="#FFFFFF" />
                        : <Feather name="send" size={16} color="#FFFFFF" />}
                      <Text style={activityModalStyles.submitButtonText}>
                        {submitting ? 'Enviando...' : envioBloqueado ? 'Já enviada' : 'Enviar'}
                      </Text>
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
