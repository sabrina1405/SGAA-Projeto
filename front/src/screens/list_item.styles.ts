import { StyleSheet } from 'react-native';

export const fileStyles = StyleSheet.create({
  folder: {
    minHeight: 64,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  iconFolder: {
    width: 42,
    height: 42,
    borderRadius: 8,
    backgroundColor: '#FFF4D6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  fileInfo: { flex: 1, marginHorizontal: 12 },
  fileTitle: { color: '#292929', fontSize: 15, fontWeight: '700' },
  fileDetails: { color: '#626262', fontSize: 12, marginTop: 3 },
  document: {
    minHeight: 64,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
  },
  documentMain: { flex: 1, flexDirection: 'row', alignItems: 'center', padding: 12 },
  iconDocument: {
    width: 42,
    height: 42,
    borderRadius: 8,
    backgroundColor: '#FCE8EC',
    alignItems: 'center',
    justifyContent: 'center',
  },
  downloadButton: {
    width: 48,
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: { opacity: 0.65 },
  disabled: { opacity: 0.45 },
});
