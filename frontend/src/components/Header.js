import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-bg-primary shadow-sm border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-primary text-sm">AM</span>
            </div>
            <div>
              <h1 className="text-xl font-primary text-text-dark">AM Auditor Pro</h1>
              <p className="text-xs text-text-secondary">AI-Powered Conversation Analysis</p>
            </div>
          </Link>
          
          <nav className="flex items-center space-x-6">
            <Link 
              to="/" 
              className="text-text-secondary hover:text-primary font-accent transition-colors"
            >
              Upload
            </Link>
            <div className="flex items-center space-x-2 text-sm text-text-secondary">
              <div className="w-2 h-2 bg-success rounded-full"></div>
              <span>System Online</span>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header; 