/**
 * ImageUpload - Cover image upload section for BlogEditor
 */

import React from 'react';
import * as Label from '@radix-ui/react-label';

interface ImageUploadProps {
  coverImageUrl: string;
  uploading: boolean;
  onUpload: (file: File) => void;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ coverImageUrl, uploading, onUpload }) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
  };

  return (
    <div>
      <Label.Root
        htmlFor="coverImage"
        style={{ fontSize: '0.95rem', fontWeight: 600, color: '#0f172a', marginBottom: '8px', display: 'block' }}
      >
        Cover Image
      </Label.Root>
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <input
          id="coverImage"
          type="file"
          accept="image/*"
          onChange={handleChange}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <label
          htmlFor="coverImage"
          style={{
            padding: '12px 24px',
            fontSize: '0.95rem',
            fontWeight: 500,
            color: '#0f172a',
            backgroundColor: '#f0f0f0',
            border: 'none',
            borderRadius: '8px',
            cursor: uploading ? 'not-allowed' : 'pointer',
            opacity: uploading ? 0.5 : 1,
          }}
        >
          {uploading ? 'Uploading...' : 'Upload Image'}
        </label>
        {coverImageUrl && (
          <span style={{ fontSize: '0.9rem', color: '#475569' }}>✓ Image uploaded</span>
        )}
      </div>
      {coverImageUrl && (
        <img
          src={coverImageUrl}
          alt="Cover preview"
          style={{
            marginTop: '12px',
            maxWidth: '200px',
            maxHeight: '150px',
            borderRadius: '8px',
            objectFit: 'cover',
          }}
        />
      )}
    </div>
  );
};

export default ImageUpload;
