import React from 'react';
import { Box, Typography, Chip, Paper, Grid } from '@mui/material';
import { getSpeakerColor, getAllSpeakerColors } from '../utils/speakerColors';

const SpeakerColorDemo: React.FC = () => {
  const allColors = getAllSpeakerColors();

  return (
    <Paper sx={{ p: 3, borderRadius: 3 }}>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Speaker Color Palette
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Each speaker is automatically assigned a unique color for easy identification in transcriptions.
      </Typography>
      
      <Grid container spacing={2}>
        {Object.entries(allColors).map(([speaker, colors]) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={speaker}>
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                backgroundColor: colors.backgroundColor,
                border: '1px solid',
                borderColor: colors.borderColor,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Chip
                label={speaker}
                size="small"
                variant="outlined"
                sx={{
                  color: colors.color,
                  backgroundColor: colors.backgroundColor,
                  borderColor: colors.borderColor,
                  fontWeight: 600,
                  '&:hover': {
                    backgroundColor: colors.backgroundColor,
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
                Sample transcription text for {speaker}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>
      
      <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Note:</strong> Colors are automatically assigned based on speaker names. 
          Unknown speakers will use a default gray color scheme.
        </Typography>
      </Box>
    </Paper>
  );
};

export default SpeakerColorDemo; 