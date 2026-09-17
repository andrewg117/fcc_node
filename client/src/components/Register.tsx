import { useState, useEffect, type SubmitEventHandler, type ChangeEventHandler } from 'react';
import { useNavigate } from 'react-router-dom';

import { useRegisterMutation } from '../features/auth/authApi';

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
      await register(formData).unwrap();
      navigate('/sign-in');
    } catch {
      // error state is already available via `error` from useRegisterMutation()
    }
  };

  useEffect(() => {
    if (error) {
      console.log(error); // TODO: create function to access fields
    }
  }, [error]);


  return (
    <>
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input name="name" type="text" onChange={handleFormChange} />
        </label>
        <label>
          Email:
          <input name="email" type="text" onChange={handleFormChange} />
        </label>
        <label>
          Password:
          <input name="password" type="password" onChange={handleFormChange} />
        </label>
        <label>
          Confirm Password:
          <input name="passwordConfirm" type="password" onChange={handleFormChange} />
        </label>
        {isLoading && <p>Creating User...</p>}
        <button type="submit" disabled={isLoading}>Create User</button>
        {passwordError && <p>{passwordError}</p>}
        {error && <p>Enter name and email</p>}
      </form>
    </>
  );
}

export default Register;
