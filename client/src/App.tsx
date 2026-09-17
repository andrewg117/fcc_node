import { Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Home from './components/Home';
import Register from './components/Register';
import SignIn from './components/SignIn';

function App() {
  return (
    <>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/sign-in">Sign In</Link>
        <Link to="/register">Register</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/sign-in" element={<SignIn />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </>
  );
}

export default App;
