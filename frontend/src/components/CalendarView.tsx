import React, { useMemo } from 'react';
import { Calendar, momentLocalizer, Event } from 'react-big-calendar';
import moment from 'moment';
import { Box, Paper, Typography, Chip, GlobalStyles } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { ArrowBack, ArrowForward } from '@mui/icons-material';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const localizer = momentLocalizer(moment);

interface Tag {
  id: number;
  name: string;
  color: string;
  created_at: string;
}

interface Meeting {
  id: number;
  title: string;
  description: string | null;
  start_time: string;
  end_time: string | null;
  status: string;
  tags: Tag[];
}

interface CalendarEvent extends Event {
  meeting: Meeting;
}

interface CalendarViewProps {
  meetings: Meeting[];
  onSelectMeeting: (meeting: Meeting) => void;
}

const CalendarView: React.FC<CalendarViewProps> = ({ meetings, onSelectMeeting }) => {
  const theme = useTheme();

  const events: CalendarEvent[] = useMemo(() => {
    return meetings.map(meeting => ({
      id: meeting.id,
      title: meeting.title,
      start: new Date(meeting.start_time),
      end: meeting.end_time ? new Date(meeting.end_time) : new Date(meeting.start_time),
      meeting,
    }));
  }, [meetings]);

  const eventStyleGetter = (event: CalendarEvent) => {
    const { meeting } = event;
    let backgroundColor = theme.palette.primary.main;
    
    // Color based on status
    switch (meeting.status.toLowerCase()) {
      case 'active':
        backgroundColor = theme.palette.success.main;
        break;
      case 'scheduled':
        backgroundColor = theme.palette.warning.main;
        break;
      case 'completed':
        backgroundColor = theme.palette.grey[500];
        break;
      default:
        backgroundColor = theme.palette.primary.main;
    }

    return {
      style: {
        backgroundColor,
        borderRadius: '4px',
        opacity: 0.9,
        color: 'white',
        border: '0px',
        display: 'block',
        fontSize: '0.75rem',
        fontWeight: 500,
        padding: '2px 4px',
        margin: '1px 0',
        lineHeight: 1.2,
      },
    };
  };

  // Global styles to override react-big-calendar grid lines
  const calendarGridStyles = (
    <GlobalStyles
      styles={{
        '.rbc-time-view .rbc-time-slot': {
          borderTop: theme.palette.mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.008) !important' 
            : '1px solid rgba(0, 0, 0, 0.015) !important',
        },
        '.rbc-time-view .rbc-timeslot-group': {
          borderBottom: theme.palette.mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.015) !important' 
            : '1px solid rgba(0, 0, 0, 0.025) !important',
        },
        '.rbc-time-view .rbc-day-bg': {
          borderRight: theme.palette.mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.015) !important' 
            : '1px solid rgba(0, 0, 0, 0.025) !important',
        },
        '.rbc-time-content > * + * > *': {
          borderLeft: theme.palette.mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.015) !important' 
            : '1px solid rgba(0, 0, 0, 0.025) !important',
        },
        '.rbc-time-gutter .rbc-time-slot': {
          borderTop: theme.palette.mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.008) !important' 
            : '1px solid rgba(0, 0, 0, 0.015) !important',
        },
        '.rbc-day-slot .rbc-time-slot': {
          borderTop: theme.palette.mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.005) !important' 
            : '1px solid rgba(0, 0, 0, 0.01) !important',
        },
      }}
    />
  );

  // Custom event component for month view - more compact
  const CustomMonthEvent = ({ event }: { event: CalendarEvent }) => (
    <Box sx={{ 
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      fontSize: '0.7rem',
      lineHeight: 1.1,
    }}>
      <Typography 
        variant="caption" 
        sx={{ 
          fontWeight: 600, 
          display: 'block',
          fontSize: 'inherit',
          lineHeight: 'inherit',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {event.title}
      </Typography>
    </Box>
  );

  // Custom event component for week/day view - more detailed
  const CustomDetailedEvent = ({ event }: { event: CalendarEvent }) => (
    <Box sx={{ p: 0.5 }}>
      <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>
        {event.title}
      </Typography>
      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
        <Chip
          label={event.meeting.status}
          size="small"
          sx={{
            height: 16,
            fontSize: '0.6rem',
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            color: 'white',
          }}
        />
        {event.meeting.tags.slice(0, 2).map(tag => (
          <Chip
            key={tag.id}
            label={tag.name}
            size="small"
            sx={{
              height: 16,
              fontSize: '0.6rem',
              backgroundColor: tag.color,
              color: 'white',
            }}
          />
        ))}
      </Box>
    </Box>
  );

  // Custom toolbar with arrow buttons
  const CustomToolbar = ({ label, onNavigate, onView, view }: any) => (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      mb: 2,
      flexWrap: 'wrap',
      gap: 2,
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          component="button"
          onClick={() => onNavigate('PREV')}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            backgroundColor: theme.palette.background.paper,
            color: theme.palette.text.primary,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: theme.shape.borderRadius,
            padding: theme.spacing(0.5, 1),
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: theme.palette.action.hover,
            },
          }}
        >
          <ArrowBack fontSize="small" />
          Back
        </Box>
        <Box
          component="button"
          onClick={() => onNavigate('TODAY')}
          sx={{
            backgroundColor: theme.palette.background.paper,
            color: theme.palette.text.primary,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: theme.shape.borderRadius,
            padding: theme.spacing(0.5, 1),
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: theme.palette.action.hover,
            },
          }}
        >
          Today
        </Box>
        <Box
          component="button"
          onClick={() => onNavigate('NEXT')}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            backgroundColor: theme.palette.background.paper,
            color: theme.palette.text.primary,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: theme.shape.borderRadius,
            padding: theme.spacing(0.5, 1),
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: theme.palette.action.hover,
            },
          }}
        >
          Next
          <ArrowForward fontSize="small" />
        </Box>
      </Box>

      <Typography 
        variant="h6" 
        sx={{ 
          fontWeight: 600,
          color: theme.palette.text.primary,
        }}
      >
        {label}
      </Typography>

      <Box sx={{ display: 'flex', gap: 0.5 }}>
        {['month', 'week', 'day'].map((viewName) => (
          <Box
            key={viewName}
            component="button"
            onClick={() => onView(viewName)}
            sx={{
              backgroundColor: view === viewName 
                ? theme.palette.primary.main 
                : theme.palette.background.paper,
              color: view === viewName 
                ? theme.palette.primary.contrastText 
                : theme.palette.text.primary,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: theme.shape.borderRadius,
              padding: theme.spacing(0.5, 1),
              cursor: 'pointer',
              textTransform: 'capitalize',
              '&:hover': {
                backgroundColor: view === viewName 
                  ? theme.palette.primary.dark 
                  : theme.palette.action.hover,
              },
            }}
          >
            {viewName}
          </Box>
        ))}
      </Box>
    </Box>
  );

  // Custom day prop getter for weekend highlighting
  const dayPropGetter = (date: Date) => {
    const day = date.getDay();
    const isWeekend = day === 0 || day === 6; // Sunday = 0, Saturday = 6
    
    if (isWeekend) {
      return {
        style: {
          backgroundColor: theme.palette.mode === 'light' 
            ? 'rgba(99, 102, 241, 0.08)' 
            : 'rgba(99, 102, 241, 0.15)',
        },
      };
    }
    return {};
  };

  const calendarStyle = {
    height: 600,
    '& .rbc-calendar': {
      fontFamily: theme.typography.fontFamily,
    },
    '& .rbc-header': {
      backgroundColor: theme.palette.background.paper,
      color: theme.palette.text.primary,
      borderBottom: `1px solid ${theme.palette.divider}`,
      padding: theme.spacing(1),
      fontWeight: 600,
    },
    '& .rbc-month-view': {
      backgroundColor: theme.palette.background.paper,
      border: `1px solid ${theme.palette.divider}`,
      borderRadius: theme.shape.borderRadius,
    },
    '& .rbc-week-view, & .rbc-day-view': {
      backgroundColor: theme.palette.background.paper,
      border: `1px solid ${theme.palette.divider}`,
      borderRadius: theme.shape.borderRadius,
      '& .rbc-time-view': {
        backgroundColor: theme.palette.mode === 'dark' 
          ? 'rgba(0, 0, 0, 0.1)' 
          : theme.palette.background.paper,
      },
      '& .rbc-time-slot': {
        borderTop: theme.palette.mode === 'dark' 
          ? `1px solid rgba(255, 255, 255, 0.01) !important` 
          : `1px solid rgba(0, 0, 0, 0.02) !important`,
      },
      '& .rbc-timeslot-group': {
        borderBottom: theme.palette.mode === 'dark' 
          ? `1px solid rgba(255, 255, 255, 0.02) !important` 
          : `1px solid rgba(0, 0, 0, 0.03) !important`,
      },
      '& .rbc-day-slot .rbc-time-slot': {
        borderTop: theme.palette.mode === 'dark' 
          ? `1px solid rgba(255, 255, 255, 0.005) !important` 
          : `1px solid rgba(0, 0, 0, 0.01) !important`,
      },
      '& .rbc-time-gutter .rbc-time-slot': {
        borderTop: theme.palette.mode === 'dark' 
          ? `1px solid rgba(255, 255, 255, 0.01) !important` 
          : `1px solid rgba(0, 0, 0, 0.02) !important`,
      },
    },
    '& .rbc-day-bg': {
      backgroundColor: theme.palette.background.paper,
      borderRight: theme.palette.mode === 'dark' 
        ? `1px solid rgba(255, 255, 255, 0.02) !important` 
        : `1px solid rgba(0, 0, 0, 0.03) !important`,
    },
    '& .rbc-time-content > * + * > *': {
      borderLeft: theme.palette.mode === 'dark' 
        ? `1px solid rgba(255, 255, 255, 0.02) !important` 
        : `1px solid rgba(0, 0, 0, 0.03) !important`,
    },
    '& .rbc-today': {
      backgroundColor: theme.palette.mode === 'light' 
        ? 'rgba(99, 102, 241, 0.05)' 
        : 'rgba(99, 102, 241, 0.1)',
    },
    '& .rbc-off-range-bg': {
      backgroundColor: theme.palette.mode === 'light' 
        ? theme.palette.grey[50] 
        : theme.palette.grey[900],
    },
    '& .rbc-date-cell': {
      color: theme.palette.text.primary,
      padding: theme.spacing(0.5),
    },
    '& .rbc-button-link': {
      color: theme.palette.text.primary,
    },
    '& .rbc-event': {
      fontSize: '0.75rem',
      padding: '1px 3px',
      margin: '1px 0',
    },
    '& .rbc-month-view .rbc-event': {
      fontSize: '0.7rem',
      padding: '1px 2px',
      margin: '0.5px 0',
      lineHeight: 1.1,
    },
    '& .rbc-show-more': {
      fontSize: '0.7rem',
      color: theme.palette.primary.main,
      fontWeight: 500,
    },
    '& .rbc-time-header': {
      borderBottom: `1px solid ${theme.palette.divider}`,
    },
    '& .rbc-time-content': {
      borderTop: 'none',
    },
    '& .rbc-allday-cell': {
      backgroundColor: theme.palette.mode === 'dark' 
        ? 'rgba(0, 0, 0, 0.1)' 
        : theme.palette.grey[50],
    },
  };

  return (
    <Paper sx={{ p: 3, borderRadius: 3 }}>
      {calendarGridStyles}
      <Typography variant="h5" fontWeight={600} gutterBottom sx={{ mb: 3 }}>
        Calendar View
      </Typography>
      <Box sx={calendarStyle}>
        <Calendar
          localizer={localizer}
          events={events}
          startAccessor="start"
          endAccessor="end"
          style={{ height: 600 }}
          eventPropGetter={eventStyleGetter}
          dayPropGetter={dayPropGetter}
          components={{
            event: ({ event, view }: any) => 
              view === 'month' 
                ? <CustomMonthEvent event={event} />
                : <CustomDetailedEvent event={event} />,
            toolbar: CustomToolbar,
          }}
          onSelectEvent={(event) => onSelectMeeting(event.meeting)}
          views={['month', 'week', 'day']}
          defaultView="month"
          popup
          showMultiDayTimes
          step={60}
          timeslots={1}
        />
      </Box>
    </Paper>
  );
};

export default CalendarView; 