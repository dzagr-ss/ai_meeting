import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Autocomplete,
  Typography,
  IconButton,
  Alert,
} from '@mui/material';
import { Add, Close } from '@mui/icons-material';
import TagChip from './TagChip';
import api from '../utils/api';

interface Tag {
  id: number;
  name: string;
  color: string;
  created_at: string;
}

interface TagManagerProps {
  open: boolean;
  onClose: () => void;
  meetingId: number;
  currentTags: Tag[];
  onTagsUpdated: (tags: Tag[]) => void;
}

const TagManager: React.FC<TagManagerProps> = ({
  open,
  onClose,
  meetingId,
  currentTags,
  onTagsUpdated,
}) => {
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [selectedTags, setSelectedTags] = useState<Tag[]>(currentTags);
  const [newTagName, setNewTagName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      loadAvailableTags();
      setSelectedTags(currentTags);
    }
  }, [open, currentTags]);

  const loadAvailableTags = async () => {
    try {
      const response = await api.get('/tags/');
      setAvailableTags(response.data);
    } catch (err) {
      console.error('Failed to load tags:', err);
      setError('Failed to load available tags');
    }
  };

  const handleAddTag = async () => {
    if (!newTagName.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // Create new tag
      const response = await api.post('/tags/', {
        name: newTagName.trim(),
      });

      const newTag = response.data;
      setAvailableTags(prev => [...prev, newTag]);
      setSelectedTags(prev => [...prev, newTag]);
      setNewTagName('');
    } catch (err) {
      console.error('Failed to create tag:', err);
      setError('Failed to create tag');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveTag = (tagId: number) => {
    setSelectedTags(prev => prev.filter(tag => tag.id !== tagId));
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);

    try {
      // Update meeting tags
      await api.put(`/meetings/${meetingId}`, {
        tag_ids: selectedTags.map(tag => tag.id),
      });

      onTagsUpdated(selectedTags);
      onClose();
    } catch (err) {
      console.error('Failed to update meeting tags:', err);
      setError('Failed to update meeting tags');
    } finally {
      setLoading(false);
    }
  };

  const handleTagSelect = (event: any, value: Tag | null) => {
    if (value && !selectedTags.find(tag => tag.id === value.id)) {
      setSelectedTags(prev => [...prev, value]);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Manage Tags
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Current Tags */}
        <Typography variant="subtitle2" gutterBottom>
          Current Tags
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3, minHeight: 40 }}>
          {selectedTags.length > 0 ? (
            selectedTags.map(tag => (
              <TagChip
                key={tag.id}
                tag={tag}
                onDelete={handleRemoveTag}
              />
            ))
          ) : (
            <Typography variant="body2" color="text.secondary">
              No tags selected
            </Typography>
          )}
        </Box>

        {/* Add Existing Tag */}
        <Typography variant="subtitle2" gutterBottom>
          Add Existing Tag
        </Typography>
        <Autocomplete
          options={availableTags.filter(tag => !selectedTags.find(selected => selected.id === tag.id))}
          getOptionLabel={(option) => option.name}
          onChange={handleTagSelect}
          renderInput={(params) => (
            <TextField
              {...params}
              placeholder="Search and select tags..."
              size="small"
              sx={{ mb: 3 }}
            />
          )}
          renderOption={(props, option) => (
            <Box component="li" {...props}>
              <TagChip tag={option} />
            </Box>
          )}
        />

        {/* Create New Tag */}
        <Typography variant="subtitle2" gutterBottom>
          Create New Tag
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            placeholder="Enter new tag name..."
            size="small"
            fullWidth
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAddTag();
              }
            }}
          />
          <Button
            variant="outlined"
            onClick={handleAddTag}
            disabled={!newTagName.trim() || loading}
            startIcon={<Add />}
          >
            Add
          </Button>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TagManager; 