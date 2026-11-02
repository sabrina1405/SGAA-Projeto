import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  root: {
    flex: 1,
  },

  safeArea: {
    flex: 1,
    backgroundColor: '#800080',
  },

  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
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

  logo: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '400',
    marginBottom: 8,
  },

  welcome: {
    color: '#FFFFFF',
    fontSize: 14,
    lineHeight: 18,
    fontWeight: '400',
  },

  studentName: {
    color: '#FFFFFF',
    fontSize: 16,
    lineHeight: 21,
    fontWeight: '700',
  },

  menuButton: {
    width: 48,
    height: 48,
    marginTop: -2,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 24,
  },

  menuButtonPressed: {
    backgroundColor: 'rgba(255,255,255,0.14)',
  },

  scroll: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },

  scrollContent: {
    paddingTop: 31,
    paddingBottom: 42,
  },

  section: {
    paddingHorizontal: 10,
  },

  sectionTitle: {
    color: '#626262',
    fontSize: 16,
    lineHeight: 21,
    fontWeight: '400',
    marginLeft: 15,
    marginBottom: 3,
  },

  separator: {
    height: 1,
    backgroundColor: '#BDBDBD',
    marginHorizontal: 6,
    marginTop: 35,
    marginBottom: 29,
  },

  listContainer: {
        padding: 16,
        gap: 12,
    },

  modalOverlay: {
    ...StyleSheet.absoluteFill,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.18)',
  },

  modalContent: {
    width: '100%',
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },

  detailCard: {
    width: '100%',
    maxWidth: 440,
    padding: 24,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    elevation: 8,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 18,
  },

  detailHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },

  detailHeading: {
    flex: 1,
  },

  detailEyebrow: {
    marginBottom: 6,
    color: '#84009A',
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
  },

  detailTitle: {
    color: '#292929',
    fontSize: 20,
    lineHeight: 26,
    fontWeight: '700',
  },

  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F3F0F4',
    alignItems: 'center',
    justifyContent: 'center',
  },

  detailDivider: {
    height: 1,
    marginVertical: 18,
    backgroundColor: '#E8E4E9',
  },

  detailStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },

  statusDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
  },

  detailStatusText: {
    color: '#555',
    fontSize: 14,
    fontWeight: '600',
  },

  detailInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 12,
  },

  detailInfoText: {
    flex: 1,
    color: '#444',
    fontSize: 15,
    lineHeight: 21,
  },

  descriptionLabel: {
    marginTop: 10,
    marginBottom: 6,
    color: '#292929',
    fontSize: 15,
    fontWeight: '700',
  },

  descriptionText: {
    color: '#626262',
    fontSize: 15,
    lineHeight: 22,
  },
});

export default styles;