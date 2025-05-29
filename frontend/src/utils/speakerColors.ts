export interface SpeakerColorScheme {
  color: string;
  backgroundColor: string;
  borderColor: string;
}

/**
 * Get consistent color scheme for each speaker
 * Uses a muted, professional color palette that fits the site design
 */
export const getSpeakerColor = (speaker: string): SpeakerColorScheme => {
  const speakerColors: Record<string, SpeakerColorScheme> = {
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

  // Default color for unknown speakers
  const defaultColor: SpeakerColorScheme = {
    color: '#6b7280', // Gray
    backgroundColor: 'rgba(107, 114, 128, 0.08)',
    borderColor: 'rgba(107, 114, 128, 0.3)'
  };

  return speakerColors[speaker] || defaultColor;
};

/**
 * Get all available speaker colors
 */
export const getAllSpeakerColors = (): Record<string, SpeakerColorScheme> => {
  const colors: Record<string, SpeakerColorScheme> = {};
  for (let i = 1; i <= 10; i++) {
    const speaker = `Speaker_${i}`;
    colors[speaker] = getSpeakerColor(speaker);
  }
  return colors;
}; 