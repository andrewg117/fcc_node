import { useState, type SubmitEventHandler, type ChangeEventHandler } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });

  const handleFormChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    const {name, value} = e.target;

    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  } 

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = (e) => {
    e.preventDefault();
    // Send formData
    console.log(formData);
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        <label>
          <input type="text" onChange={handleFormChange} />
          <input type="text" onChange={handleFormChange} />
          <button type="submit">Create User</button>
        </label>
      </form>
    </>
  );
}

export default App;
