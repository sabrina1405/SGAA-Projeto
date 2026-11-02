import React, { useMemo, useState } from 'react';
import {
  Platform,
  StyleSheet,
  Text,
  TextInput,
  View,
  SafeAreaView,
  ScrollView,
  Pressable,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import DateTimePicker, { type DateTimePickerEvent } from '@react-native-community/datetimepicker';

// Configuração de status solicitada
export const StatusConfig = {
    vencida: {
        icone: "time-outline",
        cor: "#ef4444",
        texto: "Vencida",
        bg: "#ffadad",
    },
    proxima: {
        icone: "time-outline",
        cor: "#f59e0b",
        texto: "Pendente",
        bg: "#ffe599",
    },
    realizada: {
        icone: "checkbox-outline",
        cor: "#10b981",
        texto: "Pago",
        bg: "#d4edda",
    },
} satisfies Record<string, { icone: keyof typeof Ionicons.glyphMap; cor: string; texto: string; bg: string }>;

interface Transacao {
  id: string;
  nome: string;
  vencimento: string;
  dataOriginal: Date | string;
  valor: number;
  status: keyof typeof StatusConfig;
}

type StatusFilter = keyof typeof StatusConfig | 'todos';
type FilterPanel = 'status' | 'valor' | 'data' | null;
type DateFilterTarget = 'inicio' | 'fim';

const transacoes: Transacao[] = [
  {
    id: '1',
    nome: 'Mensalidade - Espanhol',
    vencimento: '22/09/2026',
    dataOriginal: new Date(2026, 8, 22),
    valor: 250.00,
    status: 'vencida',
  },
  {
    id: '2',
    nome: 'Mensalidade - Espanhol',
    vencimento: '28/09/2026',
    dataOriginal: new Date(2026, 8, 28),
    valor: 250.00,
    status: 'proxima',
  },
  {
    id: '3',
    nome: 'Mensalidade - Espanhol',
    vencimento: '22/08/2026',
    dataOriginal: new Date(2026, 7, 22),
    valor: 250.00,
    status: 'realizada',
  },
];

const statusOptions: StatusFilter[] = ['todos', 'vencida', 'proxima', 'realizada'];

function getTransactionDate(value: Transacao['dataOriginal']): Date | null {
  if (typeof value === 'string') {
    const dateOnly = /^(\d{4})-(\d{2})-(\d{2})(?:$|T)/.exec(value);
    if (dateOnly) {
      return new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]));
    }
  }

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function parseCurrencyInput(value: string): number | null {
  const normalized = value.trim().replace(/[^\d,.-]/g, '');
  if (!normalized) {
    return null;
  }

  const amount = normalized.includes(',')
    ? Number(normalized.replace(/\./g, '').replace(',', '.'))
    : Number(normalized);

  return Number.isFinite(amount) ? amount : null;
}

function formatDateFilter(value: Date | null): string {
  return value ? value.toLocaleDateString('pt-BR') : '';
}

