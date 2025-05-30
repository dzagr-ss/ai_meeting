import React from 'react';
import { Chip, ChipProps } from '@mui/material';

interface Tag {
  id: number;
  name: string;
  color: string;
  created_at: string;
}

interface TagChipProps extends Omit<ChipProps, 'label'> {
  tag: Tag;
  onDelete?: (tagId: number) => void;
}

const TagChip: React.FC<TagChipProps> = ({ tag, onDelete, ...chipProps }) => {
  const handleDelete = onDelete ? () => onDelete(tag.id) : undefined;

  return (
    <Chip
      label={tag.name}
      size="small"
      variant="outlined"
      onDelete={handleDelete}
      sx={{
        backgroundColor: `${tag.color}15`,
        borderColor: tag.color,
        color: tag.color,
        fontWeight: 500,
        '&:hover': {
          backgroundColor: `${tag.color}25`,
        },
        '& .MuiChip-deleteIcon': {
          color: tag.color,
          '&:hover': {
            color: tag.color,
          },
        },
        ...chipProps.sx,
      }}
      {...chipProps}
    />
  );
};

export default TagChip; 