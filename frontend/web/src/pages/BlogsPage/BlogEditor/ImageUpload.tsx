/**
 * Created at: 2026-07-09 01:31 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:31 EDT
 * Last Modified by: Codex
 *
 * ImageUpload - cover image upload section for BlogEditor.
 */

import React from 'react';
import * as Label from '@radix-ui/react-label';
import { CheckCircledIcon, UploadIcon } from '@radix-ui/react-icons';

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
    <div className="blog-editor-field">
      <Label.Root
        htmlFor="coverImage"
        className="blog-editor-label"
      >
        Cover Image
      </Label.Root>
      <div className="blog-editor-upload-row">
        <input
          id="coverImage"
          type="file"
          accept="image/*"
          onChange={handleChange}
          disabled={uploading}
          className="blog-editor-upload-input"
        />
        <label
          htmlFor="coverImage"
          className={`blog-editor-upload-button${uploading ? ' is-disabled' : ''}`}
        >
          <UploadIcon width={16} height={16} />
          {uploading ? 'Uploading...' : 'Upload Image'}
        </label>
        {coverImageUrl && (
          <span className="blog-editor-upload-status">
            <CheckCircledIcon width={16} height={16} />
            Image uploaded
          </span>
        )}
      </div>
      {coverImageUrl && (
        <div className="blog-editor-cover-preview">
          <img
            src={coverImageUrl}
            alt="Cover preview"
            className="blog-editor-cover-preview__image"
          />
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
