export interface SpeakerColorScheme {
  color: string;
  backgroundColor: string;
  borderColor: string;
}

/**
 * Get consistent color scheme for each speaker
 * Uses a muted, professional color palette that adapts to theme mode
 */
export const getSpeakerColor = (speaker: string, isDarkMode: boolean = false): SpeakerColorScheme => {
  const lightModeColors: Record<string, SpeakerColorScheme> = {
    'Speaker_1': {
      color: '#4f46e5', // Indigo
      backgroundColor: 'rgba(79, 70, 229, 0.08)',
      borderColor: 'rgba(79, 70, 229, 0.3)'
    },
    'Speaker_2': {
      color: '#059669', // Emerald
      backgroundColor: 'rgba(5, 150, 105, 0.08)',
      borderColor: 'rgba(5, 150, 105, 0.3)'
    },
    'Speaker_3': {
      color: '#dc2626', // Red
      backgroundColor: 'rgba(220, 38, 38, 0.08)',
      borderColor: 'rgba(220, 38, 38, 0.3)'
    },
    'Speaker_4': {
      color: '#7c2d12', // Orange/Brown
      backgroundColor: 'rgba(124, 45, 18, 0.08)',
      borderColor: 'rgba(124, 45, 18, 0.3)'
    },
    'Speaker_5': {
      color: '#7c3aed', // Violet
      backgroundColor: 'rgba(124, 58, 237, 0.08)',
      borderColor: 'rgba(124, 58, 237, 0.3)'
    },
    'Speaker_6': {
      color: '#0891b2', // Cyan
      backgroundColor: 'rgba(8, 145, 178, 0.08)',
      borderColor: 'rgba(8, 145, 178, 0.3)'
    },
    'Speaker_7': {
      color: '#be185d', // Pink
      backgroundColor: 'rgba(190, 24, 93, 0.08)',
      borderColor: 'rgba(190, 24, 93, 0.3)'
    },
    'Speaker_8': {
      color: '#0369a1', // Blue
      backgroundColor: 'rgba(3, 105, 161, 0.08)',
      borderColor: 'rgba(3, 105, 161, 0.3)'
    },
    'Speaker_9': {
      color: '#65a30d', // Lime
      backgroundColor: 'rgba(101, 163, 13, 0.08)',
      borderColor: 'rgba(101, 163, 13, 0.3)'
    },
    'Speaker_10': {
      color: '#a21caf', // Fuchsia
      backgroundColor: 'rgba(162, 28, 175, 0.08)',
      borderColor: 'rgba(162, 28, 175, 0.3)'
    }
  };

  const darkModeColors: Record<string, SpeakerColorScheme> = {
    'Speaker_1': {
      color: '#8b5cf6', // Brighter violet for dark mode
      backgroundColor: 'rgba(139, 92, 246, 0.15)',
      borderColor: 'rgba(139, 92, 246, 0.4)'
    },
    'Speaker_2': {
      color: '#10b981', // Brighter emerald
      backgroundColor: 'rgba(16, 185, 129, 0.15)',
      borderColor: 'rgba(16, 185, 129, 0.4)'
    },
    'Speaker_3': {
      color: '#f87171', // Lighter red for better contrast
      backgroundColor: 'rgba(248, 113, 113, 0.15)',
      borderColor: 'rgba(248, 113, 113, 0.4)'
    },
    'Speaker_4': {
      color: '#fb923c', // Brighter orange
      backgroundColor: 'rgba(251, 146, 60, 0.15)',
      borderColor: 'rgba(251, 146, 60, 0.4)'
    },
    'Speaker_5': {
      color: '#a78bfa', // Lighter violet
      backgroundColor: 'rgba(167, 139, 250, 0.15)',
      borderColor: 'rgba(167, 139, 250, 0.4)'
    },
    'Speaker_6': {
      color: '#22d3ee', // Brighter cyan
      backgroundColor: 'rgba(34, 211, 238, 0.15)',
      borderColor: 'rgba(34, 211, 238, 0.4)'
    },
    'Speaker_7': {
      color: '#f472b6', // Lighter pink
      backgroundColor: 'rgba(244, 114, 182, 0.15)',
      borderColor: 'rgba(244, 114, 182, 0.4)'
    },
    'Speaker_8': {
      color: '#60a5fa', // Lighter blue
      backgroundColor: 'rgba(96, 165, 250, 0.15)',
      borderColor: 'rgba(96, 165, 250, 0.4)'
    },
    'Speaker_9': {
      color: '#84cc16', // Brighter lime
      backgroundColor: 'rgba(132, 204, 22, 0.15)',
      borderColor: 'rgba(132, 204, 22, 0.4)'
    },
    'Speaker_10': {
      color: '#e879f9', // Brighter fuchsia
      backgroundColor: 'rgba(232, 121, 249, 0.15)',
      borderColor: 'rgba(232, 121, 249, 0.4)'
    }
  };

  // Default colors for unknown speakers
  const defaultLightColor: SpeakerColorScheme = {
    color: '#6b7280', // Gray
    backgroundColor: 'rgba(107, 114, 128, 0.08)',
    borderColor: 'rgba(107, 114, 128, 0.3)'
  };

  const defaultDarkColor: SpeakerColorScheme = {
    color: '#9ca3af', // Lighter gray for dark mode
    backgroundColor: 'rgba(156, 163, 175, 0.15)',
    borderColor: 'rgba(156, 163, 175, 0.4)'
  };

  const speakerColors = isDarkMode ? darkModeColors : lightModeColors;
  const defaultColor = isDarkMode ? defaultDarkColor : defaultLightColor;

  return speakerColors[speaker] || defaultColor;
};

/**
 * Get all available speaker colors for a specific theme mode
 */
export const getAllSpeakerColors = (isDarkMode: boolean = false): Record<string, SpeakerColorScheme> => {
  const colors: Record<string, SpeakerColorScheme> = {};
  for (let i = 1; i <= 10; i++) {
    const speaker = `Speaker_${i}`;
    colors[speaker] = getSpeakerColor(speaker, isDarkMode);
  }
  return colors;
}; 