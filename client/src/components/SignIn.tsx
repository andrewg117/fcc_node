import { useState, useEffect, type SubmitEventHandler, type ChangeEventHandler } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLoginMutation } from '../features/auth/authApi';
import { useAppDispatch } from '../app/hooks';
import { setCredentials } from '../features/auth/authSlice';

function SignIn() {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [login, { isLoading, error }] = useLoginMutation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const handleFormChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    try {
      const data = await login(formData).unwrap();
      dispatch(setCredentials({ user: data.data, token: data.token }));
      navigate('/');
    } catch {
      // error state is already available via the `error` from useLoginMutation()
    }
  };

  useEffect(() => {
    if (error) console.log(error); // TODO: surface a real error message field
  }, [error]);

  return (
    <form onSubmit={handleSubmit}>
      <label>Email: <input name="email" type="text" onChange={handleFormChange} /></label>
      <label>Password: <input name="password" type="password" onChange={handleFormChange} /></label>
      {isLoading && <p>Signing in...</p>}
      <button type="submit" disabled={isLoading}>Sign In</button>
      {error && <p>Invalid email or password</p>}
    </form>
  );
}

export default SignIn;