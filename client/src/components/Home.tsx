import { useEffect } from 'react';
import { useAppSelector } from '../app/hooks';
import { getErrorMessage } from '../app/getErrorMessage';
import { useDeregisterMutation, useGetMeQuery } from '../features/auth/authApi';
import { useSignOut } from '../features/auth/useSignOut';

function Home() {
  const token = useAppSelector((state) => state.auth.token);
  const storedUser = useAppSelector((state) => state.auth.user);
  const { data: userData, error: meError } = useGetMeQuery(undefined, { skip: !token });
  const [deregister, { isLoading: isDeleting, error: deleteError }] = useDeregisterMutation();
  const signOut = useSignOut();

  useEffect(() => {
    if (meError && 'status' in meError && meError.status === 401) signOut();
  }, [meError, signOut]);

  const handleDelete = async () => {
    if (!window.confirm('Delete your account? This cannot be undone.')) return;
    try {
      await deregister().unwrap();
      signOut();
    } catch {
      // the `deleteError` from useDeregisterMutation() holds the failure
    }
  };

  const user = userData ?? storedUser;

  if (!token || !user) {
    return (
      <section className='card'>
        <h1>Home</h1>
        <p>Not signed in.</p>
      </section>
    );
  }

  return (
    <section className='card'>
      <h1>Home</h1>
      <p>Signed in as {user.name} ({user.email})</p>
      {deleteError && <p className='form-error' role='alert'>{getErrorMessage(deleteError)}</p>}
      <div className='actions'>
        <button className='button button-secondary' onClick={signOut}>Log Out</button>
        <button className='button button-danger' onClick={handleDelete} disabled={isDeleting}>
          {isDeleting ? 'Deleting...' : 'Delete Account'}
        </button>
      </div>
    </section>
  );
}

export default Home;
