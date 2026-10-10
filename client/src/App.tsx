import { Routes, Route, NavLink, Navigate } from 'react-router-dom';
import './App.css';
import { useAppSelector } from './app/hooks';
import Home from './components/Home';
import Media from './components/Media';
import Register from './components/Register';
import SignIn from './components/SignIn';

function App() {
  const token = useAppSelector((state) => state.auth.token);
  const signedIn = Boolean(token);
  
  return (
    <>
      <nav className='nav'>
        <NavLink className='nav-link' to="/">Home</NavLink>
        {signedIn ? (
          <NavLink className='nav-link' to="/media">Media</NavLink>
        ) : (
          <>
            <NavLink className='nav-link' to="/sign-in">Sign In</NavLink>
            <NavLink className='nav-link' to="/register">Register</NavLink>
          </>
        )}
      </nav>
      <main className='page'>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/media" element={signedIn ? <Media /> : <Navigate to="/" replace />} />
          <Route path="/sign-in" element={signedIn ? <Navigate to="/" replace /> : <SignIn />} />
          <Route path="/register" element={signedIn ? <Navigate to="/" replace /> : <Register />} />
        </Routes>
      </main>
    </>
  );
}

export default App;
