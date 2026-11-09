import { StyleSheet } from "react-native";

export const styles = StyleSheet.create({
  container: {
    flex: 1,
  },

  card: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  logo: {
    width: 64,
    height: 64,
    alignSelf: 'center',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3EAF5',
    borderRadius: 18,
    marginBottom: 18,
  },

  logoText: {
    color: '#84009A',
    fontSize: 17,
    fontWeight: '800',
    alignSelf: 'center',
  },

  subtitle: {
    color: '#fff',
    fontSize: 14,
    paddingVertical: 20,
    fontFamily: 'sans-serif',
    fontWeight: '300',
  },


  roleButtonsContainer: {
    width: '82%',
    flexDirection: 'row',
    gap: 10,
  },

  roleButton: {
    flex: 1,
    minHeight: 76,
    paddingVertical: 8,
    paddingHorizontal: 6,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
  },

  roleButtonSelected: {
    backgroundColor: 'rgba(132, 0, 154, 0.35)',
    borderColor: 'rgba(255, 255, 255, 0.65)',
  },
  
  roleButtonUnselected: {
    backgroundColor: '#F3EAF5',
    borderColor: '#FFFFFF',
  },

  roleButtonTitle: {
    color: '#84009A',
    fontSize: 14,
    fontWeight: '700',
  },

  roleButtonTitleSelected: {
    color: '#FFF',
  },

  roleButtonSubtitle: {
    color: '#84009A',
    fontSize: 10,
    textAlign: 'center',
  },

  roleButtonSubtitleSelected: {
    color: '#ffff',
  },


  firstAccessContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    marginBottom: 16,
    paddingVertical: 4,
  },

  firstAccessText: {
    color: '#FFFFFF',
    fontSize: 12,
  },

  firstAccessLink: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },

  inputContainer: {
    width: '82%',
    height: 40,
    backgroundColor: '#F2F2F2',
    borderRadius: 14,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 18,
    marginBottom: 16,

    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 3,
    },
    shadowOpacity: 0.35,
    shadowRadius: 4,
    elevation: 5,
  },

  input: {
    flex: 1,
    marginLeft: 14,
    color: '#222',
    fontWeight: '600',
  },

  separator: {
    width: 1,
    height: 20,
    backgroundColor: '#D6D6D6',
    marginRight: 12,
  },

  recoverContainer: {
    display: 'flex',
    width: '80%',
    alignItems: 'flex-end',
    justifyContent: 'flex-end',
  },

  recover: {
    color: '#E8DCE8',
    marginBottom: 16,
    alignSelf: 'flex-end',
    fontSize: 12,
  },

  studentButton: {
    width: '82%',
    minHeight: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(243, 234, 245, 0.2)',
  },

  studentButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },

  label: {
    width: '82%',
    marginBottom: 8,
    color: '#FFFFFF',
    fontSize: 12,
    alignSelf: 'center',
  },

  reenviarContainer: {
    width: '82%',
    alignItems: 'flex-end',
    marginBottom: 16,
  },

  reenviar: {
    color: '#FFFFFF',
    fontSize: 12,
    textDecorationLine: 'underline',
  },

  passwordStrength: {
    width: '82%',
    marginTop: 4,
  },

  strengthLabel: {
    color: '#FFFFFF',
    fontSize: 12,
    marginBottom: 6,
  },

  progressBar: {
    height: 6,
    overflow: 'hidden',
    borderRadius: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
  },

  progressFill: {
    height: '100%',
    borderRadius: 10,
  },

  rules: {
    width: '82%',
    marginTop: 10,
    marginBottom: 16,
  },

  ruleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 3,
  },

  rule: {
    color: '#FFFFFF',
    fontSize: 12,
    lineHeight: 16,
  },

  ruleValid: {
    color: '#35C46A',
  },

  ruleInvalid: {
    color: '#FF7777',
  },

  loginButton: {
    width: 100,
    height: 40,
    borderRadius: 8,
    padding: 10,
    backgroundColor: '#1B8D33',
    alignItems: 'center',
    justifyContent: 'center',
  },

  loginText: {
    color: '#fff',
    fontSize: 12,
  },
});
