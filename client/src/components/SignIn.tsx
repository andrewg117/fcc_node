import { useState, type SubmitEventHandler, type ChangeEventHandler } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLoginMutation } from '../features/auth/authApi';
import { useAppDispatch } from '../app/hooks';
import { setCredentials } from '../features/auth/authSlice';
import { getErrorMessage } from '../app/getErrorMessage';

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

  return (
    <form className='card' onSubmit={handleSubmit}>
      <h1>Sign In</h1>
      <label className='field'>
        Email
        <input className='input' name="email" type="text" autoComplete="email" onChange={handleFormChange} />
      </label>
      <label className='field'>
        Password
        <input className='input' name="password" type="password" autoComplete="current-password" onChange={handleFormChange} />
      </label>
      {error && <p className='form-error' role='alert'>{getErrorMessage(error)}</p>}
      <button className='button' type="submit" disabled={isLoading}>
        {isLoading ? 'Signing in...' : 'Sign In'}
      </button>
      <p className='form-footer'>
        No account yet? <Link to="/register">Register</Link>
      </p>
    </form>
  );
}

export default SignIn;
