import { StyleSheet } from "react-native";

export const styles = StyleSheet.create({
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
    alignSelf: 'center',
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
    alignSelf: 'center',
  },
  
  subtitle: {
    color: '#706A75',
    fontSize: 14,
    lineHeight: 20,
    marginTop: 6,
    alignSelf: 'center',
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

  submitButtonDisabled: {
    opacity: 0.55,
  },

  submitText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },

  secondaryButton: {
    minHeight: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: '#C9BCCC',
    borderRadius: 12,
    backgroundColor: '#F3EAF5',
    marginBottom: 16,
  },

  secondaryButtonText: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: '700',
  },

  tokenHint: {
    color: '#706A75',
    fontSize: 12,
    lineHeight: 18,
    marginTop: -2,
    marginBottom: 8,
  },

  codeMessage: {
    color: '#514A55',
    fontSize: 13,
    lineHeight: 19,
    marginTop: -8,
    marginBottom: 16,
  },

  codeMessageError: {
    color: '#B42318',
  },

  passwordStrength: {
    marginTop: 4,
    marginBottom: 16,
  },

  strengthLabel: {
    color: '#514A55',
    fontSize: 12,
    marginBottom: 6,
  },
  
  progressBar: {
    height: 6,
    backgroundColor: '#E8E4EA',
    borderRadius: 10,
    overflow: 'hidden',
  },

  progressFill: {
    height: '100%',
    borderRadius: 10,
  },

  rules: {
    marginTop: 10,
  },

  ruleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 3,
  },

  rule: {
    color: '#706A75',
    fontSize: 12,
    lineHeight: 16,
  },

  ruleValid: {
    color: '#228B45',
  },
  
  ruleInvalid: {
    color: '#B42318',
  },
});