export default function FinanceiroScreen() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('todos');
  const [minimumAmount, setMinimumAmount] = useState('');
  const [maximumAmount, setMaximumAmount] = useState('');
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);
  const [filterPanel, setFilterPanel] = useState<FilterPanel>(null);
  const [datePickerTarget, setDatePickerTarget] = useState<DateFilterTarget | null>(null);

  const parsedMinimum = parseCurrencyInput(minimumAmount);
  const parsedMaximum = parseCurrencyInput(maximumAmount);
  const invalidAmountRange = parsedMinimum !== null
    && parsedMaximum !== null
    && parsedMinimum > parsedMaximum;
  const invalidDateRange = startDate !== null
    && endDate !== null
    && startDate.getTime() > endDate.getTime();

  const filteredTransactions = useMemo(() => {
    if (invalidAmountRange || invalidDateRange) {
      return [];
    }

    return transacoes.filter((item) => {
      if (statusFilter !== 'todos' && item.status !== statusFilter) {
        return false;
      }
      if (parsedMinimum !== null && item.valor < parsedMinimum) {
        return false;
      }
      if (parsedMaximum !== null && item.valor > parsedMaximum) {
        return false;
      }

      if (startDate || endDate) {
        const transactionDate = getTransactionDate(item.dataOriginal);
        if (!transactionDate) {
          return false;
        }
        if (startDate && transactionDate < startDate) {
          return false;
        }
        if (endDate && transactionDate > endDate) {
          return false;
        }
      }

      return true;
    });
  }, [
    endDate,
    invalidAmountRange,
    invalidDateRange,
    parsedMaximum,
    parsedMinimum,
    startDate,
    statusFilter,
  ]);

  const itensEmAberto = useMemo(() => filteredTransactions
    .filter(item => item.status === 'vencida' || item.status === 'proxima')
    .sort((a, b) => (
      (getTransactionDate(a.dataOriginal)?.getTime() ?? 0)
      - (getTransactionDate(b.dataOriginal)?.getTime() ?? 0)
    )), [filteredTransactions]);

  const totalEmAberto = useMemo(() => {
    return itensEmAberto.reduce((acc, curr) => acc + curr.valor, 0);
  }, [itensEmAberto]);

  const proximoVencimentoItem = itensEmAberto.length > 0 ? itensEmAberto[0] : null;

  // Filtra o histórico (realizadas)
  const historicoTransacoes = useMemo(() => {
    return filteredTransactions
      .filter(item => item.status === 'realizada')
      .sort((a, b) => (
        (getTransactionDate(b.dataOriginal)?.getTime() ?? 0)
        - (getTransactionDate(a.dataOriginal)?.getTime() ?? 0)
      ));
  }, [filteredTransactions]);

  const toggleFilterPanel = (panel: Exclude<FilterPanel, null>) => {
    setDatePickerTarget(null);
    setFilterPanel((current) => current === panel ? null : panel);
  };

  const resetFilters = () => {
    setStatusFilter('todos');
    setMinimumAmount('');
    setMaximumAmount('');
    setStartDate(null);
    setEndDate(null);
    setDatePickerTarget(null);
  };

  const handleDateChange = (event: DateTimePickerEvent, selectedDate?: Date) => {
    if (selectedDate && datePickerTarget) {
      const selectedDay = new Date(
        selectedDate.getFullYear(),
        selectedDate.getMonth(),
        selectedDate.getDate(),
      );

      if (datePickerTarget === 'inicio') {
        setStartDate(selectedDay);
        if (endDate && selectedDay > endDate) {
          setEndDate(null);
        }
      } else {
        setEndDate(selectedDay);
        if (startDate && selectedDay < startDate) {
          setStartDate(null);
        }
      }
    }

    if (Platform.OS !== 'ios' || event.type === 'dismissed') {
      setDatePickerTarget(null);
    }
  };

  const getStatusFilterLabel = (filter: StatusFilter) => (
    filter === 'todos' ? 'Todos' : StatusConfig[filter].texto
  );
  const amountFilterLabel = parsedMinimum !== null || parsedMaximum !== null
    ? `${parsedMinimum ?? 0}–${parsedMaximum ?? '∞'}`
    : 'VALOR';
  const dateFilterLabel = startDate || endDate
    ? `${startDate?.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) ?? '...'}–${endDate?.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) ?? '...'}`
    : 'DATA';

  const handlePagarAgora = () => {
    if (proximoVencimentoItem) {
      router.push('/'); 
    }
  };

  // Renderizador de badge baseado no StatusConfig
  const renderBadge = (statusKey: keyof typeof StatusConfig) => {
    const config = StatusConfig[statusKey];
    if (!config) return null;

    return (
      <View style={[styles.badge, { backgroundColor: config.bg }]}>
        <Ionicons name={config.icone} size={12} color={config.cor} style={styles.badgeIcon} />
        <Text style={[styles.badgeText, { color: config.cor }]}>{config.texto}</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#7B0087" />

      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.headerText}>
            <Text style={styles.textPage}>Financeiro</Text>
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
            <Feather name="menu" size={34} color="#FFFFFF" />
          </Pressable>
        </View>
      </LinearGradient>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>

      <LinearGradient
        colors={['#7B0087', '#980070', '#C40E35']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.card}
      >
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Total em aberto:</Text>
          <Text style={styles.cardAmount}>
            {totalEmAberto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </Text>
          <Text style={styles.cardDueDate}>
            {proximoVencimentoItem 
              ? `Próximo do vencimento: ${proximoVencimentoItem.vencimento}` 
              : 'Nenhum vencimento próximo'}
          </Text>

          <Pressable 
            style={[!proximoVencimentoItem && styles.payButtonDisabled]}
            onPress={handlePagarAgora}
            disabled={!proximoVencimentoItem}
          >
            <LinearGradient
            start={{ x: 0.65, y: 0 }}
            end={{ x: 0.35, y: 1 }}
            colors={['rgba(99, 162, 86, 1)', 'rgba(8, 71, 25, 1)']}
            locations={[0.12, 1.0]}
            style={styles.payButton}
            >
            <Ionicons name="card-outline" size={20} color="#ffffff" style={styles.payIcon} />
            <Text style={styles.payButtonText}>Pagar agora</Text>
            </LinearGradient>
          </Pressable>
        </View>
        
      </LinearGradient>

        <View style={styles.filterContainer}>
          <Pressable
            style={[styles.filterButton, filterPanel === 'status' && styles.filterButtonActive]}
            onPress={() => toggleFilterPanel('status')}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar por status: ${getStatusFilterLabel(statusFilter)}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>
              {statusFilter === 'todos' ? 'STATUS' : getStatusFilterLabel(statusFilter)}
            </Text>
            <Feather name="filter" size={14} color="#ffffff" style={styles.filterIcon} />
          </Pressable>

          <Pressable
            style={[styles.filterButton, filterPanel === 'valor' && styles.filterButtonActive]}
            onPress={() => toggleFilterPanel('valor')}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar por valor: mínimo ${parsedMinimum ?? 'sem limite'}, máximo ${parsedMaximum ?? 'sem limite'}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>{amountFilterLabel}</Text>
            <Feather name="filter" size={14} color="#ffffff" style={styles.filterIcon} />
          </Pressable>

          <Pressable
            style={[styles.filterButton, filterPanel === 'data' && styles.filterButtonActive]}
            onPress={() => toggleFilterPanel('data')}
            accessibilityRole="button"
            accessibilityLabel={`Filtrar por vencimento: ${startDate ? formatDateFilter(startDate) : 'sem data inicial'} a ${endDate ? formatDateFilter(endDate) : 'sem data final'}`}
          >
            <Text numberOfLines={1} style={styles.filterText}>{dateFilterLabel}</Text>
            <Feather name="filter" size={14} color="#ffffff" style={styles.filterIcon} />
          </Pressable>
        </View>

        {filterPanel && (
          <View style={styles.filterPanel}>
            {filterPanel === 'status' && (
              <>
                <Text style={styles.filterPanelTitle}>Filtrar por status</Text>
                <View style={styles.statusOptions}>
                  {statusOptions.map((option) => {
                    const selected = statusFilter === option;
                    return (
                      <Pressable
                        key={option}
                        style={[styles.statusOption, selected && styles.statusOptionSelected]}
                        onPress={() => setStatusFilter(option)}
                        accessibilityRole="button"
                        accessibilityState={{ selected }}
                      >
                        <Text style={[styles.statusOptionText, selected && styles.statusOptionTextSelected]}>
                          {getStatusFilterLabel(option)}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </>
            )}

            {filterPanel === 'valor' && (
              <>
                <Text style={styles.filterPanelTitle}>Faixa de valor</Text>
                <View style={styles.rangeInputs}>
                  <View style={styles.rangeInputGroup}>
                    <Text style={styles.rangeInputLabel}>Mínimo (R$)</Text>
                    <TextInput
                      value={minimumAmount}
                      onChangeText={setMinimumAmount}
                      placeholder="0,00"
                      keyboardType="decimal-pad"
                      accessibilityLabel="Valor mínimo"
                      style={styles.rangeInput}
                    />
                  </View>
                  <View style={styles.rangeInputGroup}>
                    <Text style={styles.rangeInputLabel}>Máximo (R$)</Text>
                    <TextInput
                      value={maximumAmount}
                      onChangeText={setMaximumAmount}
                      placeholder="Sem limite"
                      keyboardType="decimal-pad"
                      accessibilityLabel="Valor máximo"
                      style={styles.rangeInput}
                    />
                  </View>
                </View>
                {invalidAmountRange && (
                  <Text style={styles.filterError}>O valor mínimo não pode superar o máximo.</Text>
                )}
              </>
            )}

            {filterPanel === 'data' && (
              <>
                <Text style={styles.filterPanelTitle}>Período de vencimento</Text>
                <View style={styles.rangeInputs}>
                  <Pressable
                    style={styles.dateFilterButton}
                    onPress={() => setDatePickerTarget('inicio')}
                    accessibilityRole="button"
                    accessibilityLabel="Selecionar data inicial"
                  >
                    <View>
                      <Text style={styles.dateFilterLabel}>De</Text>
                      <Text style={startDate ? styles.dateFilterValue : styles.dateFilterPlaceholder}>
                        {startDate ? formatDateFilter(startDate) : 'Data inicial'}
                      </Text>
                    </View>
                    <Feather name="calendar" size={19} color="#84009A" />
                  </Pressable>
                  <Pressable
                    style={styles.dateFilterButton}
                    onPress={() => setDatePickerTarget('fim')}
                    accessibilityRole="button"
                    accessibilityLabel="Selecionar data final"
                  >
                    <View>
                      <Text style={styles.dateFilterLabel}>Até</Text>
                      <Text style={endDate ? styles.dateFilterValue : styles.dateFilterPlaceholder}>
                        {endDate ? formatDateFilter(endDate) : 'Data final'}
                      </Text>
                    </View>
                    <Feather name="calendar" size={19} color="#84009A" />
                  </Pressable>
                </View>
                {invalidDateRange && (
                  <Text style={styles.filterError}>A data inicial não pode ser posterior à final.</Text>
                )}
                {datePickerTarget && (
                  <View style={styles.datePickerContainer}>
                    <DateTimePicker
                      value={
                        (datePickerTarget === 'inicio' ? startDate : endDate)
                        ?? (datePickerTarget === 'fim' ? startDate : endDate)
                        ?? new Date()
                      }
                      mode="date"
                      display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                      minimumDate={datePickerTarget === 'fim' ? startDate ?? undefined : undefined}
                      maximumDate={datePickerTarget === 'inicio' ? endDate ?? undefined : undefined}
                      onChange={handleDateChange}
                    />
                    {Platform.OS === 'ios' && (
                      <Pressable
                        style={styles.datePickerDone}
                        onPress={() => setDatePickerTarget(null)}
                        accessibilityRole="button"
                      >
                        <Text style={styles.datePickerDoneText}>Concluir</Text>
                      </Pressable>
                    )}
                  </View>
                )}
              </>
            )}

            <Pressable
              style={styles.clearFiltersButton}
              onPress={resetFilters}
              accessibilityRole="button"
            >
              <Text style={styles.clearFiltersText}>Limpar filtros</Text>
            </Pressable>
          </View>
        )}

        {/* Seção: Em Aberto */}
        <View style={styles.sectionHeaderContainer}>
          <Text style={styles.sectionTitle}>EM ABERTO</Text>
        </View>

        {itensEmAberto.map((item) => (
          <View key={item.id} style={styles.transactionItem}>
            <View style={styles.transactionInfo}>
              <Text style={styles.transactionName}>{item.nome}</Text>
              <Text style={styles.transactionSubText}>
                {item.status === 'vencida' ? `Vencido em ${item.vencimento}` : `Vence em ${item.vencimento}`}
              </Text>
            </View>
            <View style={styles.transactionRight}>
              {renderBadge(item.status)}
              <Text style={[styles.transactionAmount, { color: StatusConfig[item.status].cor }]}>
                {item.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </Text>
            </View>
          </View>
        ))}
        {itensEmAberto.length === 0 && (
          <Text style={styles.emptyState}>Nenhuma cobrança corresponde aos filtros.</Text>
        )}

        {/* Seção: Histórico */}
        <View style={[styles.sectionHeaderContainer, { marginTop: 24 }]}>
          <Text style={styles.sectionTitle}>HISTÓRICO</Text>
        </View>

        {historicoTransacoes.map((item) => (
          <View key={item.id} style={styles.transactionItem}>
            <View style={styles.transactionInfo}>
              <Text style={styles.transactionName}>{item.nome}</Text>
              <Text style={styles.transactionSubText}>Pago em {item.vencimento}</Text>
            </View>
            <View style={styles.transactionRight}>
              {renderBadge(item.status)}
              <Text style={[styles.transactionAmount, { color: StatusConfig[item.status].cor }]}>
                {item.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </Text>
            </View>
          </View>
        ))}
        {historicoTransacoes.length === 0 && (
          <Text style={styles.emptyState}>Nenhum pagamento corresponde aos filtros.</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
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
  
  menuButton: {
    paddingVertical: 12,
  },
  
  menuButtonPressed: {
    opacity: 0.7,
  },

  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },

  card: {
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginTop: 16,
  },

  cardLabel: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 4,
  },

  cardAmount: {
    color: '#ffffff',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 6,
  },

  cardDueDate: {
    color: '#ffff',
    fontSize: 12,
    marginBottom: 16,
  },

    payButton: {
        width: '100%',
        height: 40,
        borderRadius: 8,
        padding: 10,
        marginTop: 10,
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'row',
        paddingVertical: 10,
        paddingHorizontal: 24,
    },

  payButtonDisabled: {
    backgroundColor: '#cccccc',
  },

  payIcon: {
    marginRight: 6,
  },

  payButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },

  filterContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 20,
  },

  filterButton: {
    backgroundColor: '#c77dff',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 16,
    flex: 1,
    marginHorizontal: 4,
  },

  filterButtonActive: {
    backgroundColor: '#84009A',
  },

  filterText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 10,
  },

  filterIcon: {
    marginLeft: 4,
  },

  filterPanel: {
    padding: 14,
    marginBottom: 20,
    borderRadius: 12,
    backgroundColor: '#F7F1F8',
  },

  filterPanelTitle: {
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

  rangeInputs: {
    flexDirection: 'row',
    gap: 10,
  },

  rangeInputGroup: {
    flex: 1,
  },

  rangeInputLabel: {
    marginBottom: 5,
    color: '#666666',
    fontSize: 12,
  },

  rangeInput: {
    minHeight: 42,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: '#D8C8DC',
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    color: '#222222',
    fontSize: 14,
  },

  dateFilterButton: {
    flex: 1,
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
  },

  dateFilterLabel: {
    marginBottom: 4,
    color: '#8B8790',
    fontSize: 12,
  },

  dateFilterValue: {
    color: '#28232B',
    fontSize: 15,
  },

  dateFilterPlaceholder: {
    color: '#8B8790',
    fontSize: 15,
  },

  filterError: {
    marginTop: 8,
    color: '#B42318',
    fontSize: 12,
  },

  datePickerContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E3DEE6',
    marginTop: 10,
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

  clearFiltersButton: {
    alignSelf: 'flex-end',
    marginTop: 10,
    paddingVertical: 6,
    paddingHorizontal: 8,
  },

  clearFiltersText: {
    color: '#84009A',
    fontSize: 12,
    fontWeight: '700',
  },

  emptyState: {
    paddingVertical: 12,
    color: '#777777',
    fontSize: 13,
  },

  sectionHeaderContainer: {
    marginBottom: 12,
  },

  sectionTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#666666',
    letterSpacing: 0.5,
  },

  transactionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },

  transactionInfo: {
    flex: 1,
  },

  transactionName: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#222222',
    marginBottom: 2,
  },

  transactionSubText: {
    fontSize: 12,
    color: '#888888',
  },

  transactionRight: {
    alignItems: 'flex-end',
  },

  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginBottom: 4,
  },

  badgeIcon: {
    marginRight: 4,
  },

  badgeText: {
    fontSize: 10,
    fontWeight: 'bold',
  },

  transactionAmount: {
    fontSize: 14,
    fontWeight: 'bold',
  },
});