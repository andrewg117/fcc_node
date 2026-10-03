import { useState, type SubmitEventHandler, type ChangeEventHandler } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useRegisterMutation } from '../features/auth/authApi';
import { getErrorMessage } from '../app/getErrorMessage';

function Register() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    passwordConfirm: ''
  });
  const [passwordError, setPasswordError] = useState('');
  const [register, { isLoading, error }] = useRegisterMutation();
  const navigate = useNavigate();

  const handleFormChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    const { name, value } = e.target;

    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.passwordConfirm) {
      setPasswordError('Passwords do not match');
      return;
    }
    setPasswordError('');
    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      }).unwrap();
      navigate('/sign-in');
    } catch {
      // error state is already available via `error` from useRegisterMutation()
    }
  };

  return (
    <form className='card' onSubmit={handleSubmit}>
      <h1>Create an Account</h1>
      <label className='field'>
        Name
        <input className='input' name="name" type="text" autoComplete="name" onChange={handleFormChange} />
      </label>
      <label className='field'>
        Email
        <input className='input' name="email" type="text" autoComplete="email" onChange={handleFormChange} />
      </label>
      <label className='field'>
        Password
        <input className='input' name="password" type="password" autoComplete="new-password" onChange={handleFormChange} />
      </label>
      <label className='field'>
        Confirm Password
        <input className='input' name="passwordConfirm" type="password" autoComplete="new-password" onChange={handleFormChange} />
      </label>
      {passwordError && <p className='form-error' role='alert'>{passwordError}</p>}
      {error && <p className='form-error' role='alert'>{getErrorMessage(error)}</p>}
      <button className='button' type="submit" disabled={isLoading}>
        {isLoading ? 'Creating account...' : 'Create Account'}
      </button>
      <p className='form-footer'>
        Already have an account? <Link to="/sign-in">Sign in</Link>
      </p>
    </form>
  );
}

export default Register;
