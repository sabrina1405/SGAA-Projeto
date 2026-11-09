import { StyleSheet } from "react-native";

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 14,
  },

  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
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
  
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },

  uploadContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },

  avatarWrapper: {
    position: 'relative',
    width: 100,
    height: 100,
    borderRadius: 50,
    marginBottom: 8,
  },

  avatarImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },

  avatarPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#C481D0',
    justifyContent: 'center',
    alignItems: 'center',
  },

  cameraIconBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#7B0087',
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },

  profileNameText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
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
  
  formGroup: {
    marginBottom: 16,
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

  inputWithIcon: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
  },
  dateInput: {
    flex: 1,
    minHeight: 46,
    paddingVertical: 10,
    color: '#28232B',
    fontSize: 15,
  },
  calendarIcon: {
    marginRight: 2,
  },
  selectBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 48,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E3DEE6',
    borderRadius: 12,
    paddingHorizontal: 14,
  },
  selectText: {
    fontSize: 15,
    color: '#28232B',
  },
  actionButtonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    gap: 12,
  },
  button: {
    flex: 1,
    minHeight: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButton: {
    backgroundColor: '#C40E35',
    borderWidth: 1,
    borderColor: '#C40E35',
  },
  saveButton: {
    overflow: 'hidden',
    backgroundColor: '#1B8D33',
  },
  cancelButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },

  saveGradient: {
    ...StyleSheet.absoluteFill,
    borderRadius: 8,
  },

  saveButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 16,
  },
});