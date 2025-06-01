import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';
import AudioVisualizer from './AudioVisualizer';

const theme = createTheme();

describe('AudioVisualizer', () => {
    it('renders without crashing', () => {
        render(
            <ThemeProvider theme={theme}>
                <AudioVisualizer
                    isActive={false}
                    audioLevel={0}
                />
            </ThemeProvider>
        );
    });

    it('renders with active state', () => {
        render(
            <ThemeProvider theme={theme}>
                <AudioVisualizer
                    isActive={true}
                    audioLevel={50}
                    barCount={20}
                    height={60}
                    width={200}
                    color="#ff0000"
                />
            </ThemeProvider>
        );
    });

    it('renders correct number of bars', () => {
        const { container } = render(
            <ThemeProvider theme={theme}>
                <AudioVisualizer
                    isActive={false}
                    audioLevel={0}
                    barCount={10}
                />
            </ThemeProvider>
        );
        
        // Check that the correct number of bars are rendered
        const bars = container.querySelectorAll('[data-testid="sound-bar"]');
        expect(bars).toHaveLength(10);
    });
}); 