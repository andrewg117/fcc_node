import { useState, useEffect, type SubmitEventHandler, type ChangeEventHandler } from 'react';
import { useCreateUserMutation } from '../features/server/serverApi';

function Register() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    passwordConfirm: ''
  });
  const [createUser, { isLoading, error }] = useCreateUserMutation();

  const handleFormChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    const { name, value } = e.target;

    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  }

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    // Send formData
    await createUser(formData);
  }

  useEffect(() => {
    if (error){
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
          Email:
          <input name="password" type="text" onChange={handleFormChange} />
        </label>
        <label>
          Email:
          <input name="passwordConfirm" type="text" onChange={handleFormChange} />
        </label>
        { isLoading && <p>Creating User...</p>}
        <button type="submit" disabled={isLoading}>Create User</button>
        {error && <p>Enter name and email</p>}
      </form>
    </>
  );
}

export default Register;
