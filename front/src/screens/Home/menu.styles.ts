import { StyleSheet } from "react-native";

export const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
    },

    backdrop: {
        ...StyleSheet.absoluteFill,
    },

    drawer: {
        flex: 1,
        width: '75%',
        maxWidth: 360,
    },

    container: {
        flex: 1,
        paddingTop: 16,
    },

    menuHeader: {
        minHeight: 64,
        paddingHorizontal: 20,
        flexDirection: 'row',
        alignItems: 'center',
        alignSelf: 'flex-end',
        gap: 85
    },

    logo: {
        width: 64,
        height: 64,
        alignSelf: 'center',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#F3EAF5',
        borderRadius: 18,
    },

    logoText: {
        color: '#84009A',
        fontSize: 17,
        fontWeight: '800',
    },
    
    text: {
        fontSize: 14,
        fontWeight: '400',
        color: '#fff',
        fontFamily: 'sans-serif',
    },
    
    menuItem: {
        minHeight: 56,
        width: '70%',
        alignSelf: 'center',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 20,
        margin: 10,
        paddingHorizontal: 16,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.2)',
    },
    
    menuItemHighlight: {
        transitionDuration: '0.2s',
        backgroundColor: 'rgba(226, 219, 219, 0.48)',
    },

    separator: {
        width: '90%',
        height: 1,
        backgroundColor: '#D6D6D6',
        alignSelf: 'center',
        marginVertical: 8,
    },

});