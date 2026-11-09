import { StyleSheet } from 'react-native';
import { paleta } from '@/components/theme/colors';

export const styles = StyleSheet.create({
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
        maxWidth: 220,
        height: 50,
        borderRadius: 8,
        marginTop: 12,
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'row',
        paddingVertical: 15,
        paddingHorizontal: 30,
    },

  copyPixButton: {
    height: 100,
    padding: 0,
    overflow: 'hidden',
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
    textAlign: 'center',
  },

  filterContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 20,
  },

  filterButton: {
    backgroundColor: paleta.purple04,
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
    backgroundColor: paleta.purple02,
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

  rodape: { 
    marginTop: 32, 
    paddingHorizontal: 20, 
    alignItems: 'center' 
  },

  rodapeText: { 
    textAlign: 'center', 
    color: '#777777', 
    fontSize: 13, 
    lineHeight: 18 
  },
});