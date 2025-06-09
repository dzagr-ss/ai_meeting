import React from 'react';
import {
  Box,
  Typography,
  Button,
  Container,
  Grid,
  Card,
  CardContent,
  Fade,
  Chip,
  useTheme,
  alpha,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Mic,
  AudioFile,
  RecordVoiceOver,
  Summarize,
  EventNote,
  ChecklistRtl,
  Speed,
  Security,
  CloudUpload,
  PlayArrow,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const HeroSection = styled(Box)(({ theme }) => ({
  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
  color: 'white',
  padding: theme.spacing(12, 0, 8, 0),
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'radial-gradient(circle at 30% 20%, rgba(255,255,255,0.1) 0%, transparent 50%)',
  },
}));

const FeatureCard = styled(Card)(({ theme }) => ({
  height: '100%',
  background: alpha(theme.palette.background.paper, 0.8),
  backdropFilter: 'blur(10px)',
  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
  borderRadius: 16,
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-8px)',
    boxShadow: `0 20px 40px ${alpha(theme.palette.primary.main, 0.1)}`,
    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
  },
}));

const StatsBox = styled(Box)(({ theme }) => ({
  background: alpha(theme.palette.background.paper, 0.9),
  borderRadius: 16,
  padding: theme.spacing(3),
  textAlign: 'center',
  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
}));

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const features = [
    {
      icon: <Mic sx={{ fontSize: 48, color: theme.palette.primary.main }} />,
      title: 'Real-Time Recording',
      description: 'High-quality audio recording with live transcription and audio visualization. Start capturing your meetings instantly.',
      color: theme.palette.primary.main,
    },
    {
      icon: <AudioFile sx={{ fontSize: 48, color: theme.palette.secondary.main }} />,
      title: 'Audio File Upload',
      description: 'Upload existing audio files for processing. Supports multiple formats with automatic transcription.',
      color: theme.palette.secondary.main,
    },
    {
      icon: <RecordVoiceOver sx={{ fontSize: 48, color: theme.palette.success.main }} />,
      title: 'Speaker Diarization',
      description: 'Automatically identify and separate different speakers in your meetings with advanced AI technology.',
      color: theme.palette.success.main,
    },
    {
      icon: <Summarize sx={{ fontSize: 48, color: theme.palette.info.main }} />,
      title: 'AI Summarization',
      description: 'Generate comprehensive meeting summaries automatically, highlighting key points and decisions.',
      color: theme.palette.info.main,
    },
    {
      icon: <EventNote sx={{ fontSize: 48, color: theme.palette.warning.main }} />,
      title: 'Meeting Notes',
      description: 'Structured meeting notes with key discussion points, decisions, and important moments.',
      color: theme.palette.warning.main,
    },
    {
      icon: <ChecklistRtl sx={{ fontSize: 48, color: theme.palette.error.main }} />,
      title: 'Action Items',
      description: 'Automatically extract and organize action items, assignments, and follow-up tasks.',
      color: theme.palette.error.main,
    },
  ];

  const benefits = [
    {
      icon: <Speed />,
      title: 'Save Time',
      description: 'Reduce meeting documentation time by 90%',
    },
    {
      icon: <Security />,
      title: 'Secure & Private',
      description: 'Enterprise-grade security with data encryption',
    },
    {
      icon: <CloudUpload />,
      title: 'Cloud Storage',
      description: 'Access your meetings from anywhere, anytime',
    },
  ];

  const handleGetStarted = () => {
    navigate('/register');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <Box>
      {/* Hero Section */}
      <HeroSection>
        <Container maxWidth="lg">
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Fade in={true} timeout={1000}>
              <Box sx={{ textAlign: 'center', mb: 6 }}>
                <Typography
                  variant="h2"
                  component="h1"
                  fontWeight={700}
                  sx={{
                    mb: 3,
                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  }}
                >
                  AI-Powered Meeting Assistant
                </Typography>
                <Typography
                  variant="h5"
                  sx={{
                    mb: 4,
                    opacity: 0.9,
                    fontWeight: 400,
                    maxWidth: 600,
                    mx: 'auto',
                    lineHeight: 1.6,
                  }}
                >
                  Transform your meetings with intelligent transcription, speaker identification, 
                  and automated summaries. Never miss important details again.
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleGetStarted}
                    startIcon={<PlayArrow />}
                    sx={{
                      py: 2,
                      px: 4,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: '#ffffff',
                      color: theme.palette.primary.main,
                      '&:hover': {
                        background: alpha('#ffffff', 0.9),
                        transform: 'scale(1.05)',
                      },
                    }}
                  >
                    Get Started Free
                  </Button>
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={handleLogin}
                    sx={{
                      py: 2,
                      px: 4,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      borderColor: '#ffffff',
                      color: '#ffffff',
                      '&:hover': {
                        borderColor: '#ffffff',
                        background: alpha('#ffffff', 0.1),
                      },
                    }}
                  >
                    Sign In
                  </Button>
                </Box>
              </Box>
            </Fade>

            {/* Stats */}
            <Fade in={true} timeout={1500}>
              <Grid container spacing={4} sx={{ mt: 4 }}>
                <Grid item xs={12} md={4}>
                  <StatsBox>
                    <Typography variant="h3" fontWeight={700} color="primary">
                      99%
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Transcription Accuracy
                    </Typography>
                  </StatsBox>
                </Grid>
                <Grid item xs={12} md={4}>
                  <StatsBox>
                    <Typography variant="h3" fontWeight={700} color="primary">
                      10k+
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Meetings Processed
                    </Typography>
                  </StatsBox>
                </Grid>
                <Grid item xs={12} md={4}>
                  <StatsBox>
                    <Typography variant="h3" fontWeight={700} color="primary">
                      90%
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Time Saved
                    </Typography>
                  </StatsBox>
                </Grid>
              </Grid>
            </Fade>
          </Box>
        </Container>
      </HeroSection>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Fade in={true} timeout={2000}>
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h3" component="h2" fontWeight={700} sx={{ mb: 3 }}>
              Powerful Features
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              Everything you need to make your meetings more productive and actionable
            </Typography>
          </Box>
        </Fade>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={6} lg={4} key={index}>
              <Fade in={true} timeout={2000 + index * 200}>
                <FeatureCard>
                  <CardContent sx={{ p: 4, textAlign: 'center' }}>
                    <Box sx={{ mb: 3 }}>
                      {feature.icon}
                    </Box>
                    <Typography variant="h5" fontWeight={600} sx={{ mb: 2 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                      {feature.description}
                    </Typography>
                  </CardContent>
                </FeatureCard>
              </Fade>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Benefits Section */}
      <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.02), py: 10 }}>
        <Container maxWidth="lg">
          <Fade in={true} timeout={3000}>
            <Box sx={{ textAlign: 'center', mb: 8 }}>
              <Typography variant="h3" component="h2" fontWeight={700} sx={{ mb: 3 }}>
                Why Choose Our Platform?
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Built for modern teams who value efficiency and insight
              </Typography>
            </Box>
          </Fade>

          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={6}>
              <Fade in={true} timeout={3500}>
                <Box>
                  {benefits.map((benefit, index) => (
                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
                      <Box
                        sx={{
                          width: 60,
                          height: 60,
                          borderRadius: '50%',
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: 3,
                        }}
                      >
                        {React.cloneElement(benefit.icon, {
                          sx: { fontSize: 28, color: theme.palette.primary.main },
                        })}
                      </Box>
                      <Box>
                        <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
                          {benefit.title}
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                          {benefit.description}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Fade>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Container maxWidth="lg" sx={{ py: 10 }}>
        <Fade in={true} timeout={4500}>
          <Box
            sx={{
              textAlign: 'center',
              p: 8,
              borderRadius: 4,
              background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
              color: '#ffffff',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              <Typography variant="h3" fontWeight={700} sx={{ mb: 3 }}>
                Ready to Transform Your Meetings?
              </Typography>
              <Typography variant="h6" sx={{ mb: 4, opacity: 0.9, maxWidth: 500, mx: 'auto' }}>
                Join thousands of teams already using our AI meeting assistant to boost productivity.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGetStarted}
                  sx={{
                    py: 2,
                    px: 4,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    background: '#ffffff',
                    color: theme.palette.primary.main,
                    '&:hover': {
                      background: alpha('#ffffff', 0.9),
                      transform: 'scale(1.05)',
                    },
                  }}
                >
                  Start Free Trial
                </Button>
                <Chip
                  label="No Credit Card Required"
                  sx={{
                    bgcolor: alpha('#ffffff', 0.2),
                    color: '#ffffff',
                    fontWeight: 600,
                    alignSelf: 'center',
                  }}
                />
              </Box>
            </Box>
            <Box
              sx={{
                position: 'absolute',
                top: -100,
                left: -100,
                width: 300,
                height: 300,
                borderRadius: '50%',
                background: alpha('#ffffff', 0.05),
              }}
            />
            <Box
              sx={{
                position: 'absolute',
                bottom: -150,
                right: -150,
                width: 400,
                height: 400,
                borderRadius: '50%',
                background: alpha('#ffffff', 0.03),
              }}
            />
          </Box>
        </Fade>
      </Container>
    </Box>
  );
};

export default LandingPage; 