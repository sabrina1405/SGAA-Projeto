import { StyleSheet } from "react-native";

export const activityModalStyles = StyleSheet.create({
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