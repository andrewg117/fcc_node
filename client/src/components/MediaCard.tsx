import { useState } from 'react';
import { getErrorMessage } from '../app/getErrorMessage';
import {
  useDeleteMediaMutation,
  useUpdateMediaMutation,
  type MediaItem,
} from '../features/media/mediaApi';
import MediaForm, { type MediaFormValues } from './MediaForm';


function MediaCard({ item }: { item: MediaItem }) {

  const [isEditing, setIsEditing] = useState(false);
  const [updateMedia, { isLoading: isSaving, error: updateError, reset: resetUpdate }] = useUpdateMediaMutation();
  const [deleteMedia, { isLoading: isDeleting, error: deleteError }] = useDeleteMediaMutation();

  const handleSave = async (values: MediaFormValues) => {
    // Only send what changed. Left-out fields keep their current value.
    await updateMedia({
      id: item.id,
      title: values.title !== item.title ? values.title : undefined,
      description: values.description !== item.description ? values.description : undefined,
      image: values.image,
      song: values.song,
    }).unwrap();
    setIsEditing(false);
  };

  const handleCancel = () => {
    resetUpdate(); // clears the last save error, so it isn't shown next time
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;
    try {
      await deleteMedia(item.id).unwrap();
    } catch {
      // the `deleteError` from useDeleteMediaMutation() holds the failure
    }
  };

  if (isEditing) {
    return (
      <li className='media-item'>
        <MediaForm
          initial={{ title: item.title, description: item.description }}
          filesRequired={false}
          submitLabel='Save'
          busyLabel='Saving...'
          isBusy={isSaving}
          error={updateError}
          onSubmit={handleSave}
          onCancel={handleCancel}
        />
      </li>
    );
  }

  return (
    <li className='media-item'>
      <img src={item.image_url} alt={item.title} loading="lazy" />
      <h2 className='media-title'>{item.title}</h2>
      {item.description && <p className='media-description'>{item.description}</p>}
      <audio controls preload="metadata" src={item.song_url} />
      {deleteError && <p className='form-error' role='alert'>{getErrorMessage(deleteError)}</p>}
      <div className='actions'>
        <button className='button button-secondary button-small' onClick={() => setIsEditing(true)}>
          Edit
        </button>
        <button className='button button-danger button-small' onClick={handleDelete} disabled={isDeleting}>
          {isDeleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </li>
  );
}

export default MediaCard;
