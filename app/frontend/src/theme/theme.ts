import { createTheme } from '@mui/material/styles';

// Cyberpunk color palette
const cyberpunkColors = {
  primary: {
    main: '#00ffff', // Cyan
    dark: '#00cccc',
    light: '#66ffff',
    contrastText: '#000000'
  },
  secondary: {
    main: '#ff0080', // Hot Pink
    dark: '#cc0066',
    light: '#ff66b3',
    contrastText: '#ffffff'
  },
  background: {
    default: '#050714', // Dark blue
    paper: '#0a0b1a', // Slightly lighter dark blue
  },
  text: {
    primary: '#ffffff',
    secondary: '#cccccc',
  },
  error: {
    main: '#ff4444',
  },
  warning: {
    main: '#ffaa00',
  },
  success: {
    main: '#00ff88',
  },
  info: {
    main: '#00ffff',
  }
};

export const cyberpunkTheme = createTheme({
  palette: {
    mode: 'dark',
    ...cyberpunkColors,
    divider: 'rgba(0, 255, 255, 0.2)',
  },
  typography: {
    fontFamily: '"Orbitron", "Roboto", "Arial", sans-serif',
    h1: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 700,
      fontSize: '2.5rem',
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
    },
    h2: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 600,
      fontSize: '2rem',
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
    },
    h3: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 600,
      fontSize: '1.5rem',
      letterSpacing: '0.06em',
    },
    h4: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 500,
      fontSize: '1.25rem',
      letterSpacing: '0.05em',
    },
    h5: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 500,
      fontSize: '1.1rem',
      letterSpacing: '0.04em',
    },
    h6: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 500,
      fontSize: '1rem',
      letterSpacing: '0.03em',
    },
    button: {
      fontFamily: '"Orbitron", sans-serif',
      fontWeight: 600,
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          padding: '12px 24px',
          border: '1px solid',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 4px 20px rgba(0, 255, 255, 0.3)',
          },
        },
        contained: {
          background: 'linear-gradient(135deg, #00ffff 0%, #0099cc 100%)',
          border: '1px solid #00ffff',
          '&:hover': {
            background: 'linear-gradient(135deg, #66ffff 0%, #00cccc 100%)',
          },
        },
        outlined: {
          borderColor: '#00ffff',
          color: '#00ffff',
          '&:hover': {
            borderColor: '#66ffff',
            backgroundColor: 'rgba(0, 255, 255, 0.1)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(10, 11, 26, 0.8)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(0, 255, 255, 0.3)',
          borderRadius: '12px',
          '&:hover': {
            border: '1px solid rgba(0, 255, 255, 0.5)',
            boxShadow: '0 8px 32px rgba(0, 255, 255, 0.2)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
            '& fieldset': {
              borderColor: 'rgba(0, 255, 255, 0.3)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(0, 255, 255, 0.5)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00ffff',
            },
          },
          '& .MuiInputLabel-root': {
            color: '#cccccc',
            '&.Mui-focused': {
              color: '#00ffff',
            },
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: 'rgba(5, 7, 20, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRight: '1px solid rgba(0, 255, 255, 0.3)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(5, 7, 20, 0.95)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(0, 255, 255, 0.3)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(255, 0, 128, 0.2)',
          border: '1px solid rgba(255, 0, 128, 0.5)',
          color: '#ffffff',
          '&:hover': {
            backgroundColor: 'rgba(255, 0, 128, 0.3)',
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          color: '#cccccc',
          '&.Mui-selected': {
            color: '#00ffff',
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          backgroundColor: '#00ffff',
        },
      },
    },
  },
});

export default cyberpunkTheme;
