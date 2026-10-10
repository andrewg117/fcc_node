import { useEffect } from 'react';
import { useAppSelector } from '../app/hooks';
import { getErrorMessage } from '../app/getErrorMessage';
import { useSignOut } from '../features/auth/useSignOut';
import { useCreateMediaMutation, useGetMediaQuery } from '../features/media/mediaApi';
import MediaCard from './MediaCard';
import MediaForm, { type MediaFormValues } from './MediaForm';

function Media() {
  const token = useAppSelector((state) => state.auth.token);
  const { data: items, isLoading, error: listError } = useGetMediaQuery(undefined, { skip: !token });
  const [createMedia, { isLoading: isUploading, error: createError }] = useCreateMediaMutation();
  const signOut = useSignOut();

  useEffect(() => {
    if (listError && 'status' in listError && listError.status === 401) signOut();
  }, [listError, signOut]);

  const handleCreate = async ({ title, description, image, song }: MediaFormValues) => {
    // The form's `required` file inputs mean both are always picked here.
    if (!image || !song) return;
    await createMedia({ title, description, image, song }).unwrap();
  };

  return (
    <section className='card card-wide'>
      <h1>Media</h1>
      <MediaForm
        filesRequired
        submitLabel='Upload'
        busyLabel='Uploading...'
        isBusy={isUploading}
        error={createError}
        onSubmit={handleCreate}
      />

      {listError && <p className='form-error' role='alert'>{getErrorMessage(listError)}</p>}
      {isLoading && <p>Loading...</p>}
      {items?.length === 0 && <p>No uploads yet.</p>}

      <ul className='media-list'>
        {items?.map((item) => <MediaCard key={item.id} item={item} />)}
      </ul>
    </section>
  );
}

export default Media;
