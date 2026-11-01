import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  container: {
    flex: 1,
  },

card: {
  flex: 1,
  alignItems: 'center',
  justifyContent: 'center'
},

logo: {
  width: 80,
  height: 80,
  backgroundColor: '#D9D9D9',
  marginBottom: 10,
},

title: {
  color: '#fff',
  fontSize: 25,
  fontWeight: 400,
  fontFamily: 'sans-serif'
},

subtitle: {
  color: '#fff',
  fontSize: 14,
  marginTop: 6,
  fontFamily: 'sans-serif',
  fontWeight: 300,
  marginBottom: 28,
},

studentButton: {
  width: '82%',
  height: 40,
  backgroundColor: '#8A007A',
  borderRadius: 6,
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: 20,

  shadowColor: '#000',
  shadowOffset: {
    width: 0,
    height: 3,
  },
  shadowOpacity: 0.4,
  shadowRadius: 4,
  elevation: 6,
},

studentButtonText: {
  color: '#fff',
  fontWeight: '700',
  fontSize: 18,
},

firstAccess: {
  color: '#ffff',
  marginTop: 14,
  marginBottom: 18,
  fontSize: 12,
  fontWeight: 400,
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

recoverContainer:{
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

loginButton: {
  width: 100,
  height: 20,
  borderRadius: 8,
  padding: 10,
  backgroundColor: '#1B8D33',
  alignItems: 'center',
  justifyContent: 'center',
},

loginText: {
  color: '#fff',
  fontSize: 9,
},
  
label: {
  width: '82%',
  color: '#fff',
  fontSize: 14,
  fontWeight: 100,
  fontFamily: 'sans-serif',
  marginBottom: 8,
},

reenviarContainer: {
  width: '80%',
  alignItems: 'flex-end',
  marginTop: -10,
  marginBottom: 10,
},

reenviar: {
  color: '#fff',
  fontSize: 12,
  fontFamily: 'sans-serif',
  fontWeight: 100,
},

progressBar: {
  width: '58%',
  height: 5,
  backgroundColor: '#C0C0C0',
  borderRadius: 10,
  overflow: 'hidden',
  marginTop: 18,
},

progressFill: {
  width: '45%',
  height: '100%',
  backgroundColor: '#FF0000',
  borderRadius: 10,
},

rules: {
  width: '58%',
  marginTop: 10,
  alignSelf: 'center',
},

rule: {
  color: '#FFFFFF',
  fontSize: 11,
  lineHeight: 15,
},

inputContainer: {
  width: '82%',
  height: 40,
  backgroundColor: '#F2F2F2',
  borderRadius: 14,
  flexDirection: 'row',
  alignItems: 'center',
  paddingHorizontal: 18,
  marginBottom: 20,

  shadowColor: '#000',
  shadowOffset: {
    width: 0,
    height: 3,
  },
  shadowOpacity: 0.35,
  shadowRadius: 4,
  elevation: 5,
},

});