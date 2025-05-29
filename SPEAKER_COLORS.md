# Speaker Color System

## Overview

The Live Transcription feature now includes a sophisticated speaker color system that automatically assigns unique, visually distinct colors to different speakers (Speaker_1, Speaker_2, Speaker_3, etc.). This enhancement makes it much easier to follow conversations and identify who is speaking at any given time.

## Features

### Automatic Color Assignment
- Each speaker is automatically assigned a unique color from a carefully curated palette
- Colors are consistent across the entire session - Speaker_1 will always have the same color
- Up to 10 different speakers are supported with distinct colors
- Unknown or additional speakers fall back to a neutral gray color

### Color Palette
The color palette was specifically chosen to:
- **Fit the site design**: Colors complement the existing Material-UI theme
- **Be professional**: Muted, non-bright colors suitable for business environments
- **Ensure accessibility**: Good contrast ratios for readability
- **Provide distinction**: Each color is visually distinct from others

### Supported Speakers
- **Speaker_1**: Indigo (#4f46e5)
- **Speaker_2**: Emerald (#059669)
- **Speaker_3**: Red (#dc2626)
- **Speaker_4**: Orange/Brown (#7c2d12)
- **Speaker_5**: Violet (#7c3aed)
- **Speaker_6**: Cyan (#0891b2)
- **Speaker_7**: Pink (#be185d)
- **Speaker_8**: Blue (#0369a1)
- **Speaker_9**: Lime (#65a30d)
- **Speaker_10**: Fuchsia (#a21caf)
- **Unknown speakers**: Gray (#6b7280)

## Implementation

### Technical Details
- Colors are applied to speaker chips in both live and stored transcriptions
- Each color includes three variants:
  - **Primary color**: For text and borders
  - **Background color**: Subtle background with 8% opacity
  - **Border color**: Border with 30% opacity
- Hover effects maintain color consistency

### File Structure
```
frontend/src/utils/speakerColors.ts  # Color utility functions
frontend/src/pages/MeetingRoom.tsx   # Main implementation
frontend/src/components/SpeakerColorDemo.tsx  # Demo component
```

## Usage

The speaker color system works automatically - no configuration required. When transcriptions are displayed:

1. **Live Transcription**: Each new speaker segment gets colored chips
2. **Previous Sessions**: Stored transcriptions maintain speaker colors
3. **Consistency**: Colors remain the same throughout the session

## Benefits

- **Improved UX**: Easier to follow multi-speaker conversations
- **Visual Clarity**: Quick identification of speaker changes
- **Professional Appearance**: Maintains the clean, business-appropriate design
- **Accessibility**: Good contrast ratios for all users

## Future Enhancements

Potential future improvements could include:
- Custom speaker names (instead of Speaker_1, Speaker_2, etc.)
- User-customizable color preferences
- Color-blind friendly palette options
- Export functionality that preserves speaker colors 