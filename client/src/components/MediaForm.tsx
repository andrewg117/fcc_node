import { useState, type ChangeEventHandler, type SubmitEventHandler } from 'react';
import type { SerializedError } from '@reduxjs/toolkit';
import type { FetchBaseQueryError } from '@reduxjs/toolkit/query';
import { getErrorMessage } from '../app/getErrorMessage';

export interface MediaFormValues {
  title: string;
  description: string;
  image?: File;
  song?: File;
}

interface MediaFormProps {
  // Starting title and description. Empty for a new upload.
  initial?: { title: string; description: string };
  // true for a new upload. When editing, an empty file input means "keep the current file".
  filesRequired: boolean;
  submitLabel: string;
  busyLabel: string;
  isBusy: boolean;
  error?: FetchBaseQueryError | SerializedError;
  // Should throw if saving failed, so the form keeps what the user typed.
  onSubmit: (values: MediaFormValues) => Promise<void>;
  onCancel?: () => void;
}

function MediaForm({ initial, filesRequired, submitLabel, busyLabel, isBusy, error, onSubmit, onCancel }: MediaFormProps) {
  const [formData, setFormData] = useState({
    title: initial?.title ?? '',
    description: initial?.description ?? '',
  });
  const [files, setFiles] = useState<{ image?: File; song?: File }>({});

  const handleTextChange: ChangeEventHandler<HTMLInputElement | HTMLTextAreaElement> = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleFileChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    const { name, files: picked } = e.target;
    setFiles((prevFiles) => ({ ...prevFiles, [name]: picked?.[0] }));
  };

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    // Saved before the await: React clears e.currentTarget once the handler yields.
    const form = e.currentTarget;
    try {
      await onSubmit({ ...formData, ...files });
      // Clears the file inputs, which React can't set from state.
      form.reset();
      setFormData({ title: initial?.title ?? '', description: initial?.description ?? '' });
      setFiles({});
    } catch {
      // the parent's `error` prop holds the failure
    }
  };

  return (
    <form className='media-form' onSubmit={handleSubmit}>
      <label className='field'>
        Title
        <input className='input' name="title" type="text" maxLength={100} required value={formData.title} onChange={handleTextChange} />
      </label>
      <label className='field'>
        Description
        <textarea className='input' name="description" rows={3} maxLength={2000} value={formData.description} onChange={handleTextChange} />
      </label>
      <label className='field'>
        {filesRequired ? 'Image' : 'Replace image'}
        <input className='input' name="image" type="file" accept="image/*" required={filesRequired} onChange={handleFileChange} />
      </label>
      <label className='field'>
        {filesRequired ? 'Song' : 'Replace song'}
        <input className='input' name="song" type="file" accept="audio/*" required={filesRequired} onChange={handleFileChange} />
      </label>
      {error && <p className='form-error' role='alert'>{getErrorMessage(error)}</p>}
      <div className='actions'>
        <button className='button' type="submit" disabled={isBusy}>
          {isBusy ? busyLabel : submitLabel}
        </button>
        {onCancel && (
          <button className='button button-secondary' type="button" onClick={onCancel} disabled={isBusy}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

export default MediaForm;
