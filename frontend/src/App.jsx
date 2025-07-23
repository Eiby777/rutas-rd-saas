import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './components/Auth/Login';
import DashboardLayout from './components/Layout/DashboardLayout';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <DashboardLayout />
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
