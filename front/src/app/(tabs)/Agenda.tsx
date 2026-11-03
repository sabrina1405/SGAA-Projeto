import React, { useCallback, useState, useEffect, useMemo } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  SafeAreaView,
  ScrollView,
  Pressable,
  StatusBar,
  ActivityIndicator,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { List_item, type ListItemStatus, type ListItemCategory } from '../../components/list_item';
import { Calendar, LocaleConfig } from 'react-native-calendars';
import DateTimePicker, { type DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { paleta } from '@/components/theme/colors';
import { obterAulas, type AulaApi } from '@/services/api';

interface AulaItem {
  id: string;
  titulo: string;
  categoria: ListItemCategory;
  dataHora: string;
  dataIso: string;
  descricao: string;
  nomeAluno?: string;
  status: ListItemStatus;
  cancelada?: boolean;
  motivoCancelamento?: string;
}

type ViewMode = 'MES' | 'SEMANA' | 'DIA';
type StatusFilter = ListItemStatus | 'todos';
type PickerMode = 'date' | 'time';
type ModalMode = 'actions' | 'reschedule';
type CalendarMarks = Record<string, {
  type?: 'multi-dot';
  dots?: { key: string; color: string }[];
  selected?: boolean;
  selectedColor?: string;
}>;

function formatDateIso(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function mapearAula(aula: AulaApi): AulaItem {
  const date = new Date(aula.data_hora);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Data inválida recebida pela API: ${aula.data_hora}`);
  }

  return {
    id: String(aula.id),
    titulo: aula.titulo,
    categoria: 'Aula',
    dataHora: date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    dataIso: formatDateIso(date),
    descricao: aula.descricao,
    nomeAluno: aula.nome_aluno ?? undefined,
    status: aula.status,
    cancelada: aula.cancelada,
    motivoCancelamento: aula.motivo_cancelamento ?? undefined,
  };
}

function parseDateIso(dateIso: string) {
  const [year, month, day] = dateIso.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function getAppointmentDate(aula: AulaItem) {
  const date = parseDateIso(aula.dataIso);
  const time = /(\d{2}):(\d{2})$/.exec(aula.dataHora);
  if (time) {
    date.setHours(Number(time[1]), Number(time[2]), 0, 0);
  }
  return date;
}

function formatAppointmentDateTime(date: Date) {
  const dateLabel = date.toLocaleDateString('pt-BR');
  const timeLabel = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  return `${dateLabel} ${timeLabel}`;
}

LocaleConfig.locales['pt-br'] = {
  monthNames: [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ],
  monthNamesShort: [
    'Jan.', 'Fev.', 'Mar.', 'Abr.', 'Mai.', 'Jun.',
    'Jul.', 'Ago.', 'Set.', 'Out.', 'Nov.', 'Dez.',
  ],
  dayNames: [
    'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
    'Quinta-feira', 'Sexta-feira', 'Sábado',
  ],
  dayNamesShort: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
  today: 'Hoje',
};
LocaleConfig.defaultLocale = 'pt-br';

export default function AgendaScreen() {
  const [loading, setLoading] = useState(true);
  const [aulas, setAulas] = useState<AulaItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('MES');
  const [selectedDate, setSelectedDate] = useState(() => formatDateIso(new Date()));
  const [visibleDate, setVisibleDate] = useState(() => formatDateIso(new Date()));
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('todos');
  const [statusFilterOpen, setStatusFilterOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<AulaItem | null>(null);
  const [modalMode, setModalMode] = useState<ModalMode>('actions');
  const [rescheduleDate, setRescheduleDate] = useState(new Date());
  const [pickerMode, setPickerMode] = useState<PickerMode | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const statusOptions: { value: StatusFilter; label: string }[] = [
    { value: 'todos', label: 'Todos' },
    { value: 'vencida', label: 'Vencida' },
    { value: 'proxima', label: 'Pendente' },
    { value: 'realizada', label: 'Realizada' },
  ];

  const aulasFiltradas = useMemo(
    () => aulas.filter((aula) => (
      !aula.cancelada && (statusFilter === 'todos' || aula.status === statusFilter)
    )),
    [aulas, statusFilter],
  );

  const abrirAgendamento = useCallback((aula: AulaItem) => {
    setSelectedAppointment(aula);
    setModalMode('actions');
    setRescheduleDate(getAppointmentDate(aula));
    setPickerMode(null);
    setCancelReason('');
  }, []);

  const aulasPorDia = useMemo(
    () => aulasFiltradas.reduce<Record<string, AulaItem[]>>((porDia, aula) => {
      porDia[aula.dataIso] = [...(porDia[aula.dataIso] ?? []), aula];
      return porDia;
    }, {}),
    [aulasFiltradas],
  );

  const calendarDayComponent = useMemo(() => {
    const CalendarDay: NonNullable<React.ComponentProps<typeof Calendar>['dayComponent']> = ({
      date,
      state,
      onPress,
    }) => {
      const appointments = date ? aulasPorDia[date.dateString] ?? [] : [];
      const isSelected = state === 'selected';

      return (
        <View style={styles.calendarDay}>
          <Pressable
            onPress={() => date && onPress?.(date)}
            style={[styles.calendarDayButton, isSelected && styles.calendarDaySelected]}
            accessibilityRole="button"
            accessibilityLabel={`${date?.day ?? ''}`}
          >
            <Text style={[styles.calendarDayNumber, isSelected && styles.calendarDayNumberSelected]}>
              {date?.day}
            </Text>
          </Pressable>
          {appointments.slice(0, 2).map((appointment) => {
            const backgroundColor = appointment.status === 'vencida'
              ? '#ef4444'
              : appointment.status === 'proxima'
                ? '#f59e0b'
                : '#10b981';

            return (
              <Pressable
                key={appointment.id}
                onPress={() => abrirAgendamento(appointment)}
                style={[styles.calendarAppointment, { backgroundColor }]}
                accessibilityRole="button"
                accessibilityLabel={`Abrir agendamento ${appointment.titulo}, ${appointment.dataHora}`}
              >
                <Text numberOfLines={1} style={styles.calendarAppointmentText}>
                  {appointment.dataHora.slice(-5)} {appointment.titulo}
                </Text>
              </Pressable>
            );
          })}
          {appointments.length > 2 && (
            <Text style={styles.moreAppointments}>+{appointments.length - 2} mais</Text>
          )}
        </View>
      );
    };

    return CalendarDay;
  }, [aulasPorDia, abrirAgendamento]);

  const fecharAgendamento = () => {
    setSelectedAppointment(null);
    setPickerMode(null);
  };

  const handlePickerChange = (event: DateTimePickerEvent, date?: Date) => {
    if (date && event.type !== 'dismissed') {
      setRescheduleDate(date);
    }
    if (Platform.OS !== 'ios' || event.type === 'dismissed') {
      setPickerMode(null);
    }
  };

  const confirmarRemarcacao = () => {
    if (!selectedAppointment) {
      return;
    }

    const updatedAppointment = {
      ...selectedAppointment,
      dataIso: formatDateIso(rescheduleDate),
      dataHora: formatAppointmentDateTime(rescheduleDate),
    };

    setAulas((current) => current.map((aula) => (
      aula.id === updatedAppointment.id ? updatedAppointment : aula
    )));
    setSelectedDate(updatedAppointment.dataIso);
    setVisibleDate(updatedAppointment.dataIso);
    setViewMode('DIA');
    fecharAgendamento();
  };

  const confirmarCancelamento = () => {
    if (!selectedAppointment) {
      return;
    }
    if (!cancelReason.trim()) {
      Alert.alert('Informe o motivo', 'Digite o motivo do cancelamento para continuar.');
      return;
    }

    setAulas((current) => current.map((aula) => (
      aula.id === selectedAppointment.id
        ? { ...aula, cancelada: true, motivoCancelamento: cancelReason.trim() }
        : aula
    )));
    fecharAgendamento();
    Alert.alert('Agendamento cancelado', `Motivo registrado: ${cancelReason.trim()}`);
  };

  const loadAulas = useCallback(
    async () => (await obterAulas()).map(mapearAula),
    [],
  );

  const handleLoadError = useCallback((error: unknown) => {
    console.error('Erro ao buscar aulas:', error);
    setLoadError(
      error instanceof Error
        ? error.message
        : 'Não foi possível carregar as aulas.',
    );
  }, []);

  const retryAulas = () => {
    setLoading(true);
    setLoadError(null);
    void loadAulas()
      .then(setAulas)
      .catch(handleLoadError)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    let active = true;
    loadAulas()
      .then((data) => {
        if (active) setAulas(data);
      })
      .catch((error: unknown) => {
        if (active) handleLoadError(error);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [handleLoadError, loadAulas]);

  const markedDates = useMemo<CalendarMarks>(() => {
    const marks: CalendarMarks = {};

    aulasFiltradas.forEach((aula) => {
      const currentMark = marks[aula.dataIso];
      const color = aula.status === 'vencida'
        ? '#ef4444'
        : aula.status === 'proxima'
          ? '#f59e0b'
          : '#10b981';

      marks[aula.dataIso] = {
        ...currentMark,
        type: 'multi-dot',
        dots: [...(currentMark?.dots ?? []), { key: aula.id, color }],
      };
    });

    marks[selectedDate] = {
      ...marks[selectedDate],
      selected: true,
      selectedColor: '#84009A',
    };

    return marks;
  }, [aulasFiltradas, selectedDate]);

  const aulasVisiveis = useMemo(() => {
    if (viewMode === 'MES') {
      const visibleMonth = visibleDate.slice(0, 7);
      return aulasFiltradas.filter((aula) => aula.dataIso.startsWith(visibleMonth));
    }

    const selectedDay = parseDateIso(selectedDate);
    if (viewMode === 'DIA') {
      return aulasFiltradas.filter((aula) => aula.dataIso === selectedDate);
    }

    const weekStart = new Date(selectedDay);
    weekStart.setDate(weekStart.getDate() - ((weekStart.getDay() + 6) % 7));
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);
    const startIso = formatDateIso(weekStart);
    const endIso = formatDateIso(weekEnd);

    return aulasFiltradas.filter((aula) => aula.dataIso >= startIso && aula.dataIso <= endIso);
  }, [aulasFiltradas, selectedDate, viewMode, visibleDate]);

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <ActivityIndicator color="#7B0087" size="large" />
      </SafeAreaView>
    );
  }

  if (loadError) {
    return (
      <SafeAreaView style={[styles.container, styles.center]}>
        <Text>{loadError}</Text>
        <Pressable onPress={retryAulas} accessibilityRole="button">
          <Text>Tentar novamente</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar backgroundColor="#7B0087" barStyle="light-content" />

      {/* Header com Gradiente */}
      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerText}>
            <Text style={styles.textPage}>Agenda</Text>
          </View>

          <Pressable onPress={() => router.push('/Menu')} hitSlop={12}>
            <Feather color="#FFFFFF" name="menu" size={30} 
            style={{paddingVertical: 14}}/>
          </Pressable>
        </View>
      </LinearGradient>

      <View style={styles.topFiltersContainer}>
        {(['MES', 'SEMANA', 'DIA'] as ViewMode[]).map((mode) => (
          <Pressable
            key={mode}
            onPress={() => setViewMode(mode)}
            style={[styles.filterTab, viewMode === mode && styles.filterTabActive]}
          >
            <Text style={[styles.filterTabText, viewMode === mode && styles.filterTabTextActive]}>
              {mode}
            </Text>
          </Pressable>
        ))}

        <Pressable
          style={styles.filterStatusButton}
          onPress={() => setStatusFilterOpen((isOpen) => !isOpen)}
          accessibilityRole="button"
          accessibilityLabel="Filtrar aulas por status"
          accessibilityState={{ expanded: statusFilterOpen }}
        >
          <Text style={styles.filterStatusText}>
            {statusFilter === 'todos'
              ? 'STATUS'
              : statusOptions.find((option) => option.value === statusFilter)?.label}
          </Text>
          <Ionicons
            name={statusFilterOpen ? 'chevron-up' : 'filter'}
            size={14}
            color="#FFFFFF"
            style={{ marginLeft: 4 }}
          />
        </Pressable>
      </View>

      {statusFilterOpen && (
        <View style={styles.statusFilterPanel}>
          <Text style={styles.statusFilterTitle}>Filtrar por status</Text>
          <View style={styles.statusOptions}>
            {statusOptions.map((option) => {
              const isSelected = statusFilter === option.value;
              return (
                <Pressable
                  key={option.value}
                  onPress={() => {
                    setStatusFilter(option.value);
                    setStatusFilterOpen(false);
                  }}
                  style={[
                    styles.statusOption,
                    isSelected && styles.statusOptionSelected,
                  ]}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                >
                  <Text
                    style={[
                      styles.statusOptionText,
                      isSelected && styles.statusOptionTextSelected,
                    ]}
                  >
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      )}

      <View style={styles.todayContainer}>
        <Pressable
          onPress={() => {
            const today = formatDateIso(new Date());
            setSelectedDate(today);
            setVisibleDate(today);
            setViewMode('DIA');
          }}
          accessibilityRole="button"
          accessibilityLabel="Ir para a data atual"
          hitSlop={8}
        >
          <Text style={styles.todayButtonText}>Hoje</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={styles.calendarContent} showsVerticalScrollIndicator={false}>
        <Calendar
          current={visibleDate}
          initialDate={visibleDate}
          firstDay={1}
          hideExtraDays
          enableSwipeMonths
          markedDates={markedDates}
          dayComponent={calendarDayComponent}
          onDayPress={({ dateString }) => {
            setSelectedDate(dateString);
            setVisibleDate(dateString);
            setViewMode('DIA');
          }}
          onMonthChange={({ dateString }) => setVisibleDate(dateString)}
          renderArrow={(direction) => (
            <Ionicons
              name={direction === 'left' ? 'chevron-back' : 'chevron-forward'}
              size={22}
              color="#84009A"
            />
          )}
          style={styles.calendar}
          theme={{
            backgroundColor: '#FFFFFF',
            calendarBackground: '#FFFFFF',
            textSectionTitleColor: '#666666',
            monthTextColor: '#333333',
            selectedDayBackgroundColor: '#84009A',
            selectedDayTextColor: '#FFFFFF',
            todayTextColor: '#C40E35',
            dayTextColor: '#333333',
            textDisabledColor: '#CCCCCC',
            arrowColor: '#84009A',
            textMonthFontSize: 16,
            textMonthFontWeight: 'bold',
            textDayHeaderFontSize: 11,
            textDayHeaderFontWeight: 'bold',
            textDayFontSize: 13,
          }}
        />

        <View style={styles.sectionListContainer}>
          <Text style={styles.sectionHeaderLabel}>
            {viewMode === 'MES'
              ? 'AULAS DO MÊS'
              : viewMode === 'SEMANA'
                ? 'AULAS DA SEMANA'
                : 'AULAS DO DIA'}
          </Text>
          {aulasVisiveis.length ? aulasVisiveis.map((aula) => (
            <List_item
                key={aula.id}
                categoria={aula.categoria}
                dataHora={aula.dataHora}
                nomeAluno={aula.nomeAluno}
                onPress={() => abrirAgendamento(aula)}
                status={aula.status}
                titulo={aula.titulo}
              />
            )) : (
              <Text style={styles.emptyState}>Nenhuma aula para este período.</Text>
            )}
        </View>
      </ScrollView>

      <Modal
        visible={selectedAppointment !== null}
        transparent
        animationType="fade"
        onRequestClose={fecharAgendamento}
      >
        <KeyboardAvoidingView
          style={styles.modalOverlay}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={fecharAgendamento}
            accessibilityRole="button"
            accessibilityLabel="Fechar detalhes do agendamento"
          />
          <View style={styles.modalCard}>
            <ScrollView
              keyboardShouldPersistTaps="handled"
              showsVerticalScrollIndicator={false}
            >
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Detalhes do agendamento</Text>
                <Pressable
                  onPress={fecharAgendamento}
                  hitSlop={10}
                  accessibilityRole="button"
                  accessibilityLabel="Fechar"
                >
                  <Feather name="x" size={22} color="#666666" />
                </Pressable>
              </View>

              {selectedAppointment && (
                <>
                  <Text style={styles.detailLabel}>Título</Text>
                  <Text style={styles.detailValue}>{selectedAppointment.titulo}</Text>

                  <Text style={styles.detailLabel}>Descrição</Text>
                  <Text style={styles.detailValue}>{selectedAppointment.descricao}</Text>

                  <Text style={styles.detailLabel}>Data e hora</Text>
                  <Text style={styles.detailValue}>{selectedAppointment.dataHora}</Text>

                  {selectedAppointment.nomeAluno && (
                    <>
                      <Text style={styles.detailLabel}>Aluno</Text>
                      <Text style={styles.detailValue}>{selectedAppointment.nomeAluno}</Text>
                    </>
                  )}
                </>
              )}

              {modalMode === 'actions' ? (
                <>
                  <Text style={styles.inputLabel}>Motivo do cancelamento/Remarcação</Text>
                  <TextInput
                    value={cancelReason}
                    onChangeText={setCancelReason}
                    placeholder="Descreva o motivo"
                    multiline
                    textAlignVertical="top"
                    accessibilityLabel="Motivo do cancelamento"
                    style={styles.reasonInput}
                  />

                  <Pressable
                    onPress={() => setModalMode('reschedule')}
                    style={styles.secondaryAction}
                    accessibilityRole="button"
                  >
                    <Feather name="calendar" size={18} color="#84009A" />
                    <Text style={styles.secondaryActionText}>Remarcar</Text>
                  </Pressable>
                  <Pressable
                    onPress={confirmarCancelamento}
                    style={styles.destructiveAction}
                    accessibilityRole="button"
                  >
                    <Text style={styles.destructiveActionText}>Cancelar agendamento</Text>
                  </Pressable>
                <Pressable
                    onPress={confirmarCancelamento}
                    style={styles.sendButton}
                    accessibilityRole="button"
                    accessibilityLabel="Enviar motivo e cancelar agendamento"
                  >
                    <LinearGradient
                      colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
                      start={{ x: 0.65, y: 0 }}
                      end={{ x: 0.35, y: 1 }}
                      style={styles.sendButtonGradient}
                    >
                      <Feather name="send" size={16} color="#FFFFFF" />
                      <Text style={styles.sendButtonText}>Enviar</Text>
                    </LinearGradient>
                  </Pressable>
                </>
              ) : (
                <>
                  <Text style={styles.inputLabel}>Nova data e hora</Text>
                  <View style={styles.dateTimeActions}>
                    <Pressable
                      onPress={() => setPickerMode('date')}
                      style={styles.dateTimeButton}
                      accessibilityRole="button"
                    >
                      <Feather name="calendar" size={16} color="#84009A" />
                      <Text style={styles.dateTimeButtonText}>
                        {rescheduleDate.toLocaleDateString('pt-BR')}
                      </Text>
                    </Pressable>
                    <Pressable
                      onPress={() => setPickerMode('time')}
                      style={styles.dateTimeButton}
                      accessibilityRole="button"
                    >
                      <Feather name="clock" size={16} color="#84009A" />
                      <Text style={styles.dateTimeButtonText}>
                        {rescheduleDate.toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </Text>
                    </Pressable>
                  </View>

                  {pickerMode && (
                    <DateTimePicker
                      value={rescheduleDate}
                      mode={pickerMode}
                      display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                      onChange={handlePickerChange}
                    />
                  )}

                  <Pressable
                    onPress={confirmarRemarcacao}
                    style={styles.primaryAction}
                    accessibilityRole="button"
                  >
                    <Text style={styles.primaryActionText}>Confirmar remarcação</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => {
                      setPickerMode(null);
                      setModalMode('actions');
                    }}
                    style={styles.backAction}
                    accessibilityRole="button"
                  >
                    <Text style={styles.backActionText}>Voltar</Text>
                  </Pressable>
                </>
              )}
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  header: {
    height: 106,
    paddingHorizontal: 13,
    paddingTop: 15,
    paddingBottom: 13,
  },
  
  headerContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  
  headerText: {
    flex: 1,
  },

  textPage: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: 'bold',
    alignSelf: 'center',
    paddingVertical: 14,
  },
  
  topFiltersContainer: {
    flexDirection: 'row',
    padding: 12,
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  filterTab: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 16,
    backgroundColor: paleta.purple04,
  },
  filterTabActive: {
    backgroundColor: paleta.purple02,
  },
  filterTabText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#fff',
  },
  filterTabTextActive: {
    color: '#FFF',
  },
  filterStatusButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: paleta.purple02,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
  },
  filterStatusText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  statusFilterPanel: {
    padding: 14,
    backgroundColor: '#F7F1F8',
  },
  statusFilterTitle: {
    marginBottom: 10,
    color: '#333333',
    fontSize: 14,
    fontWeight: '700',
  },
  statusOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  statusOption: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: '#D8C8DC',
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
  },
  statusOptionSelected: {
    borderColor: '#84009A',
    backgroundColor: '#84009A',
  },
  statusOptionText: {
    color: '#555555',
    fontSize: 12,
    fontWeight: '600',
  },
  statusOptionTextSelected: {
    color: '#FFFFFF',
  },
  todayContainer: {
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FFFFFF',
  },
  todayButtonText: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: 'bold',
  },
  calendarContent: {
    paddingBottom: 24,
  },
  calendar: {
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  calendarDay: {
    width: '100%',
    minHeight: 76,
    paddingHorizontal: 2,
    paddingVertical: 3,
  },
  calendarDayButton: {
    alignSelf: 'center',
    minWidth: 24,
    minHeight: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
  },
  calendarDaySelected: {
    backgroundColor: '#84009A',
  },
  calendarDayNumber: {
    color: '#333333',
    fontSize: 12,
    fontWeight: '600',
  },
  calendarDayNumberSelected: {
    color: '#FFFFFF',
  },
  calendarAppointment: {
    marginTop: 2,
    paddingHorizontal: 3,
    paddingVertical: 1,
    borderRadius: 3,
  },
  calendarAppointmentText: {
    color: '#FFFFFF',
    fontSize: 8,
    lineHeight: 11,
  },
  moreAppointments: {
    marginTop: 2,
    color: '#666666',
    fontSize: 8,
  },
  sectionListContainer: {
    padding: 16,
  },
  sectionHeaderLabel: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 12,
  },
  emptyState: {
    color: '#777777',
    fontSize: 14,
    paddingVertical: 12,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
  },
  modalCard: {
    width: '100%',
    maxWidth: 480,
    maxHeight: '90%',
    padding: 20,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    elevation: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 18,
  },
  modalTitle: {
    color: '#333333',
    fontSize: 18,
    fontWeight: '700',
  },
  detailLabel: {
    marginTop: 10,
    color: '#777777',
    fontSize: 12,
    fontWeight: '600',
  },
  detailValue: {
    marginTop: 3,
    color: '#333333',
    fontSize: 15,
  },
  inputLabel: {
    marginTop: 20,
    marginBottom: 8,
    color: '#333333',
    fontSize: 14,
    fontWeight: '700',
  },
  reasonInput: {
    minHeight: 76,
    padding: 10,
    borderWidth: 1,
    borderColor: '#D8C8DC',
    borderRadius: 8,
    color: '#333333',
    fontSize: 14,
  },
  secondaryAction: {
    minHeight: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 18,
    borderWidth: 1,
    borderColor: '#84009A',
    borderRadius: 8,
  },
  secondaryActionText: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: '700',
  },
  primaryAction: {
    minHeight: 46,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
    borderRadius: 8,
    backgroundColor: '#84009A',
  },
  primaryActionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  destructiveAction: {
    minHeight: 46,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
    borderRadius: 8,
    backgroundColor: '#B42318',
  },
  destructiveActionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  dateTimeActions: {
    flexDirection: 'row',
    gap: 10,
  },
  dateTimeButton: {
    minHeight: 44,
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#D8C8DC',
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
  },
  dateTimeButtonText: {
    color: '#333333',
    fontSize: 13,
    fontWeight: '600',
  },
  backAction: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  backActionText: {
    color: '#666666',
    fontSize: 14,
    fontWeight: '600',
  },  sendButton: {
    overflow: 'hidden',
    marginTop: 10,
    borderRadius: 8,
  },
  sendButtonGradient: {
    minHeight: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});