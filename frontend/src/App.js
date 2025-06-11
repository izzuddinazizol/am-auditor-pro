import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Header from './components/Header';
import Upload from './components/Upload';
import Results from './components/Results';
import Status from './components/Status';
import './index.css';

function App() {
  return (
    <div className="App min-h-screen bg-bg-secondary font-sans text-text-primary">
      <Router>
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/status/:jobId" element={<Status />} />
            <Route path="/results/:jobId" element={<Results />} />
          </Routes>
        </main>
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          className="mt-16"
        />
      </Router>
    </div>
  );
}

export default App; 