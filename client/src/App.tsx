import { Routes, Route, NavLink } from 'react-router-dom';
import './App.css';
import Home from './components/Home';
import Register from './components/Register';
import SignIn from './components/SignIn';

function App() {
  return (
    <>
      <nav className='nav'>
        <NavLink className='nav-link' to="/">Home</NavLink>
        <NavLink className='nav-link' to="/sign-in">Sign In</NavLink>
        <NavLink className='nav-link' to="/register">Register</NavLink>
      </nav>
      <main className='page'>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/sign-in" element={<SignIn />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </main>
    </>
  );
}

export default App;
