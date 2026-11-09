import { StyleSheet } from "react-native";
import { paleta } from "@/components/theme/colors";


export const styles = StyleSheet.create({
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