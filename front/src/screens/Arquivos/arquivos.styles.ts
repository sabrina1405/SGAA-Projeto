import { paleta } from '@/components/theme/colors';
import { StyleSheet } from 'react-native';

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
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  
  headerText: {
    flex: 1,
    alignItems: 'center',
  },
  
  textPage: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: 'bold',
    paddingVertical: 14,
  },

  headerAction: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 22,
  },

  headerActionPlaceholder: {
    width: 44,
    height: 44,
  },
  
  menuButtonPressed: {
    opacity: 0.7,
  },

  content: {
    flexGrow: 1,
    paddingHorizontal: 18,
    paddingTop: 24,
    paddingBottom: 36,
    gap: 14,
  },

  filterContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },

  filterButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 38,
    paddingVertical: 8,
    paddingHorizontal: 6,
    marginHorizontal: 3,
    borderRadius: 16,
    backgroundColor: paleta.purple04,
  },

  filterButtonActive: {
    backgroundColor: paleta.purple03,
  },

  filterText: {
    flexShrink: 1,
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },

  filterIcon: {
    marginLeft: 4,
  },

  filterPanel: {
    padding: 14,
    marginBottom: 4,
    borderRadius: 12,
    backgroundColor: '#F7F1F8',
  },

  filterPanelTitle: {
    marginBottom: 10,
    color: '#333333',
    fontSize: 14,
    fontWeight: '700',
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
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
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

  datePickerContainer: {
    marginTop: 10,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
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

  filterError: {
    marginTop: 8,
    color: '#B42318',
    fontSize: 12,
  },

  emptyState: {
    paddingVertical: 12,
    color: '#777777',
    fontSize: 13,
  },

  sectionHeader: {
    gap: 12,
    marginBottom: 2,
  },

  sectionTitle: {
    color: '#302A32',
    fontSize: 18,
    fontWeight: '700',
  },

  demoNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
    marginTop: 8,
    padding: 12,
    backgroundColor: '#F6F2F7',
    borderRadius: 12,
  },

  demoNoticeText: {
    flex: 1,
    color: '#6C5B73',
    fontSize: 12,
    lineHeight: 18,
  },
});