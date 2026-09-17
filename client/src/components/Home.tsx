import { useAppSelector, useAppDispatch } from '../app/hooks';
import { logout } from '../features/auth/authSlice';

function Home() {
  const user = useAppSelector((state) => state.auth.user);
  const dispatch = useAppDispatch();

  return user ? (
    <>
      <p>Signed in as {user.name} ({user.email})</p>
      <button onClick={() => dispatch(logout())}>Log Out</button>
    </>
  ) : (
    <p>Not signed in.</p>
  );
}

export default Home;
