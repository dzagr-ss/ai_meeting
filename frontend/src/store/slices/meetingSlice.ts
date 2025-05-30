import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Meeting {
  id: number;
  title: string;
  description: string | null;
  start_time: string;
  end_time: string | null;
  status: string;
}

interface MeetingState {
  meetings: Meeting[];
  currentMeeting: Meeting | null;
  loading: boolean;
  error: string | null;
  isRecording: boolean;
  transcription: string;
}

const initialState: MeetingState = {
  meetings: [],
  currentMeeting: null,
  loading: false,
  error: null,
  isRecording: false,
  transcription: '',
};

const meetingSlice = createSlice({
  name: 'meeting',
  initialState,
  reducers: {
    fetchMeetingsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchMeetingsSuccess: (state, action: PayloadAction<Meeting[]>) => {
      state.loading = false;
      state.meetings = action.payload;
    },
    fetchMeetingsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
    setCurrentMeeting: (state, action: PayloadAction<Meeting>) => {
      state.currentMeeting = action.payload;
    },
    startRecording: (state) => {
      state.isRecording = true;
    },
    stopRecording: (state) => {
      state.isRecording = false;
    },
    updateTranscription: (state, action: PayloadAction<string>) => {
      state.transcription = action.payload;
    },
    updateMeetingSuccess: (state, action: PayloadAction<Meeting>) => {
      const index = state.meetings.findIndex(meeting => meeting.id === action.payload.id);
      if (index !== -1) {
        state.meetings[index] = action.payload;
      }
      if (state.currentMeeting && state.currentMeeting.id === action.payload.id) {
        state.currentMeeting = action.payload;
      }
    },
    deleteMeetingSuccess: (state, action: PayloadAction<number>) => {
      state.meetings = state.meetings.filter(meeting => meeting.id !== action.payload);
      if (state.currentMeeting && state.currentMeeting.id === action.payload) {
        state.currentMeeting = null;
      }
    },
  },
});

export const {
  fetchMeetingsStart,
  fetchMeetingsSuccess,
  fetchMeetingsFailure,
  setCurrentMeeting,
  startRecording,
  stopRecording,
  updateTranscription,
  updateMeetingSuccess,
  deleteMeetingSuccess,
} = meetingSlice.actions;

export default meetingSlice.reducer; 