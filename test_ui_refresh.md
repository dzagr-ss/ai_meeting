# UI Refresh Test Plan

## Test: Speaker Refinement UI Refresh

### Objective
Verify that the UI automatically refreshes to show updated speaker labels after speaker refinement completes, without requiring a manual page reload.

### Prerequisites
1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:3000`
3. User account created and logged in
4. Meeting created with some existing transcriptions

### Test Steps

#### Setup Phase
1. **Create a meeting** with some audio recordings that have speaker labels like "SPEAKER_00", "SPEAKER_01", etc.
2. **Navigate to the meeting room** and observe the current speaker labels in the transcription section
3. **Note the current speaker labels** (e.g., "SPEAKER_00", "SPEAKER_01")

#### Test Phase
1. **Start recording** a new audio segment
2. **Stop recording** and wait for audio upload to complete
3. **Observe the "Refining Speakers" status chip** appears during processing
4. **Wait for speaker refinement to complete** (status chip disappears)
5. **Check the transcription section** for updated speaker labels

### Expected Results

#### Before Fix (Old Behavior)
- Speaker labels remain as "SPEAKER_00", "SPEAKER_01", etc.
- User must manually reload the page to see updated labels like "Speaker_1", "Speaker_2"

#### After Fix (New Behavior)
- Speaker labels automatically update to "Speaker_1", "Speaker_2", etc.
- No manual page reload required
- UI reflects changes immediately after refinement completes

### Verification Points

1. **Automatic Refresh**: Transcriptions refresh without user intervention
2. **Updated Labels**: Speaker names change from "SPEAKER_XX" format to "Speaker_X" format
3. **No Page Reload**: Browser doesn't reload, maintaining current state
4. **Status Indication**: "Refining Speakers" chip shows during processing
5. **Console Logs**: Check browser console for refresh trigger messages

### Console Log Verification

Look for these log messages in the browser console:
```
[AudioRecorder] Speaker refinement successful: {...}
[SpeakerRefinement] Processed X audio files, updated Y transcriptions
[AudioRecorder] Triggering transcriptions refresh after speaker refinement
Refreshing stored transcriptions after speaker refinement...
Refreshed stored transcriptions: [...]
```

### Backend Log Verification

Look for these log messages in the backend console:
```
Comprehensive analysis complete: X refined segments
Found Y existing transcriptions to update
Updated transcription Z: SPEAKER_00 -> Speaker_1
Successfully updated Y transcriptions
```

### Test Success Criteria

✅ **Pass**: UI automatically shows updated speaker labels without page reload
❌ **Fail**: User must manually reload page to see updated speaker labels

### Additional Test Cases

1. **Multiple Refinements**: Test that multiple speaker refinements work correctly
2. **Error Handling**: Test behavior when speaker refinement fails
3. **Concurrent Users**: Test that refinement only affects the current user's view
4. **Network Issues**: Test behavior with slow network connections

### Implementation Details

The fix involves:
1. `AudioRecorderProps` extended with `onTranscriptionsRefresh` callback
2. `MeetingRoom` component provides `handleTranscriptionsRefresh` function
3. `refineSpeakerDiarization` calls the refresh callback on success
4. Stored transcriptions are reloaded from the backend API

This ensures the UI stays in sync with the backend state without requiring manual intervention. 