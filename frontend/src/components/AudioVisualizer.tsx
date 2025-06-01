import React, { useEffect, useState } from 'react';
import { Box, styled } from '@mui/material';

interface AudioVisualizerProps {
    isActive: boolean;
    audioLevel: number; // 0-100 representing the audio level
    barCount?: number;
    height?: number;
    width?: number;
    color?: string;
    backgroundColor?: string;
}

const VisualizerContainer = styled(Box)(({ theme }) => ({
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'center',
    gap: theme.spacing(0.5),
    padding: theme.spacing(1),
    borderRadius: theme.spacing(1),
    background: 'rgba(0, 0, 0, 0.05)',
    border: '1px solid rgba(0, 0, 0, 0.1)',
}));

const SoundBar = styled(Box, {
    shouldForwardProp: (prop) => !['barHeight', 'isActive', 'delay', 'barColor'].includes(prop as string),
})<{
    barHeight: number;
    isActive: boolean;
    delay: number;
    barColor: string;
}>(({ theme, barHeight, isActive, delay, barColor }) => ({
    width: 4,
    minHeight: 4,
    height: `${barHeight}px`,
    backgroundColor: isActive ? barColor : theme.palette.grey[300],
    borderRadius: 2,
    transition: 'height 0.1s ease-out, background-color 0.2s ease-out',
    transformOrigin: 'bottom',
}));

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
    isActive,
    audioLevel,
    barCount = 20,
    height = 60,
    width = 200,
    color = '#6366f1',
    backgroundColor = 'transparent',
}) => {
    const [barHeights, setBarHeights] = useState<number[]>(new Array(barCount).fill(4));

    useEffect(() => {
        if (isActive && audioLevel > 0) {
            // Calculate base height from actual audio level
            const baseHeight = Math.max(4, (audioLevel / 100) * height);
            
            // Create a frequency-like distribution across bars
            // Center bars show more activity, outer bars show less
            setBarHeights(prev => Array.from({ length: barCount }, (_, index) => {
                const centerIndex = barCount / 2;
                const distanceFromCenter = Math.abs(index - centerIndex);
                const maxDistance = centerIndex;
                
                // Create a bell curve-like distribution
                const normalizedDistance = distanceFromCenter / maxDistance;
                const frequencyMultiplier = Math.exp(-normalizedDistance * 2); // Exponential decay from center
                
                // Add some randomness to make it look more natural
                const randomVariation = 0.7 + Math.random() * 0.6; // 0.7 to 1.3 multiplier
                
                // Calculate final height
                const targetHeight = baseHeight * frequencyMultiplier * randomVariation;
                
                // Smooth transition from current height
                const currentHeight = prev[index];
                const smoothingFactor = 0.4; // Adjust for responsiveness vs smoothness
                const smoothedHeight = currentHeight + (targetHeight - currentHeight) * smoothingFactor;
                
                return Math.max(4, Math.min(height, smoothedHeight));
            }));
        } else if (!isActive) {
            // Gradually reduce all bars to minimum height when not active
            setBarHeights(prev => prev.map(currentHeight => {
                const targetHeight = 4;
                const smoothedHeight = currentHeight + (targetHeight - currentHeight) * 0.1;
                return Math.max(4, smoothedHeight);
            }));
        } else {
            // When active but no audio level, show minimal activity
            setBarHeights(prev => prev.map(() => 4 + Math.random() * 2));
        }
    }, [isActive, audioLevel, height, barCount]);

    return (
        <VisualizerContainer
            sx={{
                width: width,
                height: height + 16,
                backgroundColor: backgroundColor,
            }}
        >
            {Array.from({ length: barCount }, (_, index) => (
                <SoundBar
                    key={index}
                    data-testid="sound-bar"
                    barHeight={barHeights[index] || 4}
                    isActive={isActive}
                    delay={index * 0.05}
                    barColor={color}
                />
            ))}
        </VisualizerContainer>
    );
};

export default AudioVisualizer; 